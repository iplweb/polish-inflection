# Split `polish-inflection`: kod + dane rzeczowników + dane przymiotników

**Data:** 2026-07-03
**Status:** projekt zaakceptowany (do przejścia w plan implementacji)

## Problem

1. Zbudowane indeksy SGJP (`odmien.marisa` ≈ 24 MB, `podaj.marisa` ≈ 25 MB) jadą
   w wheelu `polish-inflection`, więc **każde wydanie kodu re-publikuje ~49 MB**
   słownika — choć dane zmieniają się rzadko, a kod często.
2. Rozpoznawanie przymiotników (`zgadnij_przymiotnik`) jest **regułowe bez oparcia
   w leksykonie** → nadgeneruje: dla `"Michała"` (forma rzeczownika `Michał`)
   proponuje nieistniejący przymiotnik `michały`. To realny defekt jakości.

## Cel

Trzy pakiety PyPI o niezależnych cyklach wydań:

- **`polish-inflection`** — sam kod. Wheel odchudzony do ~kilkudziesięciu KB.
- **`polish-inflection-data-nouns`** — indeksy rzeczowników (`odmien.marisa` +
  `podaj.marisa`), ~49 MB. Wersjonowane wg edycji SGJP.
- **`polish-inflection-data-adjectives`** — zbiór **baz deklinacyjnych**
  przymiotników (0,25 MB). Grunt leksykalny dla rozpoznawania — koniec `michały`.

Baza `polish-inflection` **twardo wymaga OBU** pakietów danych. UX bez regresji:
`pip install polish-inflection` ciągnie komplet.

## Decyzje (brainstorming)

| Decyzja | Wybór |
|---|---|
| Mechanizm danych | Osobne pakiety importowalne (`polish_inflection_data_nouns`, `…_adjectives`) |
| Struktura repo | Monorepo; korzeń = kod, `data-package-nouns/`, `data-package-adjectives/` |
| Wersjonowanie danych | Kalendarzowe `YYYY.M.D` z daty SGJP; `.postN` przy zmianie schematu |
| Zależność kodu | Twarda, dolny pin na OBA pakiety danych |
| Zgodność `.marisa` | Strażnik schematu (`SCHEMA` per pakiet danych) |
| Rozpoznawanie przymiotnika | **Leksykalne**: reguły (generate-and-test) filtrowane zbiorem baz |
| Nazwa funkcji | `zgadnij_przymiotnik` → **`podaj_przymiotnik`** (już nie zgaduje) |
| Zakres tej rundy | Spec + plan; implementacja i wydania osobno |

## Kluczowa idea: grunt leksykalny bez indeksu form

Fałszywe pozytywy (`Michała → michały`) biorą się z braku leksykonu, nie z reguł
(reguły mają recall 99,6%). Nie trzymamy **wszystkich form** przymiotników (742k,
~10–20 MB pełnego reverse indeksu). Trzymamy tylko **zbiór baz deklinacyjnych** =
mianownik l.poj. rodzaju męskiego, **wszystkich stopni** (pos/com/sup):

- Zmierzone na SGJP 20260628: **70 250 baz → 0,25 MB** marisa `Trie`.
- To dokładnie to, co silnik reguł nazywa „lematem" (forma słownikowa `-y/-i`,
  od której odmienia). Musi obejmować stopnie wyższe/najwyższe, bo np. „Wyższa
  Szkoła" ma bazę `wyższy` (stopień wyższy od `wysoki` — NIE `adj:pos` w SGJP).

Weryfikacja członkostwa (SGJP 20260628):

| baza | w zbiorze | skutek |
|---|---|---|
| `wyższy`, `najwyższy`, `wysoki` | ✓ | „Wyższa Szkoła" działa |
| `lubelski`, `medyczny`, `wołowy`, `lekarski`, `główny` | ✓ | nazwy instytucji działają |
| `michały`, `dupy` | ✗ | false-positives wyeliminowane |

`podaj_przymiotnik(forma)`: reguły generują kandydatów na bazę → **odrzuć te spoza
zbioru** → dla pozostałych zweryfikuj generacją, że `forma` faktycznie z nich
wynika. Ugruntowane w słowniku, silnik reguł (forward) zostaje bez zmian.

## Architektura

### Układ repo (monorepo, korzeń = kod)

```
polish-inflection/                      # repo iplweb/polish-inflection
├── pyproject.toml                      # PAKIET KODU (name="polish-inflection")
├── src/polish_inflection/
│   ├── core.py                         #   locator rzeczowników + strażnik schematu
│   ├── przymiotnik.py                  #   podaj_przymiotnik: reguły + filtr zbioru baz
│   ├── _dane.py                        #   NOWY: wspólne locatory obu pakietów danych
│   ├── build.py                        #   buduje indeksy rzeczowników I zbiór baz adj
│   └── … (bez zmian)
├── tests/
├── data-package-nouns/
│   ├── pyproject.toml                  #   name="polish-inflection-data-nouns", ver=YYYY.M.D
│   ├── src/polish_inflection_data_nouns/
│   │   ├── __init__.py                 #   KATALOG, SCHEMA, WERSJA_SGJP
│   │   └── data/  odmien.marisa, podaj.marisa, BUILD_INFO.json
│   └── sgjp/  sgjp-YYYYMMDD.tab.gz, PIN.json, LICENSE.sgjp   # surowy SGJP (git-lfs)
├── data-package-adjectives/
│   ├── pyproject.toml                  #   name="polish-inflection-data-adjectives", ver=YYYY.M.D
│   └── src/polish_inflection_data_adjectives/
│       ├── __init__.py                 #   KATALOG, SCHEMA, WERSJA_SGJP
│       └── data/  przymiotniki.marisa, BUILD_INFO.json
└── docs/, LICENSE, NOTICE.md, …
```

Surowy SGJP (`.tab.gz`) leży w `data-package-nouns/sgjp/` (jedno źródło; oba buildy
czytają ten sam plik). Testy charakteryzacyjne czytają go stamtąd.

### Pakiety danych

Każdy zawiera tylko artefakty + cienki `__init__.py` (zero logiki):

```python
# polish_inflection_data_nouns / _adjectives — __init__.py
from importlib.resources import files
from pathlib import Path
import json

SCHEMA = 1                                   # wersja formatu artefaktów tego pakietu
KATALOG = Path(str(files(__name__) / "data"))
WERSJA_SGJP = json.loads((KATALOG / "BUILD_INFO.json").read_text("utf-8")).get("wersja_sgjp")
```

- `polish-inflection-data-nouns`: `odmien.marisa` + `podaj.marisa` + `BUILD_INFO.json`.
- `polish-inflection-data-adjectives`: `przymiotniki.marisa` (marisa `Trie` baz,
  bez wartości) + `BUILD_INFO.json`.
- Wersja obu = kalendarzowa z daty SGJP (`20260628` → `2026.6.28`); `.postN` przy
  zmianie schematu bez zmiany SGJP.

### Kod: `_dane.py` (wspólne locatory)

```python
_SCHEMA_NOUNS = 1
_SCHEMA_ADJ = 1

def katalog_nouns() -> Path:
    return _zaladuj("polish_inflection_data_nouns", _SCHEMA_NOUNS, "polish-inflection-data-nouns")

def katalog_adjectives() -> Path:
    return _zaladuj("polish_inflection_data_adjectives", _SCHEMA_ADJ, "polish-inflection-data-adjectives")

def _zaladuj(modul: str, oczekiwany: int, dist: str) -> Path:
    try:
        dane = importlib.import_module(modul)
    except ModuleNotFoundError as e:
        raise RuntimeError(f"Brak pakietu danych. Zainstaluj: pip install {dist}") from e
    if dane.SCHEMA != oczekiwany:
        raise RuntimeError(
            f"Niezgodny schemat {dist}: kod oczekuje {oczekiwany}, pakiet ma {dane.SCHEMA}."
        )
    return dane.KATALOG
```

- `core.py`: `_domyslny_katalog_danych()` → `katalog_nouns()`. `_ustaw_katalog_danych`
  (hook testowy rzeczowników) bez zmian.
- `przymiotnik.py`: leniwie ładuje `przymiotniki.marisa` z `katalog_adjectives()`,
  cache modułowy (mmap), z hookiem testowym analogicznym do rzeczowników.
- Strażniki schematu leniwe — sam `import polish_inflection` nie ładuje danych.
- Zależności kodu: `["marisa-trie>=1.0", "polish-inflection-data-nouns>=2026.6.28",
  "polish-inflection-data-adjectives>=2026.6.28"]`.

### `podaj_przymiotnik` — ugruntowanie

```python
def podaj_przymiotnik(forma):
    f = forma.lower()
    bazy = _zbior_baz()                       # marisa Trie z pakietu adjectives (mmap)
    wynik = set()
    for lemat in _kandydaci_lematow(f):
        if lemat not in bazy:                 # NOWE: filtr leksykalny — koniec 'michały'
            continue
        # dalej jak dziś: weryfikacja generacją po wszystkich slotach
        ...
    return sorted(wynik, ...)
```

Rename `zgadnij_przymiotnik` → `podaj_przymiotnik` (symetria z `podaj`; już nie
zgaduje). Docstring: leksykalne, nie regułowe zgadywanie. `podaj` (rzeczowniki) i
`podaj_przymiotnik` (przymiotniki) pozostają rozdzielone.

### Build (`build.py`)

- Rzeczowniki: bez zmian (`odmien.marisa` + `podaj.marisa`) → `--out
  data-package-nouns/src/polish_inflection_data_nouns/data`.
- Przymiotniki: NOWA ścieżka — wyodrębnij bazy deklinacyjne (`adj`, `sg`, `nom`,
  rodzaj `m1|m2|m3`, dowolny stopień), zbuduj `marisa_trie.Trie` (lowercase),
  zapisz `przymiotniki.marisa` → `data-package-adjectives/.../data`.
- Do `BUILD_INFO.json` obu artefaktów trafia `wersja_sgjp` i `schema`.
- CLI: `build` buduje oba; opcje `--out-nouns` / `--out-adjectives`.

## Przepływ danych (runtime)

```
odmien("wydział", …)  → _dane.katalog_nouns() → mmap odmien.marisa
podaj("jednostki")    → _dane.katalog_nouns() → mmap podaj.marisa
podaj_przymiotnik("wołowa")
   → _dane.katalog_adjectives() → mmap przymiotniki.marisa (zbiór baz)
   → reguły generują kandydatów, filtr `in bazy`, weryfikacja generacją
```

## Obsługa błędów

| Sytuacja | Zachowanie |
|---|---|
| Brak pakietu danych (nouns/adjectives) | `RuntimeError` z instrukcją `pip install <dist>` |
| Niezgodny `SCHEMA` | `RuntimeError` (oczekiwany vs faktyczny, którego pakietu) |
| `BUILD_INFO["schema"]` ≠ `SCHEMA` pakietu | Test pakietu danych (nie runtime) |
| `import polish_inflection` bez użycia danych | Działa (locatory leniwe) |

## Testy

- Logika kodu bez zmian (poza filtrem baz); testy integracyjne wymagają obu
  pakietów danych zainstalowanych (editable w dev).
- **`podaj_przymiotnik` — nowe testy leksykalne:** `"Michała"`/`"dupa"` → `[]`
  (bazy `michały`/`dupy` spoza zbioru); `"wołowa"`→`wołowy`, `"Wyższa"`→`wyższy`
  (bazy w zbiorze). Rename pokryty (import `podaj_przymiotnik`).
- **Recall** (charakteryzacja) po ugruntowaniu: ≥ dotychczasowego, false-positives
  spadają. Sample jak dziś.
- **Testy pakietów danych:** `SCHEMA == BUILD_INFO["schema"]`; `WERSJA_SGJP`
  niepuste; artefakty istnieją i otwierają się przez marisa; zbiór baz zawiera
  próbkę (`lubelski`, `wyższy`) i nie zawiera (`michały`).
- Fraza: `KORPUS`/`KORPUS_MNOGA` bez regresji (wszystkie przymiotniki instytucji
  są w zbiorze baz — zweryfikowane).

## Migracja (kolejność bezpieczna)

1. Utwórz oba `data-package-*/`; przenieś `data/sgjp/` → `data-package-nouns/sgjp/`.
2. Rozszerz `build.py` o zbiór baz; zbuduj artefakty do obu pakietów; ustaw
   `version=2026.6.28`, `SCHEMA=1` w obu.
3. **Opublikuj `polish-inflection-data-nouns 2026.6.28` i
   `polish-inflection-data-adjectives 2026.6.28`** (przed kodem — inaczej pin się
   nie zresolvuje).
4. Usuń `.marisa` z pakietu kodu; dodaj `_dane.py` + strażniki; przełącz `core` i
   `przymiotnik`; rename `zgadnij_przymiotnik`→`podaj_przymiotnik`; dodaj zależności;
   hatchling przestaje pakować `.marisa`.
5. Zaktualizuj testy (ścieżka SGJP, filtr baz), CI (job kodu + oba data-buildy),
   README/`docs/api.md`/CHANGELOG.
6. **Wydaj `polish-inflection 0.7.0`** — wheel bez `.marisa`; breaking: rename
   `zgadnij_przymiotnik`→`podaj_przymiotnik` + wymóg pakietów danych (alpha, OK).

## Poza zakresem (YAGNI)

- Pełny reverse index form przymiotników (~10–20 MB) — odrzucony: zbiór baz 0,25 MB
  rozwiązuje realny problem (false-positives) ~50–100× taniej.
- Scalanie `podaj` + `podaj_przymiotnik` w jedno — nie reotwierane.
- Wariant opcjonalnej zależności (`extra [data]`), układ `packages/` — odrzucone.

## Kryteria sukcesu

- `pip install polish-inflection` ciągnie kod + oba pakiety danych; API i wyniki
  jak w 0.6.0 poza celowym rename i lepszym rozpoznawaniem przymiotników.
- Wheel `polish-inflection` bez `.marisa`.
- `podaj_przymiotnik("Michała") == []` (koniec `michały`); `podaj_przymiotnik("wołowa")`
  zawiera `wołowy`; „Wyższa Szkoła Pedagogiczna" nadal odmieniana.
- Nowa edycja SGJP → wydanie tylko pakietów danych, kod nietknięty.
