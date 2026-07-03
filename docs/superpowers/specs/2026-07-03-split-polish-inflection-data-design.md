# Split `polish-inflection`: kod + `polish-inflection-data`

**Data:** 2026-07-03
**Status:** projekt zaakceptowany + recenzja subagenta naniesiona (do implementacji)

## Problem

1. Zbudowane indeksy SGJP (`odmien.marisa` ≈ 24 MB, `podaj.marisa` ≈ 25 MB) jadą
   w wheelu `polish-inflection`, więc **każde wydanie kodu re-publikuje ~49 MB**
   słownika — choć dane zmieniają się rzadko, a kod często.
2. Rozpoznawanie przymiotników (`zgadnij_przymiotnik`) jest **regułowe bez oparcia
   w leksykonie** → nadgeneruje: dla `"Michała"` (forma rzeczownika `Michał`)
   proponuje nieistniejący przymiotnik `michały`.

## Cel

Dwa pakiety PyPI o niezależnych cyklach wydań:

- **`polish-inflection`** — sam kod. Wheel odchudzony do ~kilkudziesięciu KB.
- **`polish-inflection-data`** — WSZYSTKIE artefakty SGJP: `odmien.marisa` +
  `podaj.marisa` (rzeczowniki) ORAZ `przymiotniki.marisa` (zbiór baz deklinacyjnych
  przymiotników/imiesłowów, 0,50 MB). Wersjonowany wg edycji SGJP.

Baza `polish-inflection` **twardo wymaga** `polish-inflection-data`. UX bez
regresji: `pip install polish-inflection` ciągnie komplet.

## Decyzje

| Decyzja | Wybór |
|---|---|
| Mechanizm danych | Jeden osobny pakiet importowalny `polish_inflection_data` |
| Struktura repo | Monorepo; korzeń = kod, `data-package/` = pakiet danych |
| Wersjonowanie danych | Kalendarzowe `YYYY.M.D` z daty SGJP; `.postN` przy zmianie schematu |
| Zależność kodu | Twarda, dolny pin: `polish-inflection-data>=2026.6.28` |
| Zgodność `.marisa` | Strażnik schematu (`polish_inflection_data.SCHEMA`) — guard RUNTIME |
| Rozpoznawanie przymiotnika | **Leksykalne**: reguły filtrowane zbiorem baz |
| Nazwa funkcji | `zgadnij_przymiotnik` → **`podaj_przymiotnik`** |

## Kluczowa idea: grunt leksykalny bez indeksu form

Fałszywe pozytywy (`Michała → michały`) biorą się z braku leksykonu, nie z reguł.
Nie trzymamy wszystkich form przymiotników (742k, ~10–20 MB pełnego reverse). Trzymamy
**zbiór baz deklinacyjnych** = mianownik l.poj. rodzaju męskiego.

**Predykat ekstrakcji (dokładny, reprodukowalny):** dla linii SGJP `.tab` weź
`forma.lower()` gdy tag `parts[0] ∈ {adj, pact, ppas}` ORAZ `"sg" ∈ parts[1].split(".")`
ORAZ `"nom" ∈ parts[2].split(".")` ORAZ `parts[3].split(".") ∩ {m1,m2,m3} ≠ ∅`.

- **Dlaczego też `pact`/`ppas` (imiesłowy):** silnik reguł odmienia od formy
  mian.l.poj.m *dowolnej* przydawki odmieniającej się przymiotnikowo. Bez imiesłowów
  filtr odciąłby atrybutywne przydawki (`zjednoczony`, `zintegrowany` — w SGJP tylko
  `ppas`) → regresja `odmien_fraze`. Dołączenie imiesłowów NIE dodaje śmieci (to realne
  słowa), tylko zapobiega false-negatives.
- **Dlaczego wszystkie stopnie:** `nom` obejmuje mian.l.poj.m każdego stopnia, więc
  `wyższy`/`najwyższy` wchodzą (kluczowe dla „Wyższa Szkoła").

Zmierzone na SGJP 20260628 (predykat wyżej): **140 081 baz → 0,50 MB** marisa `Trie`.

| baza | w zbiorze | skutek |
|---|---|---|
| `wyższy`, `najwyższy`, `wysoki` | ✓ | „Wyższa Szkoła" działa |
| `lubelski`, `medyczny`, `wołowy`, `lekarski`, `główny`, `stosowany` | ✓ | nazwy instytucji |
| `zjednoczony`, `zintegrowany`, `otwarty` (ppas) | ✓ | przydawki imiesłowowe bez regresji |
| `michały`, `dupy` | ✗ | false-positives wyeliminowane |

`podaj_przymiotnik(forma)`: reguły generują kandydatów na bazę → **odrzuć spoza
zbioru** → dla pozostałych zweryfikuj generacją, że `forma` z nich wynika.

## Architektura

### Układ repo (monorepo, korzeń = kod)

```
polish-inflection/                      # repo iplweb/polish-inflection
├── pyproject.toml                      # PAKIET KODU (name="polish-inflection")
│                                       #   + [tool.uv.workspace] members=["data-package"]
│                                       #   + [tool.uv.sources] polish-inflection-data={workspace=true}
├── src/polish_inflection/
│   ├── core.py                         #   locator danych przez _dane
│   ├── przymiotnik.py                  #   podaj_przymiotnik: reguły + filtr baz + hook testowy
│   ├── _dane.py                        #   NOWY: locator pakietu + strażnik schematu + cache mmap
│   ├── build.py                        #   buduje odmien+podaj+przymiotniki do data-package
│   └── …
├── tests/  (+ conftest wpina hook zbioru baz)
├── data-package/
│   ├── pyproject.toml                  #   name="polish-inflection-data", ver=YYYY.M.D, hatchling
│   ├── src/polish_inflection_data/
│   │   ├── __init__.py                 #   KATALOG, SCHEMA, WERSJA_SGJP
│   │   └── data/  odmien.marisa, podaj.marisa, przymiotniki.marisa, BUILD_INFO.json, LICENSE.sgjp, NOTICE.md
│   └── sgjp/  sgjp-YYYYMMDD.tab.gz, PIN.json, LICENSE.sgjp   # surowy SGJP (git-lfs), źródło buildu
└── docs/, LICENSE, NOTICE.md, …
```

### Monorepo dev wiring (KRYTYCZNE — bez tego `uv sync` pada na niepublikowanym pinie)

Kod deklaruje `polish-inflection-data>=2026.6.28`, której na starcie nie ma na PyPI.
Rozwiązanie — uv workspace (resolver bierze pakiet z drzewa, nie z PyPI):

```toml
# pyproject.toml (kod)
[tool.uv.workspace]
members = ["data-package"]
[tool.uv.sources]
polish-inflection-data = { workspace = true }
```

Lokalny editable `2026.6.28` spełnia `>=2026.6.28` (chicken-egg pinu rozwiązany).
CI (`ci.yml`): `uv sync` (workspace ogarnia dane) lub jawnie `uv pip install -e ./data-package -e .` PRZED testami. Bez `tool.uv.sources` resolver poszedłby na PyPI → fail.

### Pakiet `polish-inflection-data`

```python
# polish_inflection_data/__init__.py
from importlib.resources import files
from pathlib import Path
import json
SCHEMA = 1
KATALOG = Path(str(files("polish_inflection_data") / "data"))
WERSJA_SGJP = json.loads((KATALOG / "BUILD_INFO.json").read_text("utf-8")).get("wersja_sgjp")
```

- Artefakty w `src/polish_inflection_data/data/`: `odmien.marisa`, `podaj.marisa`,
  `przymiotniki.marisa`, `BUILD_INFO.json`, **`LICENSE.sgjp` + `NOTICE.md`** (KRYTYCZNE:
  `.marisa` to utwory zależne od SGJP — nota licencyjna MUSI jechać w wheelu danych;
  katalog `data-package/sgjp/` jest poza `src/`, więc hatchling go nie spakuje).
- Hatchling: `[tool.hatch.build.targets.wheel] packages=["src/polish_inflection_data"]`,
  `artifacts=["*.marisa","*.json","LICENSE.sgjp","NOTICE.md"]`. **Wheel musi być
  zwykły (nie zip-safe)** — `mmap` wymaga realnego pliku na dysku; hatchling domyślnie
  daje rozpakowywalny wheel, `files()` zwraca realny `Path` w `site-packages`. OK,
  ale zapisujemy jako jawny wymóg.
- Brak zależności runtime. Wersja `YYYY.M.D`; `.postN` przy zmianie schematu.

### Kod: `_dane.py` (locator + strażnik + cache)

```python
_SCHEMA = 1  # jakiego formatu .marisa oczekuje kod
def katalog() -> Path:
    try:
        import polish_inflection_data as dane
    except ModuleNotFoundError as e:
        raise RuntimeError("Brak pakietu danych. Zainstaluj: pip install polish-inflection-data") from e
    if dane.SCHEMA != _SCHEMA:
        raise RuntimeError(f"Niezgodny schemat polish-inflection-data: kod oczekuje {_SCHEMA}, pakiet ma {dane.SCHEMA}.")
    return dane.KATALOG
```

Strażnik to guard **runtime**, nie instalacyjny: `>=` przepuści przyszły `SCHEMA=2`
przy instalacji, błąd poleci przy pierwszym użyciu. Przy bumpie schematu podnosimy
dolny pin ręcznie (rozważyć cap `,<ROK+1` gdy schemat się zmieni).

- `core.py`: `_domyslny_katalog_danych()` → `_dane.katalog()`. Hook `_ustaw_katalog_danych` bez zmian.
- `przymiotnik.py`: leniwie `mmap(przymiotniki.marisa)` z `_dane.katalog()`, cache modułowy,
  **+ hook `_ustaw_zbior_baz(trie|zbior|None)`** (analogiczny do `_ustaw_katalog_danych`).

### `podaj_przymiotnik` — ugruntowanie i rename

```python
def podaj_przymiotnik(forma):
    f = forma.lower()
    bazy = _zbior_baz()                       # marisa Trie z pakietu danych (mmap, cache) lub override
    wynik = set()
    for lemat in _kandydaci_lematow(f):
        if lemat not in bazy:                 # filtr leksykalny — koniec 'michały'
            continue
        # jak dziś: weryfikacja generacją po wszystkich slotach paradygmatu
        ...
    return sorted(wynik, ...)
```

Rename `zgadnij_przymiotnik` → `podaj_przymiotnik`. **Miejsca do zmiany:**
`przymiotnik.py` (def + `__all__` + docstring: leksykalne, nie zgadywanie),
`__init__.py` (import + `__all__`), **`fraza.py` (import l.28 + wołanie w `_lemat_przydawki` l.102)**,
`docs/api.md`, `README.md`. `_kandydaci_lematow` generuje bazy lowercase — spójne z
lowercase w zbiorze.

### Build (`build.py`)

- Rzeczowniki bez zmian (`odmien.marisa` + `podaj.marisa`).
- Przymiotniki: NOWA ścieżka — `parsuj_bazy_adj` wg predykatu wyżej (adj/pact/ppas,
  masc nom sg, lowercase), `marisa_trie.Trie`, zapis `przymiotniki.marisa`.
- Wszystkie trzy + `BUILD_INFO.json` (`wersja_sgjp`, `schema`) do `--out`.
- **Zmiana domyślnych ścieżek:** `--out` default `data-package/src/polish_inflection_data/data`;
  `_domyslny_pin_tab`/`--dane-dir` default `data-package/sgjp`. `polish-inflection-build`
  jest narzędziem **repo-only** (wymaga monorepo + LFS `sgjp/`); z zainstalowanego wheela nie działa (jak dziś).

## Obsługa błędów

| Sytuacja | Zachowanie |
|---|---|
| Brak `polish_inflection_data` | `RuntimeError` z `pip install polish-inflection-data` |
| Niezgodny `SCHEMA` (runtime) | `RuntimeError` (oczekiwany vs faktyczny) |
| `BUILD_INFO["schema"]` ≠ `SCHEMA` pakietu | Test pakietu danych |
| `import polish_inflection` bez użycia danych | Działa (locator leniwy) |

## Git / pre-commit / LFS (KRYTYCZNE)

Dziś `.marisa` są **blobami w gicie** (nie LFS), przechodzą `check-added-large-files`
tylko dzięki regexowi `exclude` w `.pre-commit-config.yaml`. Po przeniesieniu nowa
ścieżka nie pasuje → hook odrzuci commit.

- **Poprawka:** zaktualizować regex `exclude` pre-commita o
  `data-package/src/polish_inflection_data/data/.*\.marisa`. `.marisa` pozostają
  blobami (spójnie z dziś; dane zmieniają się rzadko). `przymiotniki.marisa` (0,5 MB)
  mieści się w limicie, ale ujmujemy je tym samym excludem dla spójności.
- Surowy SGJP `.tab.gz` dalej w LFS — zaktualizować `.gitattributes` na
  `data-package/sgjp/*.tab.gz`.

## Testy

- **conftest:** dodać autouse fixturę budującą MAŁY zbiór baz (z listy przymiotników
  używanych w testach) i wpinającą przez `przymiotnik._ustaw_zbior_baz`; reset po teście.
  Inaczej testy przymiotnika/frazy cicho stają się integracyjne (ładują `przymiotniki.marisa`
  z pakietu). Fraza-test (`_ustaw_katalog_danych(None)`) i tak wymaga editable pakietu danych.
- **`podaj_przymiotnik` — testy leksykalne:** `"Michała"`/`"dupa"` → `[]`;
  `"wołowa"`→`wołowy`, `"Wyższa"`→`wyższy`, `"zjednoczona"`→`zjednoczony` (ppas).
- **Charakteryzacja:** plik `test_zgadnij_przymiotnik.py` → rename na
  `test_podaj_przymiotnik.py`, import `podaj_przymiotnik`, ścieżka SGJP →
  `data-package/sgjp`, usunąć/nie-mylące docstringi „`dupa→dupy` akceptowalne" (już
  nieprawda). Recall gold rozszerzyć o `pact`/`ppas` (inaczej próg nie mierzy efektu
  filtra). Recall biegnie tylko lokalnie (CI ma `lfs:false` → `skipif(not _SGJP)`).
- **Testy pakietu danych:** `SCHEMA == BUILD_INFO["schema"]`; `WERSJA_SGJP` niepuste;
  trzy `.marisa` otwierają się przez marisa; zbiór baz zawiera `lubelski`/`wyższy`/
  `zjednoczony`, nie zawiera `michały`.
- **Fraza:** `KORPUS`/`KORPUS_MNOGA` bez regresji (wszystkie bazy zweryfikowane w zbiorze).

## Migracja (kolejność bezpieczna)

1. Utwórz `data-package/`; przenieś `data/sgjp/` → `data-package/sgjp/`; zaktualizuj
   `.gitattributes` (LFS) i regex `exclude` w pre-commit dla `.marisa`.
2. Napisz `data-package/pyproject.toml` + `src/polish_inflection_data/__init__.py`;
   dodaj `[tool.uv.workspace]`/`[tool.uv.sources]` do pyproject kodu.
3. Rozszerz `build.py` o bazy adj/pact/ppas; zbuduj trzy artefakty do data-package;
   skopiuj `LICENSE.sgjp`+`NOTICE.md` do `src/polish_inflection_data/data/`; ustaw
   `version=2026.6.28`, `SCHEMA=1`.
4. Dodaj `_dane.py`; przełącz `core` i `przymiotnik` (locator + filtr baz + hook);
   rename `zgadnij_przymiotnik`→`podaj_przymiotnik` (wszystkie miejsca); usuń `.marisa`
   z pakietu kodu; hatchling kodu przestaje pakować `.marisa` + dodaj zależność.
5. Zaktualizuj conftest, testy (rename/import/ścieżka/gold), CI, README/`docs/api.md`/CHANGELOG.
6. Zielone testy lokalnie (z editable data-package).
7. **Publikacja:** najpierw `polish-inflection-data 2026.6.28`, potem
   `polish-inflection 0.7.0` (breaking: rename + wymóg pakietu danych; alpha, OK).

## Poza zakresem (YAGNI)

- Osobny pakiet na dane przymiotników — odrzucony (0,5 MB, ta sama edycja SGJP).
- Pełny reverse index form (~10–20 MB) — odrzucony (zbiór baz rozwiązuje FP ~30× taniej).
- Scalanie `podaj`+`podaj_przymiotnik`, `extra [data]`, układ `packages/`, migracja `.marisa` do LFS.

## Kryteria sukcesu

- `pip install polish-inflection` ciągnie kod + dane; API/wyniki jak 0.6.0 poza rename
  i lepszym rozpoznawaniem przymiotników; publiczne API kompletne (w tym alias
  `odmien_rzeczownik` z 0.5.1).
- Wheel `polish-inflection` bez `.marisa`; wheel danych z `LICENSE.sgjp`.
- `podaj_przymiotnik("Michała") == []`; `podaj_przymiotnik("wołowa")` zawiera `wołowy`;
  „Wyższa Szkoła Pedagogiczna" nadal odmieniana; przydawki imiesłowowe bez regresji.
- Nowa edycja SGJP → wydanie tylko `polish-inflection-data`, kod nietknięty.
