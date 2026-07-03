"""polish-inflection — odmiana polskich rzeczowników przez przypadki (dane SGJP).

Lekka, czysto-Pythonowa biblioteka: kierunek generacji (``odmien``) i analizy
zwrotnej (``podaj``), oparta o kompaktowe indeksy DAWG zbudowane z danych SGJP.
"""

from .const import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    LICZBY,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    NARZĘDNIK,
    POJEDYNCZA,
    PRZYPADKI,
    RAISES,
    TEN_SAM_WYRAZ,
    WOŁACZ,
)
from .core import (
    odmien,
    odmien_lub_none,
    odmien_lub_wyraz,
    odmien_warianty,
    podaj,
)
from .errors import Analiza, BrakOdmiany
from .pytania import (
    kogo_co,
    kogo_czego,
    komu_czemu,
    o_kim_o_czym,
    odmiana_liczebnikowa,
    podstawowa_forma,
    z_kim_z_czym,
)

__version__ = "0.3.1"

__all__ = [
    # funkcje odmiany
    "odmien",
    "odmien_lub_none",
    "odmien_lub_wyraz",
    "odmien_warianty",
    "podaj",
    # funkcje pytaniowe (kanoniczne; pełne aliasy w polish_inflection.pytania)
    "kogo_czego",
    "komu_czemu",
    "kogo_co",
    "z_kim_z_czym",
    "o_kim_o_czym",
    "podstawowa_forma",
    "odmiana_liczebnikowa",
    # typy / wyjątki
    "Analiza",
    "BrakOdmiany",
    # stałe przypadków
    "MIANOWNIK",
    "DOPEŁNIACZ",
    "CELOWNIK",
    "BIERNIK",
    "NARZĘDNIK",
    "MIEJSCOWNIK",
    "WOŁACZ",
    "PRZYPADKI",
    # liczby
    "POJEDYNCZA",
    "MNOGA",
    "LICZBY",
    # sentinele
    "TEN_SAM_WYRAZ",
    "RAISES",
    "__version__",
]
