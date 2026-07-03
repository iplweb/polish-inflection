# Split `polish-inflection` → kod + `polish-inflection-data`

**Data:** 2026-07-03
**Status:** projekt zaakceptowany (do przejścia w plan implementacji)

## Problem

Zbudowane indeksy SGJP (`odmien.marisa` ≈ 24 MB, `podaj.marisa` ≈ 25 MB) jadą
dziś w wheelu pakietu `polish-inflection`. Skutek: **każde wydanie kodu re-publikuje
~49 MB słownika na PyPI**, choć dane zmieniają się rzadko (przy nowej edycji SGJP,
kilka razy w roku), a kod — często. Cykl wydań kodu jest sztywno sprzężony z cyklem
danych.

## Cel

Rozdzielić na dwa pakiety PyPI z niezależnymi cyklami wydań:

- **`polish-inflection`** — sam kod (logika odmiany/analizy). Wheel odchudzony do
  kilkudziesięciu KB. Wydania częste, tanie.
- **`polish-inflection-data`** — tylko zbudowane indeksy `.marisa`, wersjonowane
  **wg wersji słownika SGJP**. Wydawane tylko przy nowej edycji SGJP.

UX bez regresji: `pip install polish-inflection` dalej działa od ręki (dane
ciągnięte jako twarda zależność).

## Decyzje (rozstrzygnięte w brainstormingu)

| Decyzja | Wybór |
|---|---|
| Mechanizm odnajdywania danych | Osobny pakiet importowalny `polish_inflection_data` |
| Struktura repo | Monorepo; korzeń = pakiet kodu, `data-package/` = pakiet danych |
| Wersjonowanie danych | Kalendarzowe `YYYY.M.D` z daty SGJP; `.postN` przy przebudowie schematu |
| Zależność kodu od danych | Twarda, dolny pin: `polish-inflection-data>=<min zgodna ze SCHEMA>` |
| Zgodność formatu `.marisa` | Strażnik schematu: `polish_inflection_data.SCHEMA` sprawdzany przez kod |
| Zakres tej rundy | Spec + plan; implementacja i wydania osobno |

## Architektura

### Układ repo

```
polish-inflection/                      # repo iplweb/polish-inflection (nazwa bez zmian)
├── pyproject.toml                      # PAKIET KODU (name="polish-inflection"), korzeń jak dziś
├── src/polish_inflection/              # kod — BEZ plików .marisa
│   ├── core.py                         #   zmieniony locator + strażnik schematu
│   ├── build.py                        #   narzędzie buildu (zostaje tu — kod jest właścicielem schematu)
│   └── … (bez zmian)
├── tests/
├── data-package/                       # NOWY, samodzielny pakiet danych
│   ├── pyproject.toml                  #   name="polish-inflection-data", version="YYYY.M.D"
│   ├── README.md                       #   krótki; atrybucja SGJP, że to artefakt danych
│   ├── src/polish_inflection_data/
│   │   ├── __init__.py                 #   wystawia KATALOG, SCHEMA, WERSJA_SGJP
│   │   └── data/
│   │       ├── odmien.marisa
│   │       ├── podaj.marisa
│   │       └── BUILD_INFO.json
│   └── sgjp/                           #   surowy SGJP (git-lfs) przeniesiony z data/sgjp/
│       ├── sgjp-YYYYMMDD.tab.gz
│       ├── PIN.json
│       └── LICENSE.sgjp
└── docs/, LICENSE, NOTICE.md, …
```

Wariant „pełne `packages/`" świadomie odrzucony — rusza CI/pre-commit/ścieżki bez
proporcjonalnego zysku.

### Pakiet `polish-inflection-data`

Zawiera **wyłącznie** artefakty danych — zero logiki. `__init__.py`:

```python
from importlib.resources import files
from pathlib import Path
import json

#: Wersja formatu kluczy/wartości .marisa (CONTRACT §D). Bump gdy zmienia się schemat.
SCHEMA = 1

KATALOG = Path(str(files("polish_inflection_data") / "data"))

def _build_info() -> dict:
    return json.loads((KATALOG / "BUILD_INFO.json").read_text(encoding="utf-8"))

#: np. "pl.sgjp.sgjp-20260628"
WERSJA_SGJP = _build_info().get("wersja_sgjp")
```

- `pyproject.toml`: `name = "polish-inflection-data"`, `version = "YYYY.M.D"`,
  brak zależności runtime (pliki są statyczne; czyta je kod). Hatchling pakuje
  `*.marisa` + `BUILD_INFO.json` jako artefakty.
- Wersja = kalendarzowa z daty SGJP: `sgjp-20260628` → `2026.6.28`. Przy przebudowie
  tych samych danych po zmianie `SCHEMA` → `2026.6.28.post1`.

### Zmiany w kodzie (`polish_inflection`)

`core.py`:

```python
_OCZEKIWANY_SCHEMA = 1  # kod wie, jakiego formatu .marisa oczekuje

def _domyslny_katalog_danych() -> Path:
    try:
        import polish_inflection_data as dane
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Brak pakietu danych. Zainstaluj: pip install polish-inflection-data"
        ) from e
    if dane.SCHEMA != _OCZEKIWANY_SCHEMA:
        raise RuntimeError(
            f"Niezgodny schemat danych: kod oczekuje {_OCZEKIWANY_SCHEMA}, "
            f"polish-inflection-data ma {dane.SCHEMA}. Zaktualizuj polish-inflection-data."
        )
    return dane.KATALOG
```

- Strażnik schematu odpala się leniwie (przy pierwszym `_wczytaj`), więc sam import
  `polish_inflection` nie wymusza ładowania danych.
- `_ustaw_katalog_danych(sciezka)` (hook testowy) bez zmian — testy mogą wskazać
  dowolny katalog, omijając pakiet danych.
- Zależność w `pyproject.toml` kodu: `polish-inflection-data>=2026.6.28`.

### Build i wydania

- `build.py` **zostaje w pakiecie kodu** — kod jest właścicielem definicji schematu.
  `zbuduj_z_tab(..., --out data-package/src/polish_inflection_data/data)` wpisuje do
  `BUILD_INFO.json` również `schema` (= `_OCZEKIWANY_SCHEMA`), żeby artefakt niósł
  swój schemat jawnie. `SCHEMA` w `__init__.py` pakietu danych ustawiany ręcznie
  przy wydaniu danych (musi zgadzać się z `BUILD_INFO["schema"]`; walidowane testem).
- **Wydanie danych** (nowy SGJP): `refresh-sgjp` → `build --out data-package/…` →
  ustaw `version` = `YYYY.M.D` i `SCHEMA` → `uv build` + `uv publish` w `data-package/`.
- **Wydanie kodu**: jak dziś, ale wheel bez `.marisa` (tiny). Gdy zmienia się schemat
  `.marisa` → bump `_OCZEKIWANY_SCHEMA`, przebuduj i wydaj dane (`.postN` lub nowa
  data), podnieś dolny pin zależności.

## Przepływ danych (runtime, u użytkownika)

```
import polish_inflection            # nie ładuje danych
odmien("wydział", DOPEŁNIACZ)
  └─ _trie_odmien() → _wczytaj("odmien.marisa")
       └─ _domyslny_katalog_danych()
            ├─ import polish_inflection_data           # twarda zależność, obecny
            ├─ sprawdź dane.SCHEMA == _OCZEKIWANY_SCHEMA
            └─ zwróć dane.KATALOG
       └─ marisa_trie.mmap(KATALOG / "odmien.marisa")  # mmap, jak dziś
```

Mechanika mmap i wydajność bez zmian — zmienia się wyłącznie **skąd** brany jest
katalog `data/`.

## Obsługa błędów

| Sytuacja | Zachowanie |
|---|---|
| Brak `polish_inflection_data` | `RuntimeError` z instrukcją `pip install polish-inflection-data` |
| Niezgodny `SCHEMA` (stare dane, nowy kod) | `RuntimeError` z oczekiwanym vs faktycznym schematem |
| `BUILD_INFO["schema"]` ≠ `SCHEMA` w pakiecie danych | Wychwycone testem pakietu danych (nie runtime) |
| Import `polish_inflection` bez sięgania po dane | Działa (strażnik leniwy) |

## Testy

- Testy jednostkowe/integracyjne kodu: bez zmian logiki; wymagają zainstalowanego
  `polish-inflection-data` (editable w dev). `conftest`/`_ustaw_katalog_danych`
  działają jak dziś.
- Testy charakteryzacyjne SGJP (`test_przymiotnik`, `test_zgadnij_przymiotnik`)
  czytają surowy `.tab.gz` — ścieżka zmienia się na `data-package/sgjp/`. Zachowują
  obecny `skipif` (brak realnego gzipa w checkoutcie bez LFS → pomijane).
- **Nowe testy:**
  - kod: strażnik schematu — zgodność przechodzi; podstawiony `SCHEMA≠oczekiwany`
    rzuca `RuntimeError` (przez monkeypatch modułu danych).
  - pakiet danych: `SCHEMA == BUILD_INFO["schema"]`; `WERSJA_SGJP` niepuste;
    oba `.marisa` istnieją i otwierają się przez `marisa_trie.mmap`.

## Migracja (kolejność bezpieczna)

1. Utwórz `data-package/`, przenieś `data/sgjp/` → `data-package/sgjp/`, zbuduj
   `.marisa` do `data-package/src/polish_inflection_data/data`, ustaw
   `version=2026.6.28`, `SCHEMA=1`.
2. **Opublikuj `polish-inflection-data 2026.6.28`** na PyPI (musi być pierwsze —
   inaczej dolny pin kodu się nie zresolvuje).
3. Usuń `.marisa` z pakietu kodu (`src/polish_inflection/data/`), przełącz locator +
   strażnik schematu, dodaj zależność `polish-inflection-data>=2026.6.28`,
   zaktualizuj hatchling (już nie pakuje `.marisa`).
4. Zaktualizuj testy (ścieżka surowego SGJP), CI (dwa job-y), docs/README/CHANGELOG.
5. **Wydaj `polish-inflection 0.7.0`** — API bez zmian (minor), wheel z ~28 MB do
   ~kilkudziesięciu KB.

## Poza zakresem (YAGNI)

- Wariant opcjonalnej zależności (`extra [data]`) — można dodać później, gdyby ktoś
  chciał własny build danych.
- Entry-point/plugin discovery wielu wersji danych naraz.
- Pełny układ `packages/` — odrzucony jako nadmiarowy.

## Kryteria sukcesu

- `pip install polish-inflection` ciągnie kod + dane; publiczne API i wyniki
  identyczne jak w 0.6.0 (testy zielone).
- Wheel `polish-inflection` bez plików `.marisa` (weryfikacja zawartości).
- Nowa edycja SGJP → wydanie **tylko** `polish-inflection-data` (kod nietknięty).
- Niezgodny schemat danych → czytelny błąd, nie ciche śmieci.
