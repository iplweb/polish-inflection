"""Testy regułowej odmiany przymiotnika (l.poj. i l.mn.), w tym charakteryzacja
progowa przeciw pełnemu SGJP."""

import gzip
from collections import defaultdict
from pathlib import Path

import pytest

from polish_inflection import (
    BIERNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    MĘSKI,
    NARZĘDNIK,
    NIJAKI,
    POJEDYNCZA,
    ŻEŃSKI,
    odmien_przymiotnik,
)

# Podtyp męskoosobowy m1 nie ma publicznej stałej (biblioteka wystawia tylko
# MĘSKI/ŻEŃSKI/NIJAKI) — w teście l.mn. męskoosobowej używamy wprost "m1".
M1 = "m1"

# ── Konkretne przypadki (nazwy instytucji + trzy klasy tematu) ──────────────


@pytest.mark.parametrize(
    "lemat,przypadek,rodzaj,liczba,oczekiwana",
    [
        # welarne -ski/-cki (Lubelski, Lekarski)
        ("lubelski", DOPEŁNIACZ, MĘSKI, POJEDYNCZA, "lubelskiego"),
        ("lubelski", DOPEŁNIACZ, ŻEŃSKI, POJEDYNCZA, "lubelskiej"),
        ("lekarski", DOPEŁNIACZ, MĘSKI, POJEDYNCZA, "lekarskiego"),
        ("lekarski", MIEJSCOWNIK, MĘSKI, POJEDYNCZA, "lekarskim"),
        # twarde -ny/-owy/-any (medyczny, główny, stosowany)
        ("medyczny", DOPEŁNIACZ, MĘSKI, POJEDYNCZA, "medycznego"),
        ("medyczny", MIANOWNIK, ŻEŃSKI, POJEDYNCZA, "medyczna"),
        ("stosowany", DOPEŁNIACZ, ŻEŃSKI, POJEDYNCZA, "stosowanej"),
        ("główny", NARZĘDNIK, NIJAKI, POJEDYNCZA, "głównym"),
        # rodzaj żeński pełny (uczelnia/szkoła/akademia jako głowa)
        ("pedagogiczny", DOPEŁNIACZ, ŻEŃSKI, POJEDYNCZA, "pedagogicznej"),
        ("pedagogiczny", BIERNIK, ŻEŃSKI, POJEDYNCZA, "pedagogiczną"),
        # nijaki (kolegium jako głowa)
        ("techniczny", MIANOWNIK, NIJAKI, POJEDYNCZA, "techniczne"),
        # biernik męski nieżywotny (wydział) = mianownik
        ("lekarski", BIERNIK, MĘSKI, POJEDYNCZA, "lekarski"),
        # l.mn. niemęskoosobowa
        ("medyczny", DOPEŁNIACZ, ŻEŃSKI, MNOGA, "medycznych"),
        ("lubelski", MIEJSCOWNIK, NIJAKI, MNOGA, "lubelskich"),
        # l.mn. męskoosobowa (m1) — alternacje tematu
        ("medyczny", MIANOWNIK, M1, MNOGA, "medyczni"),
        ("lekarski", MIANOWNIK, M1, MNOGA, "lekarscy"),
    ],
)
def test_odmien_przymiotnik_przypadki(lemat, przypadek, rodzaj, liczba, oczekiwana):
    assert odmien_przymiotnik(lemat, przypadek, rodzaj, liczba) == oczekiwana


def test_niepoprawny_lemat_zwraca_default():
    # lemat nie kończący się na -y/-i nie jest przymiotnikiem -> passthrough
    assert odmien_przymiotnik("xyz", DOPEŁNIACZ, MĘSKI) == "xyz"
    assert odmien_przymiotnik("xyz", DOPEŁNIACZ, MĘSKI, default=None) is None


# ── Charakteryzacja progowa przeciw całemu SGJP ─────────────────────────────
# Pełny SGJP jest w git-lfs; w CI bez pobrania LFS zostają wskaźniki (nie gzip).
# Bierzemy tylko realne gzipy (magic 1f 8b) — inaczej test się pomija (skipif).


def _realny_gzip(p: Path) -> bool:
    try:
        with open(p, "rb") as fh:
            return fh.read(2) == b"\x1f\x8b"
    except OSError:
        return False


_SGJP = [
    p
    for p in sorted(
        (Path(__file__).resolve().parents[1] / "data-package" / "sgjp").glob("*.tab.gz")
    )
    if _realny_gzip(p)
]
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
