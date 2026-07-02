"""Testy runtime API: odmien / podaj i zachowania brzegowe."""

import pytest

from polish_inflection import (
    BIERNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MNOGA,
    POJEDYNCZA,
    WOŁACZ,
    Analiza,
    BrakOdmiany,
    odmien,
    odmien_lub_none,
    odmien_lub_wyraz,
    odmien_warianty,
    podaj,
)

# ── odmien: formy główne (znane, ręcznie zweryfikowane wobec SGJP) ──────────


def test_odmien_dopelniacz_poj():
    assert odmien("wydział", DOPEŁNIACZ) == "wydziału"


def test_odmien_dopelniacz_mnoga():
    assert odmien("wydział", DOPEŁNIACZ, MNOGA) == "wydziałów"


def test_odmien_biernik_poj():
    assert odmien("jednostka", BIERNIK) == "jednostkę"


def test_odmien_domyslnie_pojedyncza():
    # domyślna liczba to POJEDYNCZA
    assert odmien("wydział", DOPEŁNIACZ) == odmien("wydział", DOPEŁNIACZ, POJEDYNCZA)


@pytest.mark.parametrize(
    "przypadek,liczba,oczek",
    [
        (MIANOWNIK, POJEDYNCZA, "wydział"),
        (DOPEŁNIACZ, POJEDYNCZA, "wydziału"),
        (BIERNIK, POJEDYNCZA, "wydział"),
        (MIANOWNIK, MNOGA, "wydziały"),
        (DOPEŁNIACZ, MNOGA, "wydziałów"),
    ],
)
def test_odmien_wydzial_tabela(przypadek, liczba, oczek):
    assert odmien("wydział", przypadek, liczba) == oczek


# ── odmien: zachowanie przy braku formy ─────────────────────────────────────


def test_odmien_brak_rzuca_wyjatek():
    with pytest.raises(BrakOdmiany):
        odmien("zzzqwerty", DOPEŁNIACZ)


def test_odmien_default_none():
    assert odmien("zzzqwerty", DOPEŁNIACZ, default=None) is None
    assert odmien_lub_none("zzzqwerty", DOPEŁNIACZ) is None


def test_odmien_default_passthrough():
    assert odmien_lub_wyraz("zzzqwerty", DOPEŁNIACZ) == "zzzqwerty"


def test_odmien_default_dowolny():
    assert odmien("zzzqwerty", DOPEŁNIACZ, default="—") == "—"


def test_odmien_lub_none_znajduje():
    assert odmien_lub_none("wydział", DOPEŁNIACZ) == "wydziału"


# ── odmien_warianty ─────────────────────────────────────────────────────────


def test_warianty_zawiera_forme_glowna():
    warianty = odmien_warianty("wydział", DOPEŁNIACZ)
    assert warianty == ["wydziału"]


def test_warianty_puste_dla_nieznanego():
    assert odmien_warianty("zzzqwerty", DOPEŁNIACZ) == []


def test_warianty_posortowane():
    w = odmien_warianty("wydział", WOŁACZ)
    assert w == sorted(w)


# ── podaj: kierunek zwrotny + synkretyzm ────────────────────────────────────


def test_podaj_synkretyzm_jednostki():
    analizy = podaj("jednostki")
    assert all(isinstance(a, Analiza) for a in analizy)
    krotki = {(a.przypadek, a.liczba) for a in analizy}
    # jednostki = gen sg + nom/acc/voc pl
    assert ("gen", "sg") in krotki
    assert ("nom", "pl") in krotki
    assert ("acc", "pl") in krotki
    assert all(a.lemat == "jednostka" and a.rodzaj == "f" for a in analizy)


def test_podaj_filtr_liczby():
    tylko_mn = podaj("jednostki", liczba=MNOGA)
    assert tylko_mn
    assert all(a.liczba == "pl" for a in tylko_mn)
    assert ("gen", "sg") not in {(a.przypadek, a.liczba) for a in tylko_mn}


def test_podaj_wydzial_nom_i_acc():
    # wydział (forma) = nom sg oraz acc sg (synkretyzm)
    krotki = {(a.przypadek, a.liczba) for a in podaj("wydział")}
    assert ("nom", "sg") in krotki
    assert ("acc", "sg") in krotki


def test_podaj_nieznane_puste():
    assert podaj("zzzqwerty") == []


def test_podaj_zwraca_liste():
    assert isinstance(podaj("wydział"), list)
