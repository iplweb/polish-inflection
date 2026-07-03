"""Testy regułowej odmiany przymiotnika (l.poj. i l.mn.), w tym charakteryzacja
progowa przeciw pełnemu SGJP."""

import gzip
from collections import defaultdict
from pathlib import Path

import pytest

from polish_inflection import odmien_przymiotnik

# ── Konkretne przypadki (nazwy instytucji + trzy klasy tematu) ──────────────


@pytest.mark.parametrize(
    "lemat,przypadek,rodzaj,liczba,oczekiwana",
    [
        # welarne -ski/-cki (Lubelski, Lekarski)
        ("lubelski", "gen", "m", "sg", "lubelskiego"),
        ("lubelski", "gen", "f", "sg", "lubelskiej"),
        ("lekarski", "gen", "m", "sg", "lekarskiego"),
        ("lekarski", "loc", "m", "sg", "lekarskim"),
        # twarde -ny/-owy/-any (medyczny, główny, stosowany)
        ("medyczny", "gen", "m", "sg", "medycznego"),
        ("medyczny", "nom", "f", "sg", "medyczna"),
        ("stosowany", "gen", "f", "sg", "stosowanej"),
        ("główny", "inst", "n", "sg", "głównym"),
        # rodzaj żeński pełny (uczelnia/szkoła/akademia jako głowa)
        ("pedagogiczny", "gen", "f", "sg", "pedagogicznej"),
        ("pedagogiczny", "acc", "f", "sg", "pedagogiczną"),
        # nijaki (kolegium jako głowa)
        ("techniczny", "nom", "n", "sg", "techniczne"),
        # biernik męski nieżywotny (wydział = m3) = mianownik
        ("lekarski", "acc", "m", "sg", "lekarski"),
        # l.mn. niemęskoosobowa
        ("medyczny", "gen", "f", "pl", "medycznych"),
        ("lubelski", "loc", "n", "pl", "lubelskich"),
        # l.mn. męskoosobowa (m1) — alternacje tematu
        ("medyczny", "nom", "m1", "pl", "medyczni"),
        ("lekarski", "nom", "m1", "pl", "lekarscy"),
    ],
)
def test_odmien_przymiotnik_przypadki(lemat, przypadek, rodzaj, liczba, oczekiwana):
    assert odmien_przymiotnik(lemat, przypadek, rodzaj, liczba) == oczekiwana


def test_niepoprawny_lemat_zwraca_default():
    # lemat nie kończący się na -y/-i nie jest przymiotnikiem -> passthrough
    assert odmien_przymiotnik("xyz", "gen", "m") == "xyz"
    assert odmien_przymiotnik("xyz", "gen", "m", default=None) is None


# ── Charakteryzacja progowa przeciw całemu SGJP ─────────────────────────────

_SGJP = sorted((Path(__file__).resolve().parents[1] / "data" / "sgjp").glob("*.tab.gz"))
_PRZ = {"nom", "gen", "dat", "acc", "inst", "loc", "voc"}
_RODZ = {"m1", "m2", "m3", "f", "n"}


def _zbierz_gold(liczba_filtr):
    gold = defaultdict(set)
    with gzip.open(_SGJP[-1], "rt", encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            forma, lemat, tag = p[0], p[1], p[2]
            parts = tag.split(":")
            if len(parts) < 5 or parts[0] != "adj" or parts[4] != "pos":
                continue
            if parts[1] != liczba_filtr:
                continue
            bare = lemat.split(":", 1)[0]
            for przyp in parts[2].split("."):
                if przyp in _PRZ:
                    for rodz in parts[3].split("."):
                        if rodz in _RODZ:
                            gold[(bare, przyp, rodz)].add(forma)
    return gold


def _trafnosc(liczba):
    gold = _zbierz_gold(liczba)
    ok = tot = 0
    for (lemat, przyp, rodz), formy in gold.items():
        tot += 1
        if odmien_przymiotnik(lemat, przyp, rodz, liczba) in formy:
            ok += 1
    return ok / tot, tot


@pytest.mark.skipif(not _SGJP, reason="brak vendorowanego SGJP")
def test_charakteryzacja_liczba_pojedyncza():
    traf, tot = _trafnosc("sg")
    assert tot > 2_000_000  # sanity: pełny korpus
    assert traf >= 0.999, f"l.poj. trafność {traf:.4%} < 99.9%"


@pytest.mark.skipif(not _SGJP, reason="brak vendorowanego SGJP")
def test_charakteryzacja_liczba_mnoga():
    traf, _ = _trafnosc("pl")
    assert traf >= 0.996, f"l.mn. trafność {traf:.4%} < 99.6%"
