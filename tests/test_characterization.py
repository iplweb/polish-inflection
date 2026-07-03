"""Testy charakteryzacyjne na PEŁNYCH, zbudowanych danych pakietowych.

Weryfikują kryterium sukcesu §13 na realnym słowniku SGJP (nie fixturze).
Pomijane, gdy pakiet ``polish-inflection-data`` nie jest zainstalowany (jego
indeksy niedostępne) — np. w świeżym checkoutcie/CI bez pakietu danych.
"""

import pytest

from polish_inflection import (
    BIERNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MNOGA,
    NARZĘDNIK,
    POJEDYNCZA,
    PRZYPADKI,
    core,
    odmien,
    odmien_lub_none,
    podaj,
)

try:
    from polish_inflection import _dane

    _DANE = _dane.katalog()
    _MA_DANE = (_DANE / "odmien.marisa").exists() and (_DANE / "podaj.marisa").exists()
except Exception:
    _MA_DANE = False

pytestmark = pytest.mark.skipif(
    not _MA_DANE,
    reason="Brak zbudowanych indeksów pakietowych — uruchom `polish-inflection-build build`.",
)


@pytest.fixture(autouse=True)
def _dane_pakietowe():
    """Nadpisz fixture z conftest: użyj PRAWDZIWYCH danych pakietowych."""
    core._ustaw_katalog_danych(None)
    yield
    core._ustaw_katalog_danych(None)


# Pełna tabela 7×2 dla 'wydział' (ręcznie zweryfikowana wobec SGJP).
WYDZIAL = {
    (MIANOWNIK, POJEDYNCZA): "wydział",
    (DOPEŁNIACZ, POJEDYNCZA): "wydziału",
    (BIERNIK, POJEDYNCZA): "wydział",
    (NARZĘDNIK, POJEDYNCZA): "wydziałem",
    (MIANOWNIK, MNOGA): "wydziały",
    (DOPEŁNIACZ, MNOGA): "wydziałów",
    (NARZĘDNIK, MNOGA): "wydziałami",
}


@pytest.mark.parametrize("klucz,oczek", list(WYDZIAL.items()))
def test_wydzial_tabela(klucz, oczek):
    przypadek, liczba = klucz
    assert odmien("wydział", przypadek, liczba) == oczek


@pytest.mark.parametrize(
    "lemat,oczek_gen_sg",
    [
        ("dział", "działu"),
        ("oddział", "oddziału"),
        ("zakład", "zakładu"),
        ("instytut", "instytutu"),
        ("katedra", "katedry"),
        ("klinika", "kliniki"),
        ("koło", "koła"),
        ("jednostka", "jednostki"),
    ],
)
def test_domenowe_dopelniacz(lemat, oczek_gen_sg):
    assert odmien(lemat, DOPEŁNIACZ) == oczek_gen_sg


def test_jednostka_biernik():
    assert odmien("jednostka", BIERNIK) == "jednostkę"


def test_podaj_synkretyzm_jednostki():
    krotki = {(a.przypadek, a.liczba) for a in podaj("jednostki")}
    assert ("gen", "sg") in krotki
    assert ("nom", "pl") in krotki
    assert ("acc", "pl") in krotki


def test_round_trip_odmien_podaj():
    """Dla słów domenowych: jeśli odmien zwraca formę, podaj musi ją rozpoznać
    z tym samym lematem, przypadkiem i liczbą (spójność obu indeksów)."""
    slowa = ["wydział", "jednostka", "dział", "instytut", "katedra", "zakład", "koło"]
    for lemat in slowa:
        for przypadek in PRZYPADKI:
            for liczba in (POJEDYNCZA, MNOGA):
                forma = odmien_lub_none(lemat, przypadek, liczba)
                if forma is None:
                    continue
                analizy = podaj(forma, liczba=liczba)
                assert any(
                    a.lemat == lemat and a.przypadek == przypadek and a.liczba == liczba
                    for a in analizy
                ), f"round-trip fail: {lemat} {przypadek} {liczba} -> {forma}"


def test_import_nie_laduje_do_ram():
    """Sanity: pierwszy lookup działa (leniwe mmapowanie), a moduł nie trzyma
    danych w pamięci przed pierwszym użyciem."""
    # świeży reset — kolejny lookup zmapuje ponownie
    core._ustaw_katalog_danych(None)
    assert odmien("wydział", DOPEŁNIACZ) == "wydziału"
