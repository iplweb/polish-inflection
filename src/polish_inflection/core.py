"""Runtime API: odmiana (``odmien``) i analiza zwrotna (``podaj``).

Czyta gotowe indeksy ``odmien.marisa`` / ``podaj.marisa`` (marisa-trie
``BytesTrie``) leniwie i przez ``mmap`` (stała pamięć — import nie ładuje
słownika do RAM). Schemat kluczy/wartości opisuje CONTRACT §D:

    odmien.marisa:  klucz "lemat\\tprzypadek\\tliczba"  -> wartość: forma (utf-8)
    podaj.marisa:   klucz "forma"  -> wartość: "lemat\\tprzypadek\\tliczba\\trodzaj"
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import marisa_trie

from .const import POJEDYNCZA, TEN_SAM_WYRAZ
from .errors import Analiza, BrakOdmiany

__all__ = [
    "odmien",
    "odmien_lub_none",
    "odmien_lub_wyraz",
    "odmien_warianty",
    "podaj",
]

# Wewnętrzny wartownik: "default nie podany -> rzuć BrakOdmiany".
_BRAK = object()

# Leniwie ładowane, mmapowane indeksy. Cache modułowy.
_odmien_dawg = None
_podaj_dawg = None

# Katalog z danymi — domyślnie pakietowy ``polish_inflection/data``.
# Testy podmieniają go przez ``_ustaw_katalog_danych``.
_katalog_danych: Path | None = None


def _domyslny_katalog_danych() -> Path:
    return Path(str(files("polish_inflection") / "data"))


def _ustaw_katalog_danych(sciezka) -> None:
    """Wskaż inny katalog z ``odmien.dawg``/``podaj.dawg`` i wyczyść cache.

    Używane w testach (fixture DAWG budowany do tmp) oraz w integracji.
    ``None`` przywraca katalog pakietowy.
    """
    global _katalog_danych, _odmien_dawg, _podaj_dawg
    _katalog_danych = Path(sciezka) if sciezka is not None else None
    _odmien_dawg = None
    _podaj_dawg = None


def _wczytaj(nazwa: str):
    katalog = _katalog_danych or _domyslny_katalog_danych()
    sciezka = katalog / nazwa
    if not sciezka.exists():
        raise RuntimeError(
            f"Brak zbudowanego indeksu {sciezka}. "
            "Uruchom build: `polish-inflection-build build` (patrz docs/budowanie.md)."
        )
    trie = marisa_trie.BytesTrie()
    trie.mmap(str(sciezka))  # memory-mapped — stała pamięć, bez wczytywania do RAM
    return trie


def _dawg_odmien():
    global _odmien_dawg
    if _odmien_dawg is None:
        _odmien_dawg = _wczytaj("odmien.marisa")
    return _odmien_dawg


def _dawg_podaj():
    global _podaj_dawg
    if _podaj_dawg is None:
        _podaj_dawg = _wczytaj("podaj.marisa")
    return _podaj_dawg


def _formy(wyraz: str, przypadek: str, liczba: str) -> list[str]:
    """Posortowana lista poprawnych form w slocie (może być pusta)."""
    klucz = f"{wyraz}\t{przypadek}\t{liczba}"
    wartosci = _dawg_odmien().get(klucz)
    if not wartosci:
        return []
    return sorted(v.decode("utf-8") for v in wartosci)


def odmien(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA, *, default=_BRAK):
    """Zwróć główną formę ``wyraz`` w danym przypadku i liczbie.

    Zachowanie przy braku formy (słowo spoza słownika lub liczba nieistniejąca
    dla lematu, np. ``sg`` dla plurale tantum):

    - ``default`` niepodany         -> ``raise BrakOdmiany``
    - ``default is TEN_SAM_WYRAZ``  -> zwróć ``wyraz`` (passthrough)
    - ``default is None``           -> zwróć ``None``
    - ``default = <cokolwiek>``     -> zwróć ``default``

    Główna forma = pierwsza po sortowaniu bajtowym wartości slotu (deterministyczna).

    >>> odmien("wydział", "gen")
    'wydziału'
    >>> odmien("wydział", "gen", "pl")
    'wydziałów'
    """
    formy = _formy(wyraz, przypadek, liczba)
    if formy:
        return formy[0]
    if default is _BRAK:
        raise BrakOdmiany((wyraz, przypadek, liczba))
    if default is TEN_SAM_WYRAZ:
        return wyraz
    return default


def odmien_lub_none(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA):
    """Jak ``odmien``, ale przy braku formy zwraca ``None`` (nie rzuca)."""
    return odmien(wyraz, przypadek, liczba, default=None)


def odmien_lub_wyraz(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA) -> str:
    """Jak ``odmien``, ale przy braku formy zwraca wejściowy ``wyraz`` (passthrough)."""
    return odmien(wyraz, przypadek, liczba, default=TEN_SAM_WYRAZ)


def odmien_warianty(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA) -> list[str]:
    """Wszystkie poprawne formy w slocie (oboczności), posortowane. ``[]`` gdy brak."""
    return _formy(wyraz, przypadek, liczba)


def podaj(wyraz: str, liczba: str | None = None) -> list[Analiza]:
    """Kierunek zwrotny: forma -> lista analiz.

    Zwraca LISTĘ, bo polszczyzna ma synkretyzm (jedna forma = wiele przypadków)
    i homografię (jedna forma = wiele lematów). Uwzględnia też formy
    deprecjatywne (``depr``). Opcjonalny ``liczba`` ("sg"/"pl") zawęża wynik.
    Nieznana forma -> ``[]``.

    >>> podaj("jednostki")  # doctest: +SKIP
    [Analiza('jednostka','gen','sg','f'), Analiza('jednostka','nom','pl','f'), ...]
    """
    wartosci = _dawg_podaj().get(wyraz)
    if not wartosci:
        return []
    analizy: set[Analiza] = set()
    for w in wartosci:
        pola = w.decode("utf-8").split("\t")
        if len(pola) != 4:
            continue
        lemat, przypadek, lb, rodzaj = pola
        if liczba is not None and lb != liczba:
            continue
        analizy.add(Analiza(lemat, przypadek, lb, rodzaj))
    return sorted(analizy, key=lambda a: (a.liczba, a.przypadek, a.lemat, a.rodzaj))
