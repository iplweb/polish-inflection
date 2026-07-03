"""Testy odmiany wielowyrazowych nazw własnych (``odmien_fraze``).

Test integracyjny: potrzebuje szerokiego słownika (realne nazwy uczelni), więc
zamiast małej fixtury domenowej z ``conftest`` wskazuje na pełny pakietowy
indeks. Wymaga zbudowanego ``src/polish_inflection/data/*.marisa`` (jest w repo).
"""

import pytest

from polish_inflection import BrakOdmiany, core, odmien_fraze


@pytest.fixture(autouse=True)
def _pelny_indeks(_wskaz_dane):
    # zależność od conftestowego `_wskaz_dane` gwarantuje, że nasza fixtura
    # uruchomi się PO nim i nadpisze katalog danych na pakietowy (pełny SGJP).
    core._ustaw_katalog_danych(None)
    yield
    core._ustaw_katalog_danych(None)


# Korpus realnych nazw uczelni/wydziałów: (fraza, przypadek) -> oczekiwana forma.
KORPUS = [
    # przymiotnik po głowie (rzeczownik + przymiotnik uzgadniający)
    ("Uniwersytet Lubelski", "gen", "Uniwersytetu Lubelskiego"),
    ("Uniwersytet Warszawski", "gen", "Uniwersytetu Warszawskiego"),
    ("Uniwersytet Jagielloński", "gen", "Uniwersytetu Jagiellońskiego"),
    ("Wydział Lekarski", "gen", "Wydziału Lekarskiego"),
    ("Uniwersytet Medyczny", "gen", "Uniwersytetu Medycznego"),
    # głowa żeńska (pełna zgoda rodzaju żeńskiego)
    ("Akademia Medyczna", "gen", "Akademii Medycznej"),
    ("Politechnika Warszawska", "gen", "Politechniki Warszawskiej"),
    # przymiotnik przed I po głowie
    ("Szkoła Główna Handlowa", "gen", "Szkoły Głównej Handlowej"),
    ("Wyższa Szkoła Pedagogiczna", "gen", "Wyższej Szkoły Pedagogicznej"),
    ("Katolicki Uniwersytet Lubelski", "gen", "Katolickiego Uniwersytetu Lubelskiego"),
    # dopełnienie zależne (dopełniacz) — zamrożone
    ("Instytut Technologii Stosowanej", "gen", "Instytutu Technologii Stosowanej"),
    ("Instytut Fizyki", "gen", "Instytutu Fizyki"),
    ("Wydział Matematyki i Informatyki", "gen", "Wydziału Matematyki i Informatyki"),
    # inne przypadki
    ("Uniwersytet Lubelski", "loc", "Uniwersytecie Lubelskim"),
    ("Uniwersytet Lubelski", "dat", "Uniwersytetowi Lubelskiemu"),
    ("Akademia Medyczna", "inst", "Akademią Medyczną"),
    ("Wyższa Szkoła Pedagogiczna", "inst", "Wyższą Szkołą Pedagogiczną"),
]


@pytest.mark.parametrize("fraza,przypadek,oczekiwana", KORPUS)
def test_korpus(fraza, przypadek, oczekiwana):
    assert odmien_fraze(fraza, przypadek) == oczekiwana


def test_marker_im_zamraza_ogon():
    assert (
        odmien_fraze("Uniwersytet im. Marii Curie-Skłodowskiej", "gen")
        == "Uniwersytetu im. Marii Curie-Skłodowskiej"
    )


def test_zachowanie_wielkosci_liter():
    # odmieniona głowa i przydawka zachowują kapitalizację oryginału
    out = odmien_fraze("Uniwersytet Lubelski", "gen")
    assert out[0].isupper() and "Lubelskiego" in out


def test_pojedynczy_rzeczownik_tez_dziala():
    assert odmien_fraze("Uniwersytet", "gen") == "Uniwersytetu"


def test_brak_glowy_fallback_passthrough():
    # brak rozpoznanej głowy-rzeczownika -> domyślnie zwróć frazę bez zmian
    assert odmien_fraze("qwerty zxcvbn", "gen") == "qwerty zxcvbn"


def test_brak_glowy_none():
    assert odmien_fraze("qwerty zxcvbn", "gen", default=None) is None


def test_brak_glowy_raises():
    from polish_inflection import RAISES

    with pytest.raises(BrakOdmiany):
        odmien_fraze("qwerty zxcvbn", "gen", default=RAISES)


def test_pusta_fraza():
    assert odmien_fraze("", "gen") == ""
