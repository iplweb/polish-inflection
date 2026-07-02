"""Testy warstwy pytań przypadkowych i podstawowa_forma."""

import pytest

from polish_inflection import (
    MNOGA,
    POJEDYNCZA,
    RAISES,
    BrakOdmiany,
    kogo_co,
    kogo_czego,
    komu_czemu,
    o_kim_o_czym,
    podstawowa_forma,
    z_kim_z_czym,
)
from polish_inflection import pytania as p

# ── funkcje pytaniowe: podstawowe formy ─────────────────────────────────────


def test_kogo_czego():
    assert kogo_czego("wydział") == "wydziału"


def test_komu_czemu():
    assert komu_czemu("jednostka") == "jednostce"


def test_kogo_co():
    assert kogo_co("jednostka") == "jednostkę"


def test_z_kim_z_czym():
    assert z_kim_z_czym("klinika") == "kliniką"


def test_o_kim_o_czym():
    assert o_kim_o_czym("wydział") == "wydziale"


# ── zgadywanie liczby ───────────────────────────────────────────────────────


def test_zgaduje_liczbe_mnoga_z_mianownika():
    # wejście w mianowniku l.mn. -> wynik w l.mn.
    assert kogo_czego("wydziały") == "wydziałów"


def test_zgaduje_liczbe_pojedyncza():
    assert kogo_czego("wydział") == "wydziału"


def test_liczba_wymuszona():
    # jawne liczba= nadpisuje zgadywanie
    assert kogo_czego("wydział", liczba=MNOGA) == "wydziałów"
    assert kogo_czego("wydziały", liczba=POJEDYNCZA) == "wydziału"


def test_wejscie_oblique_zachowuje_liczbe():
    # 'wydziałów' to dopełniacz l.mn. (nie mianownik) -> best-effort, l.mn. zachowana
    assert kogo_czego("wydziałów") == "wydziałów"


# ── aliasy ──────────────────────────────────────────────────────────────────


def test_aliasy_to_ten_sam_obiekt():
    assert p.komu is p.komu_czemu
    assert p.czemu is p.komu_czemu
    assert p.z_kim is p.z_kim_z_czym
    assert p.z_czym is p.z_kim_z_czym
    assert p.o_kim is p.o_kim_o_czym
    assert p.o_czym is p.o_kim_o_czym


def test_aliasy_daja_ten_sam_wynik():
    assert p.komu("jednostka") == komu_czemu("jednostka")
    assert p.o_czym("wydział") == o_kim_o_czym("wydział")


# ── default / brak formy ────────────────────────────────────────────────────


def test_default_passthrough_domyslnie():
    assert kogo_czego("zzzqwerty") == "zzzqwerty"


def test_default_none():
    assert kogo_czego("zzzqwerty", default=None) is None


def test_default_wartosc():
    assert kogo_czego("zzzqwerty", default="—") == "—"


def test_default_raises():
    with pytest.raises(BrakOdmiany):
        kogo_czego("zzzqwerty", default=RAISES)


def test_nieznany_nie_rzuca_indexerror():
    # S1: nieznany wyraz idzie przez default, nie wywala IndexError
    assert kogo_czego("zzzqwerty") == "zzzqwerty"


# ── podstawowa_forma ────────────────────────────────────────────────────────


def test_podstawowa_forma_z_oblique():
    assert podstawowa_forma("wydziałów") == "wydział"
    assert podstawowa_forma("jednostce") == "jednostka"


def test_podstawowa_forma_idempotentna():
    assert podstawowa_forma("wydział") == "wydział"


def test_podstawowa_forma_plurale_tantum():
    # S2: lemat plurale tantum jest l.mnogiej (nie ma l.poj.)
    assert podstawowa_forma("drzwiach") == "drzwi"


def test_podstawowa_forma_nieznane():
    assert podstawowa_forma("zzzqwerty") == "zzzqwerty"
    assert podstawowa_forma("zzzqwerty", default=None) is None


# ── plurale tantum w funkcjach pytaniowych ──────────────────────────────────


def test_plurale_tantum_kogo_czego():
    # 'drzwi' (mian. l.mn.) -> dopełniacz l.mn. 'drzwi'
    assert kogo_czego("drzwi") == "drzwi"
    assert z_kim_z_czym("drzwi") == "drzwiami"


# ── round-trip ──────────────────────────────────────────────────────────────


def test_round_trip_podstawowa_pytanie():
    # oblique -> podstawowa_forma -> pytanie daje poprawną formę l.poj.
    assert kogo_czego(podstawowa_forma("wydziałów")) == "wydziału"
    assert kogo_czego(podstawowa_forma("jednostce")) == "jednostki"
    assert komu_czemu(podstawowa_forma("kliniką")) == "klinice"
