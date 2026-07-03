"""Regułowa odmiana przymiotników (stopień równy) — bez indeksu, czysto z reguł.

Odmiana przymiotnika w polszczyźnie jest REGULARNA (zamknięty system paradygmatów
twardo-/miękko-/welarnotematowych), inaczej niż leksykalna odmiana rzeczownika —
dlatego nie trzymamy przymiotników w indeksie SGJP (to +46 MB), tylko generujemy
je regułą (kilka KB kodu). Zwalidowane przeciw SGJP: l.poj. 99,9% zgodności.

Wejście ``lemat`` to mianownik l.poj. rodzaju męskiego (forma słownikowa, np.
``lubelski``, ``medyczny``, ``stosowany``). ``rodzaj`` to rodzaj GŁOWY, którą
przymiotnik określa (zgoda) — przyjmujemy publiczne stałe ``MĘSKI``/``ŻEŃSKI``/
``NIJAKI``; zgrubny ``MĘSKI`` traktujemy jako nieżywotny (nazwy instytucji).
"""

from __future__ import annotations

from .const import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    MĘSKI,
    NARZĘDNIK,
    NIJAKI,
    POJEDYNCZA,
    TEN_SAM_WYRAZ,
    WOŁACZ,
    ŻEŃSKI,
)
from .core import _rozwiaz_brak

__all__ = ["odmien_przymiotnik"]

# Podtypy rodzaju męskiego (m1 męskoosobowy, m2 męskozwierzęcy) są w SGJP, ale
# NIE mają publicznych stałych (biblioteka wystawia tylko MĘSKI/ŻEŃSKI/NIJAKI).
# Przyjmujemy je jako opcjonalne wejście dla zaawansowanych wywołań.
_M1 = "m1"
_M2 = "m2"

# Abstrakcyjne końcówki l.poj.: (grupa_rodzaju, przypadek) -> końcówka.
# grupa_rodzaju: MĘSKI (m1/m2/m3 wspólne poza biernikiem), ŻEŃSKI, NIJAKI.
_SG = {
    (MĘSKI, MIANOWNIK): "y",
    (MĘSKI, DOPEŁNIACZ): "ego",
    (MĘSKI, CELOWNIK): "emu",
    (MĘSKI, NARZĘDNIK): "ym",
    (MĘSKI, MIEJSCOWNIK): "ym",
    (MĘSKI, WOŁACZ): "y",
    (ŻEŃSKI, MIANOWNIK): "a",
    (ŻEŃSKI, DOPEŁNIACZ): "ej",
    (ŻEŃSKI, CELOWNIK): "ej",
    (ŻEŃSKI, BIERNIK): "ą",
    (ŻEŃSKI, NARZĘDNIK): "ą",
    (ŻEŃSKI, MIEJSCOWNIK): "ej",
    (ŻEŃSKI, WOŁACZ): "a",
    (NIJAKI, MIANOWNIK): "e",
    (NIJAKI, DOPEŁNIACZ): "ego",
    (NIJAKI, CELOWNIK): "emu",
    (NIJAKI, BIERNIK): "e",
    (NIJAKI, NARZĘDNIK): "ym",
    (NIJAKI, MIEJSCOWNIK): "ym",
    (NIJAKI, WOŁACZ): "e",
}

# Końcówki l.mn. NIEmęskoosobowe (m2/m3/f/n) — wspólne dla wszystkich rodzajów
# poza mianownikiem/wołaczem męskoosobowym (patrz _mn_meskoosobowy_mianownik).
_PL_NIEMESK = {
    MIANOWNIK: "e",
    DOPEŁNIACZ: "ych",
    CELOWNIK: "ym",
    BIERNIK: "e",
    NARZĘDNIK: "ymi",
    MIEJSCOWNIK: "ych",
    WOŁACZ: "e",
}

# Tablica alternacji tematu dla mianownika l.mn. MĘSKOOSOBOWEGO (m1):
# temat -> (nowa_koncowka_tematu, samogloska). Dłuższe wzorce najpierw.
_MESK_ALT = [
    ("sk", "sc", "y"),
    ("st", "śc", "i"),
    ("zk", "zc", "y"),
    ("ch", "s", "i"),
    ("sz", "s", "i"),
    ("cz", "cz", "y"),
    ("k", "c", "y"),
    ("g", "dz", "y"),
    ("r", "rz", "y"),
    ("ł", "l", "i"),
    ("t", "c", "i"),
    ("d", "dz", "i"),
    ("sł", "śl", "i"),
    ("zł", "źl", "i"),
    ("ż", "z", "i"),
    ("n", "n", "i"),
    ("ni", "ni", ""),
]


def _klasa_temat(lemat: str):
    """(klasa, temat). Klasa steruje samogłoską łączącą i/y w formach zależnych."""
    if lemat.endswith("y"):
        return "HARD", lemat[:-1]
    if lemat.endswith("i"):
        temat = lemat[:-1]
        if temat and temat[-1] in "kg":
            return "VELAR", temat
        if temat and temat[-1] == "l":
            return "LTWARDA", temat  # -li: 'l' funkcjonalnie twarde (anieli->aniela)
        return "SOFT", temat
    return None, lemat


def _sklej(klasa: str, temat: str, koncowka: str) -> str:
    if klasa == "HARD":
        return temat + koncowka
    if klasa == "LTWARDA":
        return temat + ("i" + koncowka[1:] if koncowka[0] == "y" else koncowka)
    if klasa == "VELAR":
        if koncowka[0] == "y":
            return temat + "i" + koncowka[1:]
        if koncowka[0] == "e":
            return temat + "i" + koncowka
        return temat + koncowka  # a, ą — samogłoski tylne bez zmiękczenia
    # SOFT: "i" przed każdą końcówką; y->i
    return temat + ("i" + koncowka[1:] if koncowka[0] == "y" else "i" + koncowka)


def _grupa(rodzaj: str) -> str:
    if rodzaj in (MĘSKI, _M1, _M2, "m3"):
        return MĘSKI
    if rodzaj == NIJAKI:
        return NIJAKI
    return ŻEŃSKI


def _zywotny(rodzaj: str) -> bool:
    # Zgrubne MĘSKI traktujemy jako NIEżywotne (nazwy instytucji: uniwersytet, wydział).
    return rodzaj in (_M1, _M2)


def _mn_meskoosobowy_mianownik(temat: str) -> str:
    for konc, nowy, sam in _MESK_ALT:
        if temat.endswith(konc):
            return temat[: -len(konc)] + nowy + sam
    return temat + "i"  # brak alternacji -> miękczenie samą samogłoską


def _forma_sg(klasa, temat, rodzaj, przypadek):
    grupa = _grupa(rodzaj)
    if grupa == MĘSKI and przypadek == BIERNIK:
        klucz = (MĘSKI, DOPEŁNIACZ) if _zywotny(rodzaj) else (MĘSKI, MIANOWNIK)
    else:
        klucz = (grupa, przypadek)
    konc = _SG.get(klucz)
    return _sklej(klasa, temat, konc) if konc else None


def _forma_pl(klasa, temat, rodzaj, przypadek):
    meskoosobowy = rodzaj == _M1
    if meskoosobowy and przypadek in (MIANOWNIK, WOŁACZ):
        return _mn_meskoosobowy_mianownik(temat)
    if meskoosobowy and przypadek == BIERNIK:
        konc = _PL_NIEMESK[DOPEŁNIACZ]  # biernik m1 l.mn. = dopełniacz
    else:
        konc = _PL_NIEMESK.get(przypadek)
    return _sklej(klasa, temat, konc) if konc else None


def odmien_przymiotnik(
    lemat: str,
    przypadek: str,
    rodzaj: str,
    liczba: str = POJEDYNCZA,
    *,
    default=TEN_SAM_WYRAZ,
):
    """Odmień przymiotnik ``lemat`` do (``przypadek``, ``rodzaj``, ``liczba``).

    ``lemat`` — mianownik l.poj. m (forma słownikowa). ``przypadek`` — stała
    przypadka (``DOPEŁNIACZ`` itd.). ``rodzaj`` — rodzaj głowy (``MĘSKI``/
    ``ŻEŃSKI``/``NIJAKI``; zgrubny ``MĘSKI`` = nieżywotny). Przy niepoprawnym
    wejściu stosuje ``default`` (jak reszta API).

    >>> from polish_inflection import DOPEŁNIACZ, MIEJSCOWNIK, MĘSKI, ŻEŃSKI, NIJAKI
    >>> odmien_przymiotnik("lubelski", DOPEŁNIACZ, MĘSKI)
    'lubelskiego'
    >>> odmien_przymiotnik("stosowany", DOPEŁNIACZ, ŻEŃSKI)
    'stosowanej'
    >>> odmien_przymiotnik("medyczny", MIEJSCOWNIK, NIJAKI)
    'medycznym'
    """
    klasa, temat = _klasa_temat(lemat)
    if klasa is None:
        return _rozwiaz_brak(lemat, default)
    if liczba == MNOGA:
        forma = _forma_pl(klasa, temat, rodzaj, przypadek)
    else:
        forma = _forma_sg(klasa, temat, rodzaj, przypadek)
    if forma is None:
        return _rozwiaz_brak(lemat, default)
    return forma
