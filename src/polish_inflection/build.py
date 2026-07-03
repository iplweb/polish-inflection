"""Pipeline BUILD (offline): SGJP ``.tab`` -> dwa indeksy marisa-trie (``BytesTrie``).

Uruchamiany u autora / w CI, NIGDY przy ``pip install``. Buduje kompaktowy,
w pełni wyliczony indeks — runtime niczego nie generuje, tylko wyszukuje.

Zapis indeksów robi ``marisa-trie`` (zależność runtime). Extra ``build`` dokłada
tylko ``requests`` do ``refresh_sgjp``; sam build indeksów go nie potrzebuje.

Schemat wyjścia — patrz CONTRACT §D / :mod:`polish_inflection.core`.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

from .const import LICZBY_SET, PRZYPADKI_SET

# ── Model rekordu po ekspansji ─────────────────────────────────────────────


class Rekord(NamedTuple):
    forma: str
    lemat: str  # goły lemat (bez sufiksu fleksemu)
    liczba: str  # "sg"/"pl"
    przypadek: str  # "nom".."voc"
    rodzaj: str  # "m1","f","n",...
    depr: bool  # True dla form deprecjatywnych (tag depr:)


# ── Parsowanie + EKSPANSJA tagu SGJP ───────────────────────────────────────


def goly_lemat(lemat: str) -> str:
    """Utnij sufiks fleksemu/homonimu: ``profesor:Sm1`` -> ``profesor``."""
    return lemat.split(":", 1)[0]


def parsuj_linie(linie: Iterable[str]) -> Iterator[Rekord]:
    """Parsuj i ROZWIŃ linie SGJP ``.tab`` na pojedyncze rekordy.

    Tag NIE jest 1:1: pola ``liczby`` i ``przypadki`` to kropkowo sklejone
    podzbiory (``subst:sg:nom.acc:m3`` -> dwa rekordy). Pomija nagłówki (``#``),
    tagi inne niż ``subst``/``depr`` oraz wpisy niekompletne/nietypowe.
    """
    for linia in linie:
        linia = linia.rstrip("\n")
        if not linia or linia.startswith("#"):
            continue
        pola = linia.split("\t")
        if len(pola) < 3:
            continue
        forma, lemat, tag = pola[0], pola[1], pola[2]
        if not forma or not tag:
            continue

        czesci = tag.split(":")
        pos = czesci[0]
        if pos not in ("subst", "depr"):
            continue
        if len(czesci) < 4:
            continue

        depr = pos == "depr"
        bare = goly_lemat(lemat)
        liczby = czesci[1].split(".")
        przypadki = czesci[2].split(".")
        rodzaj = czesci[3].split(".")[0]  # rodzaj bywa kropkowany — bierz główny

        for liczba in liczby:
            if liczba not in LICZBY_SET:
                continue
            for przypadek in przypadki:
                if przypadek not in PRZYPADKI_SET:
                    continue
                yield Rekord(forma, bare, liczba, przypadek, rodzaj, depr)


# ── Budowa indeksów (marisa-trie BytesTrie) ────────────────────────────────


def _pary_indeksow(rekordy: Iterable[Rekord]):
    """Zwróć (pary_odmien, pary_podaj) jako listy (klucz:str, wartosc:bytes).

    odmien: tylko subst (formy główne). podaj: subst + depr.
    Deduplikacja identycznych par.
    """
    odmien_set: set[tuple[str, bytes]] = set()
    podaj_set: set[tuple[str, bytes]] = set()
    for r in rekordy:
        wart_podaj = f"{r.lemat}\t{r.przypadek}\t{r.liczba}\t{r.rodzaj}".encode()
        podaj_set.add((r.forma, wart_podaj))
        if not r.depr:
            klucz = f"{r.lemat}\t{r.przypadek}\t{r.liczba}"
            odmien_set.add((klucz, r.forma.encode("utf-8")))
    return sorted(odmien_set), sorted(podaj_set)


def zbuduj_indeksy(rekordy: Iterable[Rekord]):
    """Zbuduj i zwróć oba ``marisa_trie.BytesTrie`` (odmien, podaj)."""
    import marisa_trie

    pary_odmien, pary_podaj = _pary_indeksow(rekordy)
    return marisa_trie.BytesTrie(pary_odmien), marisa_trie.BytesTrie(pary_podaj)


# ── Czytanie źródła ────────────────────────────────────────────────────────


def _otworz_tab(sciezka: Path) -> Iterator[str]:
    """Otwórz ``.tab`` lub ``.tab.gz`` jako strumień linii (utf-8)."""
    if sciezka.suffix == ".gz":
        with gzip.open(sciezka, "rt", encoding="utf-8") as f:
            yield from f
    else:
        with open(sciezka, encoding="utf-8") as f:
            yield from f


_DICT_ID_RE = re.compile(r"#!DICT-ID\s+(\S+)")


def _linie_naglowka(linie: Iterable[str]) -> Iterator[str]:
    """Wydziel linie nagłówka SGJP (do pierwszej linii danych).

    UWAGA: treść bloku ``#<COPYRIGHT> ... #</COPYRIGHT>`` to zwykłe linie BEZ
    prefiksu ``#`` — więc nie wolno przerywać na pierwszej linii bez ``#``;
    czytamy dopóki jesteśmy wewnątrz bloku licencji. Wspólne dla ``wersja_sgjp``
    i ``refresh_sgjp`` (jeden kontrakt na kształt nagłówka).
    """
    wewnatrz_licencji = False
    for linia in linie:
        s = linia.rstrip("\n")
        if not wewnatrz_licencji and not s.startswith("#"):
            break
        yield linia
        if s.startswith("#<COPYRIGHT>"):
            wewnatrz_licencji = True
        elif s.startswith("#</COPYRIGHT>"):
            wewnatrz_licencji = False


def wersja_sgjp(sciezka: Path) -> str | None:
    """Odczytaj wersję z nagłówka ``#!DICT-ID pl.sgjp.sgjp-YYYY.MM.DD``."""
    for linia in _linie_naglowka(_otworz_tab(sciezka)):
        m = _DICT_ID_RE.search(linia)
        if m:
            return m.group(1)
    return None


# ── Pełny bieg buildu ──────────────────────────────────────────────────────


def zbuduj_z_tab(sciezka_tab: Path, out_dir: Path, *, data_build: str | None = None) -> dict:
    """Zbuduj ``odmien.marisa``/``podaj.marisa`` + ``BUILD_INFO.json`` w ``out_dir``.

    Zwraca słownik BUILD_INFO. ``data_build`` przekazuje wywołujący (brak zegara
    w bibliotece); ``None`` -> pole pominięte.
    """
    sciezka_tab = Path(sciezka_tab)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rekordy = list(parsuj_linie(_otworz_tab(sciezka_tab)))
    odmien_trie, podaj_trie = zbuduj_indeksy(rekordy)

    odmien_path = out_dir / "odmien.marisa"
    podaj_path = out_dir / "podaj.marisa"
    odmien_trie.save(str(odmien_path))
    podaj_trie.save(str(podaj_path))

    lematy = {r.lemat for r in rekordy}
    formy = {(r.forma, r.lemat, r.liczba, r.przypadek) for r in rekordy}
    info = {
        "wersja_sgjp": wersja_sgjp(sciezka_tab),
        "data_build": data_build,
        "liczba_lematow": len(lematy),
        "liczba_form": len(formy),
        "liczba_rekordow": len(rekordy),
        "rozmiar_odmien_marisa": odmien_path.stat().st_size,
        "rozmiar_podaj_marisa": podaj_path.stat().st_size,
    }
    (out_dir / "BUILD_INFO.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return info


# ── refresh-sgjp (jedyne miejsce sięgające do sieci) ───────────────────────

_BAZA_URL = "https://download.sgjp.pl/morfeusz"
_KATALOG_RE = re.compile(r'href="(\d{8})/"')


def _najnowsza_wersja(sesja) -> str:
    """Znajdź najnowszy katalog dat (``YYYYMMDD``) w indeksie SGJP."""
    r = sesja.get(f"{_BAZA_URL}/", timeout=60)
    r.raise_for_status()
    daty = sorted(set(_KATALOG_RE.findall(r.text)))
    if not daty:
        raise RuntimeError("Nie znaleziono katalogów wersji SGJP.")
    return daty[-1]


def _wytnij_licencje(naglowek: str) -> str | None:
    """Wytnij blok ``#<COPYRIGHT> ... #</COPYRIGHT>`` (verbatim) z nagłówka."""
    linie = []
    zapisuj = False
    for linia in naglowek.splitlines():
        if linia.startswith("#<COPYRIGHT>"):
            zapisuj = True
            continue
        if linia.startswith("#</COPYRIGHT>"):
            break
        if zapisuj:
            linie.append(linia)
    return "\n".join(linie).strip() + "\n" if linie else None


def refresh_sgjp(dane_dir: Path, *, wersja: str | None = None, data_pobrania: str | None = None):
    """Pobierz najnowszy (lub wskazany) SGJP ``.tab.gz``, zwendoruj, zaktualizuj pin.

    Zapisuje ``sgjp-<wersja>.tab.gz``, ``PIN.json`` i ``LICENSE.sgjp``.
    """
    import requests

    dane_dir = Path(dane_dir)
    dane_dir.mkdir(parents=True, exist_ok=True)
    sesja = requests.Session()

    if wersja is None:
        wersja = _najnowsza_wersja(sesja)
    url = f"{_BAZA_URL}/{wersja}/sgjp-{wersja}.tab.gz"

    print(f"Pobieram {url} ...", file=sys.stderr)
    r = sesja.get(url, timeout=600)
    r.raise_for_status()
    dane = r.content
    sha256 = hashlib.sha256(dane).hexdigest()

    plik = dane_dir / f"sgjp-{wersja}.tab.gz"
    plik.write_bytes(dane)

    # Nagłówek do wersji i licencji — wspólny iterator respektuje blok licencji.
    with gzip.open(io.BytesIO(dane), "rt", encoding="utf-8") as f:
        naglowek = "".join(_linie_naglowka(f))
    m = _DICT_ID_RE.search(naglowek)
    dict_id = m.group(1) if m else None

    licencja = _wytnij_licencje(naglowek)
    if licencja:
        (dane_dir / "LICENSE.sgjp").write_text(licencja, encoding="utf-8")

    pin = {
        "wersja": wersja,
        "dict_id": dict_id,
        "data_pobrania": data_pobrania,
        "sha256": sha256,
        "url_zrodlowy": url,
        "plik": plik.name,
    }
    (dane_dir / "PIN.json").write_text(
        json.dumps(pin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Zapisano {plik.name} (sha256={sha256[:12]}…), zaktualizowano PIN.json", file=sys.stderr)
    return pin


# ── CLI ────────────────────────────────────────────────────────────────────


def _domyslny_pin_tab(dane_dir: Path) -> Path:
    """Znajdź vendorowany ``.tab.gz`` wg ``PIN.json`` (lub jedyny w katalogu)."""
    pin_path = dane_dir / "PIN.json"
    if pin_path.exists():
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
        nazwa = pin.get("plik")
        if nazwa and (dane_dir / nazwa).exists():
            return dane_dir / nazwa
    kandydaci = sorted(dane_dir.glob("*.tab.gz"))
    if not kandydaci:
        raise SystemExit(f"Brak vendorowanego SGJP w {dane_dir}. Uruchom `refresh-sgjp`.")
    return kandydaci[-1]


def main(argv: list[str] | None = None) -> int:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="polish-inflection-build")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Zbuduj indeksy z vendorowanego pinu (bez sieci).")
    p_build.add_argument("--tab", type=Path, default=None, help="Ścieżka do .tab/.tab.gz")
    p_build.add_argument("--out", type=Path, default=repo / "src" / "polish_inflection" / "data")
    p_build.add_argument("--data-build", default=None, help="Data buildu (do BUILD_INFO).")

    p_refresh = sub.add_parser("refresh-sgjp", help="Pobierz najnowszy SGJP i zaktualizuj pin.")
    p_refresh.add_argument("--wersja", default=None, help="Konkretna wersja YYYYMMDD.")
    p_refresh.add_argument("--data-pobrania", default=None)
    p_refresh.add_argument("--dane-dir", type=Path, default=repo / "data" / "sgjp")

    args = parser.parse_args(argv)

    if args.cmd == "build":
        tab = args.tab or _domyslny_pin_tab(repo / "data" / "sgjp")
        info = zbuduj_z_tab(tab, args.out, data_build=args.data_build)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "refresh-sgjp":
        refresh_sgjp(args.dane_dir, wersja=args.wersja, data_pobrania=args.data_pobrania)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
