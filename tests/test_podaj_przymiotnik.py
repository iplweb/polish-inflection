"""Testy leksykalnego rozpoznawania przymiotników (kierunek zwrotny: forma → lemat).

``podaj_przymiotnik`` to odwrotność ``odmien_przymiotnik`` (generate-and-test na
zamkniętym paradygmacie), ale LEKSYKALNA: kandydaci na bazę są filtrowani zbiorem
prawdziwych baz deklinacyjnych z SGJP (``przymiotniki.marisa``), więc formy które
tylko wyglądają jak przymiotnik (np. rzeczownik ``dupa``/``Michała``) dają ``[]``.
Charakteryzacja progowa mierzy RECALL przeciw SGJP (czy dla złotej formy
odzyskujemy poprawną analizę). Wymaga zainstalowanego ``polish-inflection-data``.
"""

import gzip
from collections import defaultdict
from pathlib import Path

import pytest

from polish_inflection import (
    BIERNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MNOGA,
    MĘSKI,
    NIJAKI,
    POJEDYNCZA,
    ŻEŃSKI,
    Analiza,
    podaj_przymiotnik,
)


def _zawiera(forma, lemat, przypadek, liczba, rodzaj):
    return Analiza(lemat, przypadek, liczba, rodzaj) in podaj_przymiotnik(forma)


@pytest.mark.parametrize(
    "forma,lemat,przypadek,liczba,rodzaj",
    [
        # żeński mianownik (kanoniczny przypadek "wołowa" → "wołowy")
        ("wołowa", "wołowy", MIANOWNIK, POJEDYNCZA, ŻEŃSKI),
        ("medyczna", "medyczny", MIANOWNIK, POJEDYNCZA, ŻEŃSKI),
        ("lubelska", "lubelski", MIANOWNIK, POJEDYNCZA, ŻEŃSKI),
        # męski mianownik l.poj. (forma słownikowa)
        ("lubelski", "lubelski", MIANOWNIK, POJEDYNCZA, MĘSKI),
        ("medyczny", "medyczny", MIANOWNIK, POJEDYNCZA, MĘSKI),
        # dopełniacz męski/nijaki (synkretyzm -ego)
        ("lekarskiego", "lekarski", DOPEŁNIACZ, POJEDYNCZA, MĘSKI),
        ("lekarskiego", "lekarski", DOPEŁNIACZ, POJEDYNCZA, NIJAKI),
        # żeński dopełniacz -ej
        ("stosowanej", "stosowany", DOPEŁNIACZ, POJEDYNCZA, ŻEŃSKI),
        # nijaki mianownik -e
        ("techniczne", "techniczny", MIANOWNIK, POJEDYNCZA, NIJAKI),
        # l.mn. niemęskoosobowa -ych
        ("medycznych", "medyczny", DOPEŁNIACZ, MNOGA, ŻEŃSKI),
        # l.mn. męskoosobowa (alternacja tematu sk→sc): lekarscy → lekarski
        ("lekarscy", "lekarski", MIANOWNIK, MNOGA, MĘSKI),
        ("medyczni", "medyczny", MIANOWNIK, MNOGA, MĘSKI),
    ],
)
def test_rozpoznaje(forma, lemat, przypadek, liczba, rodzaj):
    assert _zawiera(forma, lemat, przypadek, liczba, rodzaj)


def test_niewrazliwe_na_wielkosc_liter():
    # proper-noun-owa kapitalizacja nie przeszkadza; lemat zawsze małą literą
    assert _zawiera("Lubelskiego", "lubelski", DOPEŁNIACZ, POJEDYNCZA, MĘSKI)
    assert _zawiera("WOŁOWA", "wołowy", MIANOWNIK, POJEDYNCZA, ŻEŃSKI)


def test_forma_bez_ksztaltu_przymiotnika_pusta():
    # nie kończy się jak żadna forma przymiotnika w paradygmacie
    assert podaj_przymiotnik("xyz") == []
    assert podaj_przymiotnik("") == []


def test_biernik_zenski_a():
    assert _zawiera("medyczną", "medyczny", BIERNIK, POJEDYNCZA, ŻEŃSKI)


# ── Ugruntowanie leksykalne: koniec „Michała → michały" ─────────────────────


@pytest.mark.parametrize("forma", ["Michała", "michała", "dupa", "kobieta", "jednostki"])
def test_forma_rzeczownika_nie_jest_przymiotnikiem(forma):
    # bazy 'michały'/'dupy'/'kobiety'/'jednostki' NIE istnieją w SGJP jako
    # przymiotniki → filtr leksykalny odrzuca (regułowy recognizer by je nadgenerował)
    assert podaj_przymiotnik(forma) == []


def test_imieslow_bierny_jest_rozpoznawany():
    # ppas 'zjednoczony' jest w zbiorze baz (dlatego adj+pact+ppas, nie samo adj)
    assert _zawiera("zjednoczona", "zjednoczony", MIANOWNIK, POJEDYNCZA, ŻEŃSKI)


def test_stopien_wyzszy_jest_baza():
    # 'wyższy' (stopień wyższy od 'wysoki') to baza deklinacji — kluczowe dla frazy
    assert _zawiera("wyższa", "wyższy", MIANOWNIK, POJEDYNCZA, ŻEŃSKI)


# ── Charakteryzacja progowa (RECALL) przeciw SGJP ───────────────────────────
# Dla każdej złotej (forma, lemat, przyp, rodz) sprawdzamy, czy
# podaj_przymiotnik(forma) zawiera analizę o publicznym rodzaju. Recognizer jest
# DROGI per-forma (generate-and-test), więc charakteryzujemy na deterministycznym
# SAMPLU (co N-ta unikalna forma) — reprezentatywnym, ale wykonalnym w sekundy.

_SAMPLE = 6000

_PRZ = {"nom", "gen", "dat", "acc", "inst", "loc", "voc"}
_RODZ = {"m1", "m2", "m3", "f", "n"}


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


def _publiczny(rodz: str) -> str:
    return rodz[:1]  # m1/m2/m3 -> m, f -> f, n -> n


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
                            gold[(forma, bare, przyp, _publiczny(rodz))].add(True)
    return gold


def _recall(liczba):
    # deterministyczny sample: posortuj klucze i weź co (n/_SAMPLE)-ty
    klucze = sorted(_zbierz_gold(liczba))
    krok = max(1, len(klucze) // _SAMPLE)
    probka = klucze[::krok]
    ok = 0
    cache = {}
    for forma, lemat, przyp, rodz_pub in probka:
        if forma not in cache:
            cache[forma] = {(a.lemat, a.przypadek, a.rodzaj) for a in podaj_przymiotnik(forma)}
        if (lemat, przyp, rodz_pub) in cache[forma]:
            ok += 1
    return ok / len(probka), len(klucze)


@pytest.mark.skipif(not _SGJP, reason="brak vendorowanego SGJP")
def test_recall_liczba_pojedyncza():
    # Reszta (~0,4%) to klasy poza regułowym paradygmatem: nieodmienne zapożyczenia
    # (extra, wideo, offline), skrótowce z wielkoliterowym lematem (AK-owski) oraz
    # zaimkowe archaizmy (wszystek, ów). Produktywne przymiotniki: praktycznie 100%.
    traf, tot = _recall("sg")
    assert tot > 1_000_000  # sanity: pełny korpus adj l.poj.
    assert traf >= 0.996, f"recall l.poj. {traf:.4%} < 99.6%"


@pytest.mark.skipif(not _SGJP, reason="brak vendorowanego SGJP")
def test_recall_liczba_mnoga():
    traf, _ = _recall("pl")
    assert traf >= 0.99, f"recall l.mn. {traf:.4%} < 99%"
