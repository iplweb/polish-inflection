"""Testy odmiany wielowyrazowych nazw własnych (``odmien_fraze``).

Test integracyjny: potrzebuje szerokiego słownika (realne nazwy uczelni), więc
zamiast małej fixtury domenowej z ``conftest`` wskazuje na pełny pakietowy
indeks. Wymaga zbudowanego ``src/polish_inflection/data/*.marisa`` (jest w repo).
"""

import pytest

from polish_inflection import (
    CELOWNIK,
    DOPEŁNIACZ,
    MIEJSCOWNIK,
    NARZĘDNIK,
    BrakOdmiany,
    core,
    odmien_fraze,
)


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
    ("Uniwersytet Lubelski", DOPEŁNIACZ, "Uniwersytetu Lubelskiego"),
    ("Uniwersytet Warszawski", DOPEŁNIACZ, "Uniwersytetu Warszawskiego"),
    ("Uniwersytet Jagielloński", DOPEŁNIACZ, "Uniwersytetu Jagiellońskiego"),
    ("Wydział Lekarski", DOPEŁNIACZ, "Wydziału Lekarskiego"),
    ("Uniwersytet Medyczny", DOPEŁNIACZ, "Uniwersytetu Medycznego"),
    # głowa żeńska (pełna zgoda rodzaju żeńskiego)
    ("Akademia Medyczna", DOPEŁNIACZ, "Akademii Medycznej"),
    ("Politechnika Warszawska", DOPEŁNIACZ, "Politechniki Warszawskiej"),
    # przymiotnik przed I po głowie
    ("Szkoła Główna Handlowa", DOPEŁNIACZ, "Szkoły Głównej Handlowej"),
    ("Wyższa Szkoła Pedagogiczna", DOPEŁNIACZ, "Wyższej Szkoły Pedagogicznej"),
    ("Katolicki Uniwersytet Lubelski", DOPEŁNIACZ, "Katolickiego Uniwersytetu Lubelskiego"),
    # dopełnienie zależne (dopełniacz) — zamrożone
    ("Instytut Technologii Stosowanej", DOPEŁNIACZ, "Instytutu Technologii Stosowanej"),
    ("Instytut Fizyki", DOPEŁNIACZ, "Instytutu Fizyki"),
    ("Wydział Matematyki i Informatyki", DOPEŁNIACZ, "Wydziału Matematyki i Informatyki"),
    # inne przypadki
    ("Uniwersytet Lubelski", MIEJSCOWNIK, "Uniwersytecie Lubelskim"),
    ("Uniwersytet Lubelski", CELOWNIK, "Uniwersytetowi Lubelskiemu"),
    ("Akademia Medyczna", NARZĘDNIK, "Akademią Medyczną"),
    ("Wyższa Szkoła Pedagogiczna", NARZĘDNIK, "Wyższą Szkołą Pedagogiczną"),
]


@pytest.mark.parametrize("fraza,przypadek,oczekiwana", KORPUS)
def test_korpus(fraza, przypadek, oczekiwana):
    assert odmien_fraze(fraza, przypadek) == oczekiwana


def test_marker_im_zamraza_ogon():
    assert (
        odmien_fraze("Uniwersytet im. Marii Curie-Skłodowskiej", DOPEŁNIACZ)
        == "Uniwersytetu im. Marii Curie-Skłodowskiej"
    )


def test_zachowanie_wielkosci_liter():
    # odmieniona głowa i przydawka zachowują kapitalizację oryginału
    out = odmien_fraze("Uniwersytet Lubelski", DOPEŁNIACZ)
    assert out[0].isupper() and "Lubelskiego" in out


def test_pojedynczy_rzeczownik_tez_dziala():
    assert odmien_fraze("Uniwersytet", DOPEŁNIACZ) == "Uniwersytetu"


def test_brak_glowy_fallback_passthrough():
    # brak rozpoznanej głowy-rzeczownika -> domyślnie zwróć frazę bez zmian
    assert odmien_fraze("qwerty zxcvbn", DOPEŁNIACZ) == "qwerty zxcvbn"


def test_brak_glowy_none():
    assert odmien_fraze("qwerty zxcvbn", DOPEŁNIACZ, default=None) is None


def test_brak_glowy_raises():
    from polish_inflection import RAISES

    with pytest.raises(BrakOdmiany):
        odmien_fraze("qwerty zxcvbn", DOPEŁNIACZ, default=RAISES)


def test_pusta_fraza():
    assert odmien_fraze("", DOPEŁNIACZ) == ""
