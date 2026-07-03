"""Testy integralności pakietu ``polish-inflection-data`` (jeśli zainstalowany).

Sprawdzają, że artefakty istnieją, otwierają się przez marisa, schemat zgadza się
z kodem, a zbiór baz przymiotników zawiera prawdziwe bazy (i nie zawiera atrap).
Pomijane, gdy pakiet danych nie jest zainstalowany.
"""

import json

import pytest

dane = pytest.importorskip("polish_inflection_data")

from polish_inflection import _dane  # noqa: E402  (po importorskip)


def _build_info() -> dict:
    return json.loads((dane.KATALOG / "BUILD_INFO.json").read_text(encoding="utf-8"))


def test_schema_zgodny_z_build_info():
    assert dane.SCHEMA == _build_info()["schema"]


def test_schema_zgodny_z_kodem():
    # runtime guard używa _dane._SCHEMA; musi zgadzać się z pakietem
    assert dane.SCHEMA == _dane._SCHEMA


def test_wersja_sgjp_niepusta():
    assert dane.WERSJA_SGJP and "sgjp" in dane.WERSJA_SGJP.lower()


@pytest.mark.parametrize("nazwa", ["odmien.marisa", "podaj.marisa", "przymiotniki.marisa"])
def test_artefakt_istnieje_i_sie_otwiera(nazwa):
    import marisa_trie

    sciezka = dane.KATALOG / nazwa
    assert sciezka.exists()
    trie = marisa_trie.BytesTrie() if nazwa != "przymiotniki.marisa" else marisa_trie.Trie()
    trie.mmap(str(sciezka))  # nie rzuca => plik jest poprawnym marisa


def test_licencja_sgjp_w_pakiecie():
    # nota licencyjna SGJP MUSI jechać z danymi (utwory zależne)
    assert (dane.KATALOG / "LICENSE.sgjp").exists()


def test_zbior_baz_zawiera_prawdziwe_nie_atrapy():
    import marisa_trie

    bazy = marisa_trie.Trie()
    bazy.mmap(str(dane.KATALOG / "przymiotniki.marisa"))
    for prawdziwa in ("lubelski", "wyższy", "najwyższy", "zjednoczony", "wołowy"):
        assert prawdziwa in bazy, f"brak prawdziwej bazy: {prawdziwa}"
    for atrapa in ("michały", "dupy", "kobiety"):
        assert atrapa not in bazy, f"atrapa w zbiorze baz: {atrapa}"
