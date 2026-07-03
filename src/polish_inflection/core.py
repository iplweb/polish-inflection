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

from .const import POJEDYNCZA, RAISES, TEN_SAM_WYRAZ
from .errors import Analiza, BrakOdmiany

__all__ = [
    "odmien",
    "odmien_lub_none",
    "odmien_lub_wyraz",
    "odmien_warianty",
    "podaj",
]


def _rozwiaz_brak(wyraz, default):
    """Rozwiąż brak formy wg parametru ``default`` (wspólne dla warstwy pytań).

    ``RAISES`` → rzuć ``BrakOdmiany``; ``TEN_SAM_WYRAZ`` → zwróć ``wyraz``;
    inaczej zwróć ``default`` (``None`` lub dowolną wartość).
    """
    if default is RAISES:
        raise BrakOdmiany(wyraz)
    if default is TEN_SAM_WYRAZ:
        return wyraz
    return default


# Leniwie ładowane, mmapowane indeksy. Cache modułowy.
_odmien_trie = None
_podaj_trie = None

# Katalog z danymi — domyślnie pakietowy ``polish_inflection/data``.
# Testy podmieniają go przez ``_ustaw_katalog_danych``.
_katalog_danych: Path | None = None


def _domyslny_katalog_danych() -> Path:
    return Path(str(files("polish_inflection") / "data"))


def _ustaw_katalog_danych(sciezka) -> None:
    """Wskaż inny katalog z ``odmien.marisa``/``podaj.marisa`` i wyczyść cache.

    Używane w testach (fixture marisa-trie budowany do tmp) oraz w integracji.
    ``None`` przywraca katalog pakietowy.
    """
    global _katalog_danych, _odmien_trie, _podaj_trie
    _katalog_danych = Path(sciezka) if sciezka is not None else None
    _odmien_trie = None
    _podaj_trie = None


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


def _trie_odmien():
    global _odmien_trie
    if _odmien_trie is None:
        _odmien_trie = _wczytaj("odmien.marisa")
    return _odmien_trie


def _trie_podaj():
    global _podaj_trie
    if _podaj_trie is None:
        _podaj_trie = _wczytaj("podaj.marisa")
    return _podaj_trie


def _formy(wyraz: str, przypadek: str, liczba: str) -> list[str]:
    """Posortowana lista poprawnych form w slocie (może być pusta)."""
    klucz = f"{wyraz}\t{przypadek}\t{liczba}"
    wartosci = _trie_odmien().get(klucz)
    if not wartosci:
        return []
    return sorted(v.decode("utf-8") for v in wartosci)


def _forma_o_rodzaju(formy, wyraz, przypadek, liczba, rodzaj):
    """Forma ze slotu, której analiza (``podaj``) ma dany ``rodzaj``. ``None`` gdy brak."""
    for forma in formy:
        if any(
            a.lemat == wyraz
            and a.przypadek == przypadek
            and a.liczba == liczba
            and a.rodzaj == rodzaj
            for a in podaj(forma)
        ):
            return forma
    return None


def odmien(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA, *, rodzaj=None, default=RAISES):
    """Zwróć główną formę ``wyraz`` w danym przypadku i liczbie.

    ``rodzaj`` (opcjonalnie) wymusza rodzaj gramatyczny dla homografów rodzajowych
    (stałe ``MĘSKI`` / ``ŻEŃSKI`` / ``NIJAKI``). Gdy podany, zwracamy formę o tym
    rodzaju; jeśli słownik nie ma formy tego rodzaju w tym slocie — traktujemy to
    jak brak formy (zob. ``default``).

    Bez ``rodzaj`` główna forma: przy homografii/oboczności preferujemy formę
    **odmienioną** (różną od lematu ``wyraz``) nad tożsamościową — dla homografu
    rodzajów (np. ``profesor`` = męski odmienny + żeński nieodmienny) dostajemy
    ``profesora``/``profesorów``, a nie nieodmienne ``profesor``. Wśród kandydatów
    wybór jest deterministyczny (sortowanie bajtowe).

    Zachowanie przy braku formy (słowo spoza słownika, nieistniejąca liczba, lub
    brak formy żądanego ``rodzaj``):

    - ``default`` niepodany         -> ``raise BrakOdmiany``
    - ``default is TEN_SAM_WYRAZ``  -> zwróć ``wyraz`` (passthrough)
    - ``default is None``           -> zwróć ``None``
    - ``default = <cokolwiek>``     -> zwróć ``default``

    >>> odmien("wydział", DOPEŁNIACZ)
    'wydziału'
    >>> odmien("profesor", DOPEŁNIACZ)                     # bez rodzaju: forma odmieniona
    'profesora'
    >>> odmien("profesor", DOPEŁNIACZ, rodzaj=ŻEŃSKI)      # wymuszony żeński (nieodmienny)
    'profesor'
    >>> odmien("profesor", DOPEŁNIACZ, MNOGA, rodzaj=MĘSKI)
    'profesorów'
    """
    formy = _formy(wyraz, przypadek, liczba)
    if formy:
        if rodzaj is None:
            odmienione = [f for f in formy if f != wyraz]
            return (odmienione or formy)[0]
        wybor = _forma_o_rodzaju(formy, wyraz, przypadek, liczba, rodzaj)
        if wybor is not None:
            return wybor
        # brak formy żądanego rodzaju -> jak brak formy (obsługa default poniżej)
    if default is RAISES:
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


def _rodzaj_publiczny(rodzaj_surowy: str) -> str:
    """Zwęź rodzaj SGJP do publicznego: m1/m2/m3 -> "m" (MĘSKI), f -> "f", n -> "n".

    Podtypy rodzaju męskiego (męskoosobowy m1, męskozwierzęcy m2, męskorzeczowy m3)
    są szczegółem implementacyjnym — publicznie widać tylko męski/żeński/nijaki.
    """
    return rodzaj_surowy[:1] if rodzaj_surowy else rodzaj_surowy


def _rekordy_podaj(wyraz: str, liczba: str | None = None):
    """Surowe rekordy analizy ``(lemat, przypadek, liczba, rodzaj_SUROWY)`` — rodzaj
    z podtypem SGJP (m1/m2/m3/f/n). Do użytku WEWNĘTRZNEGO (np. wykrywanie
    męskoosobowego w liczebnikach); publiczne API zwęża rodzaj (patrz ``podaj``)."""
    wartosci = _trie_podaj().get(wyraz)
    if not wartosci:
        return []
    rekordy = []
    for w in wartosci:
        pola = w.decode("utf-8").split("\t")
        if len(pola) != 4:
            continue
        lemat, przypadek, lb, rodzaj = pola
        if liczba is not None and lb != liczba:
            continue
        rekordy.append((lemat, przypadek, lb, rodzaj))
    return rekordy


def podaj(wyraz: str, liczba: str | None = None) -> list[Analiza]:
    """Kierunek zwrotny: forma -> lista analiz.

    Zwraca LISTĘ, bo polszczyzna ma synkretyzm (jedna forma = wiele przypadków)
    i homografię (jedna forma = wiele lematów). Uwzględnia też formy
    deprecjatywne (``depr``). Opcjonalny ``liczba`` ("sg"/"pl") zawęża wynik.
    Nieznana forma -> ``[]``.

    ``Analiza.rodzaj`` to rodzaj publiczny: ``MĘSKI`` (``"m"``) / ``ŻEŃSKI``
    (``"f"``) / ``NIJAKI`` (``"n"``).

    >>> podaj("jednostki")  # doctest: +SKIP
    [Analiza('jednostka','gen','sg','f'), Analiza('jednostka','nom','pl','f'), ...]
    """
    analizy = {
        Analiza(lemat, przypadek, lb, _rodzaj_publiczny(rodzaj))
        for lemat, przypadek, lb, rodzaj in _rekordy_podaj(wyraz, liczba)
    }
    return sorted(analizy, key=lambda a: (a.liczba, a.przypadek, a.lemat, a.rodzaj))
