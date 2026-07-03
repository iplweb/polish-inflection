"""Testy odmiana_liczebnikowa (zgoda liczebnikowa rzeczownika)."""

import pytest

from polish_inflection import (
    BIERNIK,
    DOPEŁNIACZ,
    MIEJSCOWNIK,
    NARZĘDNIK,
    odmiana_liczebnikowa,
)

# ── mianownik frazy (domyślny): 1 / 2-4 / 5+ ────────────────────────────────


@pytest.mark.parametrize(
    "count,oczek",
    [
        (1, "wydział"),  # l.poj.
        (2, "wydziały"),  # 2-4 -> nom pl
        (3, "wydziały"),
        (4, "wydziały"),
        (5, "wydziałów"),  # 5+ -> gen pl (rząd)
        (0, "wydziałów"),  # 0 -> gen pl
        (12, "wydziałów"),  # 12-14 wyjątek -> gen pl
        (13, "wydziałów"),
        (14, "wydziałów"),
        (22, "wydziały"),  # końcówka 2 (nie 12) -> nom pl
        (23, "wydziały"),
        (25, "wydziałów"),  # 5+ -> gen pl
        (21, "wydziałów"),  # końcówka 1, ale nie 1 -> gen pl
        (101, "wydziałów"),
        (102, "wydziały"),  # końcówka 2 -> nom pl
    ],
)
def test_mianownik_wydzial(count, oczek):
    assert odmiana_liczebnikowa("wydział", count) == oczek


def test_ujemne_przez_abs():
    assert odmiana_liczebnikowa("wydział", -5) == "wydziałów"


# ── przypadki zależne: rzeczownik w l.mn. tego przypadka ─────────────────────


@pytest.mark.parametrize(
    "count,oczek",
    [
        (1, "wydziałem"),  # l.poj.
        (2, "wydziałami"),  # l.mn. narzędnika
        (5, "wydziałami"),
        (12, "wydziałami"),
    ],
)
def test_narzednik_wydzial(count, oczek):
    assert odmiana_liczebnikowa("wydział", count, NARZĘDNIK) == oczek


def test_dopelniacz_i_miejscownik():
    assert odmiana_liczebnikowa("wydział", 5, DOPEŁNIACZ) == "wydziałów"
    assert odmiana_liczebnikowa("wydział", 2, DOPEŁNIACZ) == "wydziałów"
    assert odmiana_liczebnikowa("wydział", 5, MIEJSCOWNIK) == "wydziałach"


# ── rodzaj żeński ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "count,oczek",
    [
        (1, "jednostka"),
        (2, "jednostki"),  # nom pl
        (5, "jednostek"),  # gen pl
    ],
)
def test_rodzaj_zenski(count, oczek):
    assert odmiana_liczebnikowa("jednostka", count) == oczek


def test_zenski_narzednik():
    assert odmiana_liczebnikowa("jednostka", 5, NARZĘDNIK) == "jednostkami"
    assert odmiana_liczebnikowa("jednostka", 1, NARZĘDNIK) == "jednostką"


# ── rodzaj męskoosobowy (m1) — wykrywany automatycznie ──────────────────────


def test_m1_mianownik_2_4_to_dopelniacz():
    # m1: 'dwóch studentów' (dop. l.mn.), NIE 'dwaj studenci'
    assert odmiana_liczebnikowa("student", 2) == "studentów"
    assert odmiana_liczebnikowa("student", 3) == "studentów"
    assert odmiana_liczebnikowa("student", 4) == "studentów"


def test_m1_mianownik_5plus():
    assert odmiana_liczebnikowa("student", 5) == "studentów"  # 'pięciu studentów'
    assert odmiana_liczebnikowa("student", 1) == "student"


def test_m1_biernik_to_dopelniacz():
    # m1 biernik = dopełniacz: 'widzę dwóch/pięciu studentów'
    assert odmiana_liczebnikowa("student", 2, BIERNIK) == "studentów"
    assert odmiana_liczebnikowa("student", 5, BIERNIK) == "studentów"


def test_m1_przypadki_zalezne_jak_reszta():
    # oblique: rzeczownik w l.mn. tego przypadka (jak nie-m1)
    assert odmiana_liczebnikowa("student", 2, NARZĘDNIK) == "studentami"
    assert odmiana_liczebnikowa("student", 5, NARZĘDNIK) == "studentami"


def test_niem1_2_4_pozostaje_zgoda():
    # kontrola: nie-m1 przy 2-4 nadal daje mianownik l.mn. (zgoda)
    assert odmiana_liczebnikowa("wydział", 2) == "wydziały"
    assert odmiana_liczebnikowa("jednostka", 2) == "jednostki"


# ── homograf rodzajowy: profesor = m1 (osoba) + f (nieodmienny) ─────────────


def test_homograf_profesor_bierze_forme_m1():
    # slot dop. l.mn. zawiera 'profesor' (żeński nieodm.) i 'profesorów' (m1);
    # dla liczenia osób bierzemy m1 -> 'profesorów', nie 'profesor'
    assert odmiana_liczebnikowa("profesor", 5) == "profesorów"
    assert odmiana_liczebnikowa("profesor", 2) == "profesorów"  # m1 -> dopełniacz
    assert odmiana_liczebnikowa("profesor", 5, NARZĘDNIK) == "profesorami"
    assert odmiana_liczebnikowa("profesor", 1) == "profesor"  # mianownik l.poj.


# ── brak formy ──────────────────────────────────────────────────────────────


def test_nieznany_wyraz_passthrough():
    assert odmiana_liczebnikowa("zzzqwerty", 5) == "zzzqwerty"


def test_nieznany_wyraz_default_none():
    assert odmiana_liczebnikowa("zzzqwerty", 5, default=None) is None
