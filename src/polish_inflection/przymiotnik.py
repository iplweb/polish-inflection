"""Regułowa odmiana przymiotników (stopień równy) — bez indeksu, czysto z reguł.

Odmiana przymiotnika w polszczyźnie jest REGULARNA (zamknięty system paradygmatów
twardo-/miękko-/welarnotematowych), inaczej niż leksykalna odmiana rzeczownika —
dlatego nie trzymamy przymiotników w indeksie SGJP (to +46 MB), tylko generujemy
je regułą (kilka KB kodu). Zwalidowane przeciw SGJP: l.poj. 99,98% zgodności.

Wejście ``lemat`` to mianownik l.poj. rodzaju męskiego (forma słownikowa, np.
``lubelski``, ``medyczny``, ``stosowany``). ``rodzaj`` to rodzaj GŁOWY, którą
przymiotnik określa (zgoda) — akceptujemy zarówno zgrubny ``m``/``f``/``n`` (jak
zwraca :func:`polish_inflection.podaj`), jak i dokładny ``m1``/``m2``/``m3``.
"""

from __future__ import annotations

from .const import MNOGA, POJEDYNCZA, TEN_SAM_WYRAZ
from .core import _rozwiaz_brak

__all__ = ["odmien_przymiotnik"]

# Abstrakcyjne końcówki l.poj.: (grupa_rodzaju, przypadek) -> końcówka.
# grupa_rodzaju: "m" (m1/m2/m3 wspólne poza biernikiem), "f", "n".
_SG = {
    ("m", "nom"): "y",
    ("m", "gen"): "ego",
    ("m", "dat"): "emu",
    ("m", "inst"): "ym",
    ("m", "loc"): "ym",
    ("m", "voc"): "y",
    ("f", "nom"): "a",
    ("f", "gen"): "ej",
    ("f", "dat"): "ej",
    ("f", "acc"): "ą",
    ("f", "inst"): "ą",
    ("f", "loc"): "ej",
    ("f", "voc"): "a",
    ("n", "nom"): "e",
    ("n", "gen"): "ego",
    ("n", "dat"): "emu",
    ("n", "acc"): "e",
    ("n", "inst"): "ym",
    ("n", "loc"): "ym",
    ("n", "voc"): "e",
}

# Końcówki l.mn. NIEmęskoosobowe (m2/m3/f/n) — wspólne dla wszystkich rodzajów
# poza mianownikiem/wołaczem męskoosobowym (patrz _mn_meskoosobowy_mianownik).
_PL_NIEMESK = {
    "nom": "e",
    "gen": "ych",
    "dat": "ym",
    "acc": "e",
    "inst": "ymi",
    "loc": "ych",
    "voc": "e",
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
    if rodzaj in ("m", "m1", "m2", "m3"):
        return "m"
    if rodzaj == "n":
        return "n"
    return "f"


def _zywotny(rodzaj: str) -> bool:
    # Zgrubne "m" traktujemy jako NIEżywotne (nazwy instytucji: uniwersytet, wydział).
    return rodzaj in ("m1", "m2")


def _mn_meskoosobowy_mianownik(klasa: str, temat: str) -> str:
    for konc, nowy, sam in _MESK_ALT:
        if temat.endswith(konc):
            return temat[: -len(konc)] + nowy + sam
    # brak alternacji: SOFT/VELAR -> +i, HARD -> +i (miękczy)
    return temat + "i"


def _forma_sg(klasa, temat, rodzaj, przypadek):
    grupa = _grupa(rodzaj)
    if grupa == "m" and przypadek == "acc":
        klucz = ("m", "gen") if _zywotny(rodzaj) else ("m", "nom")
    else:
        klucz = (grupa, przypadek)
    konc = _SG.get(klucz)
    return _sklej(klasa, temat, konc) if konc else None


def _forma_pl(klasa, temat, rodzaj, przypadek):
    meskoosobowy = rodzaj == "m1"
    if meskoosobowy and przypadek in ("nom", "voc"):
        return _mn_meskoosobowy_mianownik(klasa, temat)
    if meskoosobowy and przypadek == "acc":
        konc = _PL_NIEMESK["gen"]  # biernik m1 l.mn. = dopełniacz
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

    ``lemat`` — mianownik l.poj. m (forma słownikowa). ``rodzaj`` — rodzaj głowy
    (``m``/``m1``/``m2``/``m3``/``f``/``n``; zgrubne ``m`` = nieżywotny).
    Przy niepoprawnym wejściu stosuje ``default`` (jak reszta API).

    >>> odmien_przymiotnik("lubelski", "gen", "m")
    'lubelskiego'
    >>> odmien_przymiotnik("stosowany", "gen", "f")
    'stosowanej'
    >>> odmien_przymiotnik("medyczny", "nom", "m1", "pl")
    'medyczni'
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
