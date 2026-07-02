"""Nazwane stałe przypadków i liczby (mapowane 1:1 na tagi SGJP) oraz sentinel
``TEN_SAM_WYRAZ`` dla trybu passthrough w :func:`polish_inflection.core.odmien`.
"""

# Przypadki — wartości identyczne z tagami SGJP.
MIANOWNIK = "nom"  # kto? co?
DOPEŁNIACZ = "gen"  # kogo? czego?
CELOWNIK = "dat"  # komu? czemu?
BIERNIK = "acc"  # kogo? co?
NARZĘDNIK = "inst"  # (z) kim? (z) czym?
MIEJSCOWNIK = "loc"  # o kim? o czym?
WOŁACZ = "voc"  # o!

# Liczba.
POJEDYNCZA = "sg"
MNOGA = "pl"

PRZYPADKI = (MIANOWNIK, DOPEŁNIACZ, CELOWNIK, BIERNIK, NARZĘDNIK, MIEJSCOWNIK, WOŁACZ)
LICZBY = (POJEDYNCZA, MNOGA)

# Zbiory do szybkiej walidacji w buildzie/runtime.
PRZYPADKI_SET = frozenset(PRZYPADKI)
LICZBY_SET = frozenset(LICZBY)


class _TenSamWyraz:
    """Sentinel: gdy przekazany jako ``default`` do ``odmien`` i brak formy —
    zwróć wejściowy wyraz zamiast rzucać wyjątek."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "TEN_SAM_WYRAZ"


#: Wartownik dla ``odmien(..., default=TEN_SAM_WYRAZ)`` — passthrough wejścia.
TEN_SAM_WYRAZ = _TenSamWyraz()
