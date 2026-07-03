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


# ── główna forma przy homografie rodzajów ───────────────────────────────────


def test_odmien_homograf_preferuje_odmieniona():
    # 'profesor' = m1 (odmienny: profesora/profesorów) + f (nieodmienny: profesor);
    # główną formą ma być odmieniona m1, nie tożsamościowe 'profesor'
    assert odmien("profesor", DOPEŁNIACZ) == "profesora"
    assert odmien("profesor", DOPEŁNIACZ, MNOGA) == "profesorów"


def test_odmien_mianownik_nadal_lemat():
    # gdy jedyną formą jest lemat (mianownik l.poj.), zwracamy ją
    assert odmien("profesor", MIANOWNIK) == "profesor"
    assert odmien("wydział", MIANOWNIK) == "wydział"


# ── wymuszony rodzaj (odmien rodzaj=) ───────────────────────────────────────


def test_odmien_wymuszony_rodzaj_meski_i_zenski():
    from polish_inflection import MĘSKI, ŻEŃSKI

    assert odmien("profesor", DOPEŁNIACZ, rodzaj=MĘSKI) == "profesora"
    assert odmien("profesor", DOPEŁNIACZ, MNOGA, rodzaj=MĘSKI) == "profesorów"
    assert odmien("profesor", DOPEŁNIACZ, rodzaj=ŻEŃSKI) == "profesor"


def test_odmien_wymuszony_rodzaj_brak_to_default():
    from polish_inflection import ŻEŃSKI

    # 'wydział' nie ma formy żeńskiej -> jak brak formy
    assert odmien("wydział", DOPEŁNIACZ, rodzaj=ŻEŃSKI, default=None) is None


def test_podaj_rodzaj_jest_publiczny():
    # rodzaj w Analiza to m/f/n, NIE m1/m2/m3
    rodzaje = {a.rodzaj for a in podaj("student")}
    assert rodzaje == {"m"}
    assert "m1" not in rodzaje


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
