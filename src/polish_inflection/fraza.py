"""Odmiana wielowyrazowych nazw własnych instytucji (``odmien_fraze``).

Parser heurystyczny pod nazwy własne uczelni/wydziałów/jednostek: wykrywa głowę
(pierwszy rzeczownik w mianowniku), odmienia głowę + uzgadniające się z nią
przymiotniki (przez :func:`odmien_przymiotnik`), a od pierwszego dopełnienia
zależnego (rzeczownik w przypadku zależnym) lub markera ``im.`` zamraża resztę.

Rozstrzyganie „przydawka vs dopełnienie" (najtrudniejszy punkt) idzie względem
głowy: token z rzeczownikowym czytaniem w przypadku ZALEŻNYM zamraża ogon;
token pasujący morfologicznie do mianownikowej przydawki zgodnej z głową jest
odmieniany. Nieusuwalne dwuznaczności (np. „Instytut Polski") rozstrzyga warstwa
override w django-polish-inflection.
"""

from __future__ import annotations

from .const import MIANOWNIK, POJEDYNCZA, TEN_SAM_WYRAZ, WOŁACZ
from .core import _rozwiaz_brak, odmien, podaj
from .przymiotnik import odmien_przymiotnik

__all__ = ["odmien_fraze"]

# Markery rozpoczynające zamrożony ogon (patronat, wezwanie).
_MARKERY = {"im.", "imienia", "im", "pw.", "p.w.", "pw"}


def _analizy(token: str):
    """Analizy ``podaj`` odporne na wielkość liter (proper nouny są kapitalizowane)."""
    for w in (token, token.lower(), token.capitalize()):
        a = podaj(w)
        if a:
            return a
    return []


def _mianownikowa(token: str):
    """Zwróć pierwszą analizę rzeczownika w mianowniku (głowa) albo None."""
    for a in _analizy(token):
        if a.przypadek == MIANOWNIK:
            return a
    return None


def _ma_czytanie_zalezne(token: str) -> bool:
    """Czy token ma rzeczownikowe czytanie w przypadku ZALEŻNYM (dopełnienie)?

    Zależny = dop./cel./bier./narz./miejsc. Mianownik i WOŁACZ nie liczą się —
    wołacz to homograf nazwisk odmiejscowych (Lubelski, Warszawski), nie sygnał
    dopełnienia dopełniaczowego.
    """
    return any(a.przypadek not in (MIANOWNIK, WOŁACZ) for a in _analizy(token))


def _adj_lemat(token: str, rodzaj: str):
    """Wyprowadź lemat przymiotnika (mian. l.poj. m) z formy mianownikowej w
    rodzaju ``rodzaj``. None, jeśli token nie ma kształtu mian. przydawki."""
    t = token.lower()
    if rodzaj.startswith("m"):
        return t if t.endswith(("y", "i")) else None
    if rodzaj == "f":
        if t.endswith("a"):
            stem = t[:-1]
            return stem + ("i" if stem[-1:] in "kg" else "y")
        return None
    if rodzaj == "n":
        if t.endswith("e"):
            stem = t[:-1]
            return stem if stem.endswith("i") else stem + "y"
    return None


def _lemat_przydawki(token: str, rodzaj: str, liczba: str):
    """Lemat, jeśli token to mianownikowa przydawka zgodna z głową; inaczej None.
    Weryfikacja przez regenerację: regeneruj mianownik z lematu i porównaj."""
    lemat = _adj_lemat(token, rodzaj)
    if lemat is None:
        return None
    regen = odmien_przymiotnik(lemat, MIANOWNIK, rodzaj, liczba, default=None)
    if regen and regen.lower() == token.lower():
        return lemat
    return None


def _zachowaj_wielkosc(wzor: str, forma: str) -> str:
    if wzor[:1].isupper():
        return forma[:1].upper() + forma[1:]
    return forma


def _wybierz_glowe(tokeny):
    """(indeks, analiza) głowy. Preferuj kandydata NIE wyglądającego na przymiotnik
    (żeby „Polski Uniwersytet" wziął Uniwersytet, nie Polski)."""
    kandydaci = [(i, a) for i, t in enumerate(tokeny) if (a := _mianownikowa(t))]
    if not kandydaci:
        return None, None
    for i, a in kandydaci:
        if _adj_lemat(tokeny[i], a.rodzaj) is None:
            return i, a
    return kandydaci[0]


def odmien_fraze(fraza: str, przypadek: str, liczba: str = POJEDYNCZA, *, default=TEN_SAM_WYRAZ):
    """Odmień wielowyrazową nazwę własną instytucji do ``przypadek``/``liczba``.

    >>> odmien_fraze("Uniwersytet Lubelski", "gen")
    'Uniwersytetu Lubelskiego'
    >>> odmien_fraze("Instytut Technologii Stosowanej", "gen")
    'Instytutu Technologii Stosowanej'
    >>> odmien_fraze("Akademia Medyczna", "gen")
    'Akademii Medycznej'
    """
    tokeny = fraza.split()
    if not tokeny:
        return fraza

    head_idx, head_a = _wybierz_glowe(tokeny)
    if head_idx is None:
        return _rozwiaz_brak(fraza, default)

    rodzaj = head_a.rodzaj
    forma_glowy = odmien(head_a.lemat, przypadek, liczba, default=None)
    if forma_glowy is None:
        return _rozwiaz_brak(fraza, default)

    wynik = list(tokeny)
    wynik[head_idx] = _zachowaj_wielkosc(tokeny[head_idx], forma_glowy)

    # Przydawki przed głową (rzadkie, ale np. „Wyższa Szkoła", „Katolicki Uniwersytet").
    for i in range(head_idx):
        if _ma_czytanie_zalezne(tokeny[i]):
            continue  # nie przydawka — zostaw
        lemat = _lemat_przydawki(tokeny[i], rodzaj, liczba)
        if lemat:
            f = odmien_przymiotnik(lemat, przypadek, rodzaj, liczba, default=None)
            if f:
                wynik[i] = _zachowaj_wielkosc(tokeny[i], f)

    # Po głowie: odmieniaj przydawki aż do pierwszego dopełnienia/markera/nieznanego.
    for i in range(head_idx + 1, len(tokeny)):
        tok = tokeny[i]
        if tok.lower() in _MARKERY or _ma_czytanie_zalezne(tok):
            break
        lemat = _lemat_przydawki(tok, rodzaj, liczba)
        if not lemat:
            break
        f = odmien_przymiotnik(lemat, przypadek, rodzaj, liczba, default=None)
        if not f:
            break
        wynik[i] = _zachowaj_wielkosc(tok, f)

    return " ".join(wynik)
