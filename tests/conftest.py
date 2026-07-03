"""Fixtury testowe.

Budujemy MAŁE indeksy marisa-trie z realnych linii SGJP dla słów domenowych
(``tests/fixtures/sgjp_domain.tab``) i wskazujemy na nie runtime przez
``core._ustaw_katalog_danych``. Dzięki temu testy ``core`` biegną na prawdziwych
formach, ale bez zależności od zbudowanego pakietowego indeksu ani 42 MB SGJP.
"""

from pathlib import Path

import pytest

from polish_inflection import build, core

FIXTURES = Path(__file__).parent / "fixtures"
DOMAIN_TAB = FIXTURES / "sgjp_domain.tab"


@pytest.fixture(scope="session")
def zbudowane_dane(tmp_path_factory) -> Path:
    """Zbuduj odmien.marisa/podaj.marisa z fixtury domenowej; zwróć katalog."""
    out = tmp_path_factory.mktemp("indeksy")
    build.zbuduj_z_tab(DOMAIN_TAB, out, data_build="test")
    return out


@pytest.fixture(autouse=True)
def _wskaz_dane(zbudowane_dane):
    """Wskaż runtime na zbudowane dane testowe; posprzątaj po teście."""
    core._ustaw_katalog_danych(zbudowane_dane)
    yield
    core._ustaw_katalog_danych(None)
