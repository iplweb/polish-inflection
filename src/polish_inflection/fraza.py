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

from .const import (
    BIERNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MĘSKI,
    POJEDYNCZA,
    TEN_SAM_WYRAZ,
)
from .core import _rozwiaz_brak, odmien, podaj
from .przymiotnik import odmien_przymiotnik, podaj_przymiotnik

__all__ = ["odmien_fraze"]

# Markery rozpoczynające zamrożony ogon (patronat, wezwanie).
_MARKERY = {"im.", "imienia", "im", "pw.", "p.w.", "pw"}


def _analizy(token: str, proper: bool = True):
    """Analizy ``podaj`` dla tokenu.

    ``proper=True`` (tryb nazw własnych) — odporne na wielkość liter: próbuje też
    warianty skapitalizowane, żeby złapać proper-nouny z gazeteera (SGJP trzyma je
    wielką literą). ``proper=False`` (fraza pisana w całości małą literą) — TYLKO
    dokładny token: świadomie NIE schodzimy do gazeteera, żeby homograf nazwy
    miejscowej (np. wieś „Wołowo" dla „wołowa") nie ukradł roli rzeczownika.
    """
    proby = (token, token.lower(), token.capitalize()) if proper else (token,)
    for w in proby:
        a = podaj(w)
        if a:
            return a
    return []


def _mianownikowa(token: str, proper: bool = True):
    """Zwróć pierwszą analizę rzeczownika w mianowniku (głowa) albo None."""
    for a in _analizy(token, proper):
        if a.przypadek == MIANOWNIK:
            return a
    return None


def _ma_czytanie_dopelniaczowe(token: str, proper: bool = True) -> bool:
    """Czy token ma rzeczownikowe czytanie w DOPEŁNIACZU?

    Dopełniacz to kanoniczny sygnał dopełnienia zależnego w nazwach instytucji
    („Instytut *czego?* Technologii", „Wydział *czego?* Matematyki"). Świadomie
    NIE zamrażamy na innych przypadkach (zwł. bierniku): homografy przymiotników
    pospolitych/odmiejscowych (polski→acc, Lubelski→voc) mają czytania nom/acc/
    voc i muszą się odmieniać jak przydawki, nie zamrażać. Wielkość liter działa
    naturalnie: „Instytut Polski" (Polska→dop. „Polski") zamraża, a „instytut
    polski" (przymiotnik) odmienia się.
    """
    return any(a.przypadek == DOPEŁNIACZ for a in _analizy(token, proper))


def _jest_przymiotnik(token: str) -> bool:
    """Czy token ma mianownikowe czytanie PRZYMIOTNIKOWE (leksykalnie, przez
    :func:`podaj_przymiotnik`)? Rozstrzyga homograf przymiotnik/rzeczownik przy
    wyborze głowy niezależnie od rodzaju: „Polski" → przymiotnik (demotuj z roli
    głowy), „Instytut" → nie (kandydat na głowę). Zastępuje kruchą heurystykę
    stringową, która myliła się na homografach rodzajowych (Polski↔Polska)."""
    return any(a.przypadek == MIANOWNIK for a in podaj_przymiotnik(token))


def _lemat_przydawki(token: str, rodzaj: str):
    """Lemat, jeśli token to mianownikowa przydawka zgodna z rodzajem głowy; inaczej
    None. Rozpoznanie przez :func:`podaj_przymiotnik` (regułowe, generate-and-test).

    Dopasowanie jest NIEZALEŻNE od docelowej liczby: token wejściowy jest zwykle w
    l.poj. (np. „Lekarski"), a do liczby docelowej odmieniamy dopiero potem —
    dawne porównanie po regeneracji w docelowej liczbie rozjeżdżało się dla l.mn.
    (regen l.mn. „Lekarskie" ≠ token l.poj. „Lekarski")."""
    rp = MĘSKI if rodzaj.startswith(MĘSKI) else rodzaj  # m1/m2/m3 -> publiczny "m"
    for a in podaj_przymiotnik(token):
        if a.przypadek == MIANOWNIK and a.rodzaj == rp:
            return a.lemat
    return None


def _zachowaj_wielkosc(wzor: str, forma: str) -> str:
    if wzor[:1].isupper():
        return forma[:1].upper() + forma[1:]
    return forma


def _wybierz_glowe(tokeny, proper: bool = True):
    """(indeks, analiza) głowy. Preferuj kandydata NIE będącego leksykalnie
    przymiotnikiem (żeby „Polski Instytut" wziął Instytut, nie Polski)."""
    kandydaci = [(i, a) for i, t in enumerate(tokeny) if (a := _mianownikowa(t, proper))]
    if not kandydaci:
        return None, None
    for i, a in kandydaci:
        if not _jest_przymiotnik(tokeny[i]):
            return i, a
    return kandydaci[0]


def _rodzaj_zgody(lemat: str, rodzaj: str) -> str:
    """Doprecyzuj żywotność rodzaju męskiego — biernik l.poj. od niej zależy.

    ``podaj`` zwraca rodzaj zgrubny (``MĘSKI``), a przymiotnik w bierniku męskim
    musi znać żywotność: żywotny → biernik = dopełniacz (``chuja jebanego``),
    nieżywotny → biernik = mianownik (``wydział lubelski``). Żywotność czytamy z
    form głowy (biernik = dopełniacz ⇒ żywotny → ``m2``, inaczej ``m3``). f/n bez
    zmian. (m1 vs m2 — męskoosobowość — nierozstrzygane; istotne tylko dla l.mn.)
    """
    if rodzaj != MĘSKI:
        return rodzaj
    biernik = odmien(lemat, BIERNIK, POJEDYNCZA, default=None)
    if biernik is not None and biernik == odmien(lemat, DOPEŁNIACZ, POJEDYNCZA, default=None):
        return "m2"  # żywotny
    return "m3"  # nieżywotny


def odmien_fraze(fraza: str, przypadek: str, liczba: str = POJEDYNCZA, *, default=TEN_SAM_WYRAZ):
    """Odmień wielowyrazową nazwę własną instytucji do ``przypadek``/``liczba``.

    ``przypadek`` — stała przypadka (``DOPEŁNIACZ`` itd.).

    >>> from polish_inflection import DOPEŁNIACZ
    >>> odmien_fraze("Uniwersytet Lubelski", DOPEŁNIACZ)
    'Uniwersytetu Lubelskiego'
    >>> odmien_fraze("Instytut Technologii Stosowanej", DOPEŁNIACZ)
    'Instytutu Technologii Stosowanej'
    >>> odmien_fraze("Akademia Medyczna", DOPEŁNIACZ)
    'Akademii Medycznej'
    >>> odmien_fraze("dupa wołowa", DOPEŁNIACZ)   # mała litera = zwykłe rzeczowniki
    'dupy wołowej'
    """
    tokeny = fraza.split()
    if not tokeny:
        return fraza

    # Reguła wielkości liter: fraza w CAŁOŚCI małą literą ⇒ to NIE nazwa własna —
    # traktuj jak zwykłe rzeczowniki (bez gazeteera, bez kapitalizacji). Dopiero gdy
    # tak niczego nie rozpoznamy (żadnej głowy), schodzimy do trybu nazw własnych
    # („chyba że ich nie znajdziesz").
    proper = fraza != fraza.lower()
    if not proper:
        wynik = _odmien(tokeny, przypadek, liczba, proper=False)
        if wynik is not None:
            return wynik
        proper = True

    wynik = _odmien(tokeny, przypadek, liczba, proper=True)
    if wynik is None:
        return _rozwiaz_brak(fraza, default)
    return wynik


def _odmien(tokeny, przypadek: str, liczba: str, proper: bool):
    """Właściwa odmiana frazy w danym trybie (``proper``). ``None`` = brak głowy
    lub brak formy głowy (sygnał do fallbacku / obsługi ``default`` przez wrapper)."""
    head_idx, head_a = _wybierz_glowe(tokeny, proper)
    if head_idx is None:
        return None

    rodzaj = _rodzaj_zgody(head_a.lemat, head_a.rodzaj)
    forma_glowy = odmien(head_a.lemat, przypadek, liczba, default=None)
    if forma_glowy is None:
        return None

    wynik = list(tokeny)
    wynik[head_idx] = _zachowaj_wielkosc(tokeny[head_idx], forma_glowy)

    # Przydawki PRZED głową (np. „Wyższa Szkoła", „Katolicki Uniwersytet", „Polski
    # Instytut"). Zawsze przymiotnikowe — dopełnienie dopełniaczowe nie stoi przed
    # głową — więc przymiotnik ma pierwszeństwo NAWET przy homograficznym czytaniu
    # dopełniacza („Polski" = przym. polski / dop. Polska): odmieniamy jako przym.
    for i in range(head_idx):
        lemat = _lemat_przydawki(tokeny[i], rodzaj)
        if lemat:
            f = odmien_przymiotnik(lemat, przypadek, rodzaj, liczba, default=None)
            if f:
                wynik[i] = _zachowaj_wielkosc(tokeny[i], f)

    # Po głowie: odmieniaj przydawki aż do pierwszego dopełnienia/markera/nieznanego.
    for i in range(head_idx + 1, len(tokeny)):
        tok = tokeny[i]
        if tok.lower() in _MARKERY or _ma_czytanie_dopelniaczowe(tok, proper):
            break
        lemat = _lemat_przydawki(tok, rodzaj)
        if not lemat:
            break
        f = odmien_przymiotnik(lemat, przypadek, rodzaj, liczba, default=None)
        if not f:
            break
        wynik[i] = _zachowaj_wielkosc(tok, f)

    return " ".join(wynik)
