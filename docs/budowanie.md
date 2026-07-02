# Budowanie indeksów (BUILD)

Ten dokument opisuje, jak z danych SGJP powstają zbudowane indeksy `.marisa`,
które wiezie wheel. Faza BUILD jest **offline**, uruchamiana u autora lub w CI —
nigdy przy `pip install`. Użytkownik pakietu nie buduje niczego i nie potrzebuje
SGJP.

Zależności rozdziela `pyproject.toml`:

- **runtime**: `marisa-trie` — ta sama biblioteka **buduje i czyta** indeksy
  `.marisa` (`marisa_trie.BytesTrie`); dostarcza gotowe binarne wheele, więc
  `pip install` nie potrzebuje kompilatora.
- **build (extra `build`)**: `requests` (pobieranie SGJP) — instalowane tylko do
  budowania: `pip install -e ".[build]"` (lub `uv sync --extra build`).

CLI budowniczego wpięte jest jako skrypt **`polish-inflection-build`**
(`[project.scripts]` → `polish_inflection.build:main`), z dwiema podkomendami:
`build` i `refresh-sgjp`.

---

## 1. Vendoring i pin

Domyślny build czyta **zwendorowaną, przypiętą** kopię SGJP z repozytorium —
plik `data/sgjp/sgjp-<wersja>.tab.gz`. To daje reprodukowalność i odporność na
zniknięcie źródła: upstream może kiedyś zniknąć, a kopia podróżuje z repo.

Metadane pinu leżą w **`data/sgjp/PIN.json`**:

| klucz | znaczenie |
|---|---|
| `wersja` | wersja wydania SGJP, np. `20260628` (z nagłówka `#!DICT-ID`) |
| `data_pobrania` | data zwendorowania kopii (ISO 8601) |
| `sha256` | suma kontrolna pobranego `.tab.gz` (weryfikacja integralności) |
| `url_zrodlowy` | dokładny URL, z którego pobrano wydanie |

Skompresowany `.tab.gz` ma rzędu kilkudziesięciu MB (SGJP `20260628` ≈ 42,7 MB),
dlatego jest śledzony przez **git-lfs** — reguła w `.gitattributes`:

```
data/sgjp/*.tab.gz filter=lfs diff=lfs merge=lfs -text
```

Aby po sklonowaniu repo mieć realny plik (a nie wskaźnik LFS), potrzebny jest
zainstalowany `git-lfs` i `git lfs pull`.

---

## 2. `refresh-sgjp` — jedyne miejsce sięgające do sieci

Komenda maintainerska, aktualizująca zwendorowaną kopię do **najnowszego**
wydania SGJP:

```bash
polish-inflection-build refresh-sgjp
```

Kroki:

1. Pobiera najnowszy `sgjp-<data>.tab.gz` z
   `https://download.sgjp.pl/morfeusz/<data>/sgjp-<data>.tab.gz`.
2. Liczy `sha256` i zapisuje plik do `data/sgjp/sgjp-<wersja>.tab.gz`
   (śledzony przez git-lfs).
3. Odczytuje wersję z nagłówka `#!DICT-ID pl.sgjp.sgjp-YYYY.MM.DD` i aktualizuje
   `data/sgjp/PIN.json` (`wersja`, `data_pobrania`, `sha256`, `url_zrodlowy`).
4. Wyodrębnia blok `#<COPYRIGHT> … #</COPYRIGHT>` z nagłówka pliku i zapisuje go
   verbatim do **`data/sgjp/LICENSE.sgjp`** (autorytatywny tekst licencji
   podróżujący z danymi — patrz `NOTICE.md`).

`refresh-sgjp` to **jedyna** komenda korzystająca z sieci. Normalny `build` nigdy
nie pobiera niczego.

---

## 3. `build` — reprodukowalny build z pinu (bez sieci)

```bash
polish-inflection-build build
```

Czyta wyłącznie zwendorowany `data/sgjp/sgjp-<wersja>.tab.gz` i przetwarza go
całkowicie lokalnie:

1. Rozpakowuje `.tab.gz` (strumieniowo, gzip).
2. Filtruje linie: zostają tylko te, których tag zaczyna się od `subst:` lub
   `depr:`; linie `#` (nagłówek, copyright) i pozostałe części mowy są pomijane.
3. Parsuje i **ekspanduje** tag SGJP — pola `liczba` i `przypadek` bywają
   kropkowo sklejonymi podzbiorami (np. `subst:pl:nom.acc.voc:m3` → trzy rekordy),
   a lemat może nieść sufiks fleksemu po dwukropku (`profesor:Sm1` → goły lemat
   `profesor`). Wpisy niekompletne/nietypowe są odrzucane.
4. Buduje dwa indeksy `marisa_trie.BytesTrie` i zapisuje je do
   `src/polish_inflection/data/`:
   - **`odmien.marisa`** — klucz `"lemat\tprzypadek\tliczba"` → forma(y);
     źródło: tylko wpisy `subst` (formy główne).
   - **`podaj.marisa`** — klucz `"forma"` → rekordy `(lemat, przypadek, liczba,
     rodzaj)`; źródło: wpisy `subst` **oraz** `depr` (formy deprecjatywne
     ujawniane tylko w kierunku zwrotnym).
5. Zapisuje `BUILD_INFO.json` (wersja SGJP z `#!DICT-ID`, data buildu, liczba
   lematów/form, rozmiary plików) — do diagnostyki i README.

W testach build kieruje się do `tmp_path`, nie do pakietu — testy nie zależą od
realnych, wielkich `.marisa`.

> Tę samą bibliotekę `marisa-trie` używamy do **zapisu** i **odczytu** indeksów,
> więc nie ma rozdziału build-vs-runtime. `marisa-trie` dostarcza binarne wheele,
> a czytnik mapuje indeks przez **mmap** — pojedynczy lookup stronicuje tylko
> O(długość słowa) węzłów (~1 µs), więc import nie ładuje słownika do RAM.
> Oba indeksy (`odmien.marisa` + `podaj.marisa`) ważą łącznie ~49 MB dla całego
> zbioru rzeczowników SGJP (223 748 lematów / ~3,86 mln form-rekordów).

---

## 4. Co ląduje gdzie (spec §6.3)

| Artefakt | Repo/git | sdist | wheel |
|---|---|---|---|
| Zwendorowany SGJP `.tab.gz` + `PIN.json` | ✅ (durability, git-lfs) | ❌ (rozmiar) | ❌ |
| Zbudowane `.marisa` | ✅ (lub build w CI) | ✅ | ✅ |
| Skrypt build + `refresh-sgjp` | ✅ | ✅ | ❌ (kod jest w src, ale nieużywany w runtime) |

Wheel wiezie wyłącznie kompaktowe `.marisa` — użytkownik dostaje działający pakiet
bez SGJP i bez narzędzi build. Surowy `.tab.gz` jest wykluczony z sdist ze
względu na rozmiar (`exclude = ["data/sgjp/*.tab.gz"]` w `pyproject.toml`);
odtworzenie buildu wymaga sklonowania repo z git-lfs.

---

## 5. Typowy cykl maintainera

```bash
# 1. odśwież dane do najnowszego wydania SGJP (sieć)
polish-inflection-build refresh-sgjp

# 2. przejrzyj zmianę pinu i licencji
git diff data/sgjp/PIN.json data/sgjp/LICENSE.sgjp

# 3. przebuduj indeksy z nowego pinu (offline)
polish-inflection-build build

# 4. uruchom testy i zacommituj (kopia .tab.gz idzie przez git-lfs)
uv run pytest -q
git add data/sgjp src/polish_inflection/data
git commit -m "chore: odśwież SGJP do <wersja>"
```
