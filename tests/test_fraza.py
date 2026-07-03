"""Testy odmiany wielowyrazowych nazw własnych (``odmien_fraze``).

Test integracyjny: potrzebuje szerokiego słownika (realne nazwy uczelni), więc
zamiast małej fixtury domenowej z ``conftest`` wskazuje na pełny indeks z pakietu
``polish-inflection-data`` (editable w dev). Rozpoznanie przymiotników w tych
frazach korzysta też ze zbioru baz (``przymiotniki.marisa``) z tego pakietu.
"""

import pytest

from polish_inflection import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    MIEJSCOWNIK,
    MNOGA,
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
    # przymiotnik z homografem rzeczownikowym (nom/acc) — MUSI się odmienić, nie zamrozić
    ("język polski", DOPEŁNIACZ, "języka polskiego"),
    # wielkość liter rozstrzyga: mała = przymiotnik (odmienia), wielka = nazwa własna (zamraża)
    ("instytut polski", DOPEŁNIACZ, "instytutu polskiego"),
    ("Instytut Polski", DOPEŁNIACZ, "Instytutu Polski"),
    # POZYCJA rozstrzyga homograf "Polski": PRZED głową = przymiotnik (odmienia),
    # PO głowie z czytaniem dopełniaczowym = nazwa własna (zamraża, wyżej).
    ("Polski Instytut Weterynaryjny", DOPEŁNIACZ, "Polskiego Instytutu Weterynaryjnego"),
    ("Polski Uniwersytet", DOPEŁNIACZ, "Polskiego Uniwersytetu"),
    # biernik: żywotność głowy rządzi zgodą przymiotnika (żywotny: biernik=dopełniacz)
    ("nowy pracownik", BIERNIK, "nowego pracownika"),
    ("stary nauczyciel", BIERNIK, "starego nauczyciela"),
    ("Uniwersytet Lubelski", BIERNIK, "Uniwersytet Lubelski"),  # nieżywotny: biernik=mianownik
    # inne przypadki
    ("Uniwersytet Lubelski", MIEJSCOWNIK, "Uniwersytecie Lubelskim"),
    ("Uniwersytet Lubelski", CELOWNIK, "Uniwersytetowi Lubelskiemu"),
    ("Akademia Medyczna", NARZĘDNIK, "Akademią Medyczną"),
    ("Wyższa Szkoła Pedagogiczna", NARZĘDNIK, "Wyższą Szkołą Pedagogiczną"),
]


@pytest.mark.parametrize("fraza,przypadek,oczekiwana", KORPUS)
def test_korpus(fraza, przypadek, oczekiwana):
    assert odmien_fraze(fraza, przypadek) == oczekiwana


# ── Frazy pisane małą literą = zwykłe rzeczowniki + przymiotnik (NIE nazwy własne) ──
# Reguła: cała fraza małą literą ⇒ NIE traktuj słów jak proper-nouny z gazeteera
# (żaden homograf nazwy miejscowej nie może „ukraść" roli głowy) i NIE kapitalizuj.

FRAZY_MALA_LITERA = [
    # sedno bug-reportu: głowa-rzeczownik się odmienia, przymiotnik uzgadnia, zero kapitalizacji
    ("dupa wołowa", DOPEŁNIACZ, "dupy wołowej"),
    ("dupa wołowa", NARZĘDNIK, "dupą wołową"),
    ("sala gimnastyczna", DOPEŁNIACZ, "sali gimnastycznej"),
    ("czerwony samochód", DOPEŁNIACZ, "czerwonego samochodu"),
    # leniwie małą literą wpisana nazwa uczelni — poprawna odmiana, ale bez kapitalizacji
    ("uniwersytet warszawski", DOPEŁNIACZ, "uniwersytetu warszawskiego"),
]


@pytest.mark.parametrize("fraza,przypadek,oczekiwana", FRAZY_MALA_LITERA)
def test_mala_litera_zwykle_rzeczowniki(fraza, przypadek, oczekiwana):
    assert odmien_fraze(fraza, przypadek) == oczekiwana


def test_mala_litera_nie_kapitalizuje():
    out = odmien_fraze("dupa wołowa", DOPEŁNIACZ)
    assert out == out.lower(), f"nie powinno kapitalizować: {out!r}"


# ── Liczba mnoga wielowyrazowych nazw: przymiotnik MUSI uzgodnić liczbę ──────
KORPUS_MNOGA = [
    ("Wydział Lekarski", DOPEŁNIACZ, "Wydziałów Lekarskich"),
    ("Uniwersytet Lubelski", DOPEŁNIACZ, "Uniwersytetów Lubelskich"),
    ("Akademia Medyczna", DOPEŁNIACZ, "Akademii Medycznych"),
    ("Politechnika Warszawska", MIEJSCOWNIK, "Politechnikach Warszawskich"),
]


@pytest.mark.parametrize("fraza,przypadek,oczekiwana", KORPUS_MNOGA)
def test_korpus_mnoga(fraza, przypadek, oczekiwana):
    assert odmien_fraze(fraza, przypadek, MNOGA) == oczekiwana


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
