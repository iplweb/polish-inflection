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

__version__ = "0.1.0"

__all__ = [
    # funkcje
    "odmien",
    "odmien_lub_none",
    "odmien_lub_wyraz",
    "odmien_warianty",
    "podaj",
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
    # sentinel
    "TEN_SAM_WYRAZ",
    "__version__",
]
