"""Warstwa ergonomiczna: funkcje nazwane pytaniami przypadków + forma podstawowa.

Cienka kompozycja nad ``podaj`` + ``odmien`` (zero nowych danych). Funkcje
pytaniowe ZAKŁADAJĄ, że wejściowy wyraz jest w mianowniku, zgadują jego liczbę
i zwracają żądany przypadek w tej liczbie. ``podstawowa_forma`` robi odwrotność:
dowolna forma → lemat (forma słownikowa).

Zachowanie przy braku (parametr ``default``):
    TEN_SAM_WYRAZ (domyślnie) → zwróć wejściowy wyraz (passthrough)
    None                      → zwróć None
    RAISES                    → rzuć BrakOdmiany
    <cokolwiek>               → zwróć tę wartość
"""

from __future__ import annotations

from .const import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    NARZĘDNIK,
    POJEDYNCZA,
    TEN_SAM_WYRAZ,
)
from .core import _rozwiaz_brak, odmien, podaj

__all__ = [
    # kanoniczne
    "kogo_czego",
    "komu_czemu",
    "kogo_co",
    "z_kim_z_czym",
    "o_kim_o_czym",
    "podstawowa_forma",
    "odmiana_liczebnikowa",
    # aliasy
    "komu",
    "czemu",
    "z_kim",
    "z_czym",
    "o_kim",
    "o_czym",
]


def _pytanie(wyraz: str, przypadek: str, liczba: str | None, default):
    """Wspólny rdzeń funkcji pytaniowych (patrz spec §3.2).

    Lemat i liczbę bierzemy z JEDNEJ, tej samej analizy — nigdy nie mieszamy.
    """
    analizy = podaj(wyraz)
    if not analizy:  # wyraz nieznany
        return _rozwiaz_brak(wyraz, default)
    nom = [a for a in analizy if a.przypadek == MIANOWNIK]
    kandydaci = nom or analizy  # preferuj mianownik; inaczej best-effort (oblique)
    # jedna analiza deterministycznie: alfabetycznie po lemacie, przy remisie sg < pl
    wybrana = min(kandydaci, key=lambda a: (a.lemat, 0 if a.liczba == POJEDYNCZA else 1))
    liczba_efektywna = liczba if liczba is not None else wybrana.liczba
    forma = odmien(wybrana.lemat, przypadek, liczba_efektywna, default=None)
    if forma is None:  # slot nie istnieje (np. brak danej liczby dla lematu)
        return _rozwiaz_brak(wyraz, default)
    return forma


def kogo_czego(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Dopełniacz (kogo? czego?) wyrazu zakładanego w mianowniku.

    >>> kogo_czego("wydział")
    'wydziału'
    >>> kogo_czego("wydziały")
    'wydziałów'
    """
    return _pytanie(wyraz, DOPEŁNIACZ, liczba, default)


def komu_czemu(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Celownik (komu? czemu?). Alias: ``komu``, ``czemu``."""
    return _pytanie(wyraz, CELOWNIK, liczba, default)


def kogo_co(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Biernik (kogo? co?)."""
    return _pytanie(wyraz, BIERNIK, liczba, default)


def z_kim_z_czym(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Narzędnik (z kim? z czym?). Alias: ``z_kim``, ``z_czym``."""
    return _pytanie(wyraz, NARZĘDNIK, liczba, default)


def o_kim_o_czym(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Miejscownik (o kim? o czym?). Alias: ``o_kim``, ``o_czym``."""
    return _pytanie(wyraz, MIEJSCOWNIK, liczba, default)


# Aliasy — TE SAME obiekty funkcji związane pod wieloma nazwami.
komu = komu_czemu
czemu = komu_czemu
z_kim = z_kim_z_czym
z_czym = z_kim_z_czym
o_kim = o_kim_o_czym
o_czym = o_kim_o_czym


def podstawowa_forma(wyraz: str, *, default=TEN_SAM_WYRAZ):
    """Forma podstawowa (lemat SGJP) dowolnej formy fleksyjnej.

    Zwraca lemat = forma słownikowa: mianownik l.poj. dla rzeczowników
    policzalnych; dla plurale tantum (np. ``drzwi``) lemat jest l.mnogiej.
    Homografia → pierwszy lemat deterministycznie.

    >>> podstawowa_forma("wydziałów")
    'wydział'
    >>> podstawowa_forma("jednostce")
    'jednostka'
    """
    analizy = podaj(wyraz)
    if not analizy:
        return _rozwiaz_brak(wyraz, default)
    return sorted(a.lemat for a in analizy)[0]


def _czy_meskoosobowy(wyraz: str) -> bool:
    """Czy rzeczownik jest rodzaju męskoosobowego (m1)? Wykrywane z danych SGJP.

    Homograf mający analizę m1 (np. ``profesor`` = m1/f) traktujemy jak m1 —
    przy liczeniu chodzi zwykle o osoby.
    """
    return any(a.rodzaj == "m1" for a in podaj(wyraz))


def odmiana_liczebnikowa(wyraz, count, przypadek=MIANOWNIK, *, default=TEN_SAM_WYRAZ):
    """Forma rzeczownika narzucona przez liczbę ``count`` (zgoda liczebnikowa).

    Zwraca SAM rzeczownik w formie wymaganej przez polską składnię liczebnika,
    w zadanym przypadku frazy. Liczebnik słownie NIE jest generowany — numer
    doklejasz sam (``f"{count} {odmiana_liczebnikowa(...)}"``).

    Rodzaj (w tym męskoosobowy m1) jest WYKRYWANY AUTOMATYCZNIE z danych SGJP,
    więc rząd liczebnika jest dobrany poprawnie dla obu grup.

    Reguła:

    - ``count == 1`` → l.poj. w przypadku frazy;
    - mianownik/biernik: nie-męskoosobowe z końcówką 2–4 (nie 12–14) → l.mn.,
      zgoda (``dwa wydziały``); w pozostałych (m1 dla ≥2 oraz nie-m1 5+/0) →
      dopełniacz l.mn., rząd (``dwóch studentów`` / ``pięciu studentów`` /
      ``pięć wydziałów``);
    - przypadki zależne (dop./cel./narz./miejsc.) → l.mn. w tym przypadku.

    >>> odmiana_liczebnikowa("wydział", 2)
    'wydziały'
    >>> odmiana_liczebnikowa("wydział", 5)
    'wydziałów'
    >>> odmiana_liczebnikowa("student", 2)   # m1 wykryty automatycznie
    'studentów'
    >>> odmiana_liczebnikowa("wydział", 5, NARZĘDNIK)
    'wydziałami'

    ``default`` jak w pozostałych funkcjach (domyślnie passthrough).
    """
    n = abs(int(count))
    if n == 1:
        return odmien(wyraz, przypadek, POJEDYNCZA, default=default)
    d, dd = n % 10, n % 100
    grupa_2_4 = 2 <= d <= 4 and not 12 <= dd <= 14
    # zgoda (nom/acc l.mn.) tylko dla nie-męskoosobowych w grupie 2-4;
    # m1 oraz 5+/0 rządzą dopełniaczem l.mn.
    zgoda_nom = grupa_2_4 and not _czy_meskoosobowy(wyraz)
    if przypadek in (MIANOWNIK, BIERNIK) and not zgoda_nom:
        return odmien(wyraz, DOPEŁNIACZ, MNOGA, default=default)  # rząd: dopełniacz l.mn.
    return odmien(wyraz, przypadek, MNOGA, default=default)  # zgoda l.mn. / przypadek zależny
