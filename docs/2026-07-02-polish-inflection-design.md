# polish-inflection — specyfikacja projektowa

- **Data:** 2026-07-02
- **Status:** projekt zaakceptowany (brainstorming), przed planem implementacji
- **Autor:** Michał Pasternak (+ Claude)
- **Repozytorium:** `~/Programowanie/polish-inflection`

---

## 1. Cel i problem

Chcemy odmieniać polskie **rzeczowniki przez przypadki** programowo — np. mając
wyraz `wydział`, dostać `wydziału` (dopełniacz), `wydziałowi` (celownik) itd.
Zastosowanie źródłowe: nazwy typów jednostek organizacyjnych w BPP
(`jednostka` / `dział` / `wydział` / `klinika` / `koło` / `instytut` / …), które
w interfejsie muszą pojawiać się w różnych przypadkach ("lista pracowników
*wydziału*", "wybierz *jednostkę*").

### Dlaczego nowy pakiet — luka w ekosystemie

Research (2026-07-02) pokazał, że nie istnieje lekkie, czysto-Pythonowe,
przyjazne wdrożeniu rozwiązanie do odmiany polskich rzeczowników:

- **gettext / formy mnogie** — rozwiązują *inny* problem: wybór wariantu wg
  **liczby** (`nplurals=3`: 1 / 2–4 / 5+), a nie odmianę przez **przypadki**.
  gettext nie zna pojęcia przypadka i nie potrafi odmienić rzeczownika. ICU
  MessageFormat / Fluent mają `select`, ale form nie **generują** — trzeba je
  dostarczyć. Ślepa uliczka dla naszego problemu.
- **Morfeusz 2 (SGJP)** — kanoniczny analizator + generator morfologiczny
  polszczyzny, ale natywny silnik C++ + bindingi SWIG + słownik ~dziesiątki MB.
  Armata na muchę i ból wdrożeniowy w Dockerze.
- **pymorphy2 / pymorphy3** — tylko rosyjski i ukraiński. Nie polski.
- **inflection / inflect / pyinflect** — tylko angielski.
- **unimorph_inflect** — modele ML, ciężkie, probabilistyczne.

Ekosystem jest rozdwojony: albo pełny silnik NLP (Morfeusz), albo "trzymaj
formy ręcznie w tabeli" (to, co BPP robi dziś modelem `Rzeczownik`). Nisza na
**lekką, czysto-Pythonową bibliotekę opartą o dane SGJP** realnie istnieje.

### Kluczowa idea architektoniczna: dane, nie silnik

Morfeusz skleja dwie rzeczy, które my rozdzielamy:

- **Silnik** (C++, analiza, segmentacja, guesser, bindingi SWIG) → **odrzucamy.**
- **Dane** (trójki `forma / lemat / tag` w plikach źródłowych `.tab`) → **bierzemy**,
  wycinamy podzbiór rzeczowników, budujemy własny kompaktowy indeks.

Silnik i skompilowany `.dict` (binarny FSA) są nam **niepotrzebne**: mamy zamknięty,
w pełni wyliczony zbiór form w `.tab`, więc nie generujemy niczego w locie — tylko
indeksujemy i wyszukujemy.

---

## 2. Zakres

**W zakresie (v1):**

- Odmiana **rzeczowników** przez 7 przypadków × 2 liczby (poj./mn.).
- Kierunek generacji: `lemat + przypadek + liczba → forma` (funkcja `odmien`).
- Kierunek analizy (zwrotny): `forma → [(lemat, przypadek, liczba)]`
  (funkcja `podaj`).
- Czysta biblioteka Pythonowa — **zero zależności od Django**.

**Poza zakresem (YAGNI — świadomie odłożone):**

- Czasowniki, przymiotniki, liczebniki, inne części mowy.
- Guesser słów spoza słownika, analiza biegnącego tekstu, segmentacja/tokenizacja.
- Warstwa Django (model-override, templatetagi, admin) — to **przyszły konsument**
  tej biblioteki w BPP, osobny byt, nie ten pakiet.
- Pełny "pure-Python Morfeusz" — inny, znacznie większy produkt.

---

## 3. Architektura wysokopoziomowa

Dwie fazy rozdzielone w czasie:

```
┌─────────────────── BUILD (offline, u autora / w CI) ───────────────────┐
│  SGJP .tab (vendored, pinned)                                          │
│      │  filtr: zostaw linie subst / depr                              │
│      │  parse tagu: subst:<liczba>:<przypadek>:<rodzaj>               │
│      ▼                                                                 │
│  budowa DWÓCH indeksów DAWG:                                          │
│      • odmien.dawg   klucz=(lemat, przypadek, liczba) → forma(y)      │
│      • podaj.dawg    klucz=forma → [(lemat, przypadek, liczba, rodzaj)]│
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  artefakty .dawg shipowane w wheelu
┌───────────────────────────────▼─────────── RUNTIME (czysty Python) ────┐
│  odmien("wydział", DOPEŁNIACZ, liczba=POJEDYNCZA) → "wydziału"         │
│  podaj("jednostki")  → [(jednostka, DOPEŁNIACZ, poj.),                 │
│                         (jednostka, MIANOWNIK, mn.),                   │
│                         (jednostka, BIERNIK, mn.)]                     │
└────────────────────────────────────────────────────────────────────────┘
```

Runtime ładuje gotowe `.dawg` (mmap, stała pamięć) — nie widzi ani SGJP `.tab`,
ani Morfeusza, ani narzędzi build.

---

## 4. Format źródła SGJP

Morfeusz ma dwie warstwy formatu; **bierzemy tę pierwszą**:

1. **Źródło `.tab`** — czysty tekst, tab-separated. Linia = jedna forma:
   ```
   forma <TAB> lemat <TAB> tag [<TAB> nazwa <TAB> kwalifikatory]
   ```
   gdzie `tag` dla rzeczownika to `subst:<liczba>:<przypadek>:<rodzaj>`, np.:
   ```
   wydział      wydział   subst:sg:nom:m3
   wydziału     wydział   subst:sg:gen:m3
   wydziałowi   wydział   subst:sg:dat:m3
   wydziałem    wydział   subst:sg:inst:m3
   wydziały     wydział   subst:pl:nom:m3
   wydziałów    wydział   subst:pl:gen:m3
   ```
   - `liczba`: `sg` / `pl`
   - `przypadek`: `nom gen dat acc inst loc voc`
   - `rodzaj`: `m1 m2 m3 f n1 n2 p1 p2 p3` (atrybut lematu, nie parametr zapytania)
   - `depr` — osobny znacznik dla form deprecjatywnych (obsługiwany obok `subst`)

2. **Skompilowany `.dict`** — binarny FSA (dwa automaty: analizy i syntezy),
   nieczytelny bez silnika C++. **Nie używamy go.**

Tag `subst:sg:gen:m3` rozpakowuje się 1:1 na nasz klucz — cały build to
"wczytaj `.tab` → filtruj → rozbij tag → wsyp do DAWG".

---

## 5. Reprezentacja danych: DAWG

**Wybór: DAWG (Directed Acyclic Word Graph), nie SQLite.**

Uzasadnienie:

- Dane to **read-only słownik ładowany raz** — nie potrzeba zapytań ad-hoc,
  zakresów, mutowalności (mocne strony SQLite).
- Indeks SQLite (B-drzewo) przyspiesza *wyszukanie*, ale **nie kompresuje**:
  każda forma leży w wierszu w całości, zero współdzielenia wspólnych rdzeni i
  końcówek. SQLite nie ma typu "trie/automat".
- DAWG kompresuje **strukturalnie**: scala wspólne prefiksy (jak trie) *oraz*
  wspólne sufiksy (współdzielone pod-grafy). Polska fleksja = ~1116 wzorców
  końcówek na ~330k leksemów → końcówki (`-ach`, `-owi`, `-ami`, `-em`) powtarzają
  się miliony razy; DAWG scala obie osie redundancji. To matematycznie minimalny
  automat dla danego zbioru.
- Lookup = przejście grafu w O(długość słowa), stała pamięć (mmap).

**Biblioteka:** `dawg2` / `DAWG-Python` (autor: ten sam co pymorphy) — `BytesDAWG`
/ `RecordDAWG` mapują klucz-string → **listę** rekordów binarnych. Czysto-Pythonowy
reader, `pip install`, zero C++.

- `odmien.dawg` — `BytesDAWG`, klucz `"lemat\tprzypadek\tliczba"` → forma(y).
  Oboczności (wiele poprawnych form w jednym slocie) = wiele rekordów pod kluczem.
- `podaj.dawg` — `BytesDAWG`, klucz `"forma"` → rekordy `(lemat, przypadek,
  liczba, rodzaj)`. Synkretyzm/homografia = wiele rekordów pod kluczem.

**Fallback:** jeśli pomiar rozmiaru rzeczowników-DAWG pokaże plik nadmiernie
ciężki na PyPI — rozważyć wariant kompresji/kwantyzacji, ale to zamiana warstwy
storage za flagą, nie zmiana architektury. Domyślnie: DAWG.

---

## 6. Pipeline BUILD

Faza offline, uruchamiana u autora / w CI, **nie** przy `pip install`.

### 6.1. Pozyskanie i vendoring SGJP

- Domyślny build czyta **vendorowaną, przypiętą** kopię SGJP z repo
  (`data/sgjp/sgjp-<wersja>.tab.gz`) — reprodukowalność i **odporność na
  zniknięcie źródła** (upstream może zniknąć; kopia podróżuje z repo).
- Metadane pinu: plik `data/sgjp/PIN.json` z `wersja`, `data_pobrania`,
  `sha256`, `url_zrodlowy`.
- Osobna komenda maintainerska `refresh-sgjp` pobiera **najnowszą** wersję SGJP,
  weryfikuje, aktualizuje pin (wersja + suma kontrolna) i re-vendoruje. Normalny
  build nigdy nie sięga do sieci; tylko jawny `refresh` to robi.
- Rozmiar: skompresowany `.tab.gz` rzędu kilkudziesięciu MB. Do rozważenia
  **git-lfs** dla kopii vendorowanej (decyzja w planie).

### 6.2. Budowa indeksów

1. Rozpakuj vendorowany `.tab.gz`.
2. Filtruj linie: zostaw `subst` i `depr`, odrzuć resztę.
3. Parsuj tag → `(liczba, przypadek, rodzaj)`; odrzuć wpisy niekompletne/nietypowe.
4. Zbuduj `odmien.dawg` i `podaj.dawg`.
5. Zapisz artefakty do `src/polish_inflection/data/`.
6. Zapisz `BUILD_INFO.json` (wersja SGJP, data build, liczba lematów/form,
   rozmiary plików) — do diagnostyki i do README.

### 6.3. Co ląduje gdzie

| Artefakt | Repo/git | sdist | wheel |
|---|---|---|---|
| Vendorowany SGJP `.tab.gz` + `PIN.json` | ✅ (durability) | do decyzji (rozmiar) | ❌ |
| Zbudowane `.dawg` | ✅ (lub build w CI) | ✅ | ✅ |
| Skrypt build + `refresh-sgjp` | ✅ | ✅ | ❌ |

Wheel wiezie tylko kompaktowe `.dawg` — użytkownik dostaje działający pakiet bez
SGJP i bez narzędzi build.

---

## 7. API runtime

Czysty Python, moduł `polish_inflection`.

### 7.1. Stałe (plik `const`)

Nazwane stałe przypadków i liczby (mapowane wewnętrznie na tagi SGJP):

```python
# polish_inflection/const.py
MIANOWNIK   = "nom"   # kto? co?
DOPEŁNIACZ  = "gen"   # kogo? czego?
CELOWNIK    = "dat"   # komu? czemu?
BIERNIK     = "acc"   # kogo? co?
NARZĘDNIK   = "inst"  # (z) kim? (z) czym?
MIEJSCOWNIK = "loc"   # o kim? o czym?
WOŁACZ      = "voc"   # o!

POJEDYNCZA  = "sg"
MNOGA       = "pl"
```

(Do rozważenia w planie: `enum.Enum` zamiast stałych modułowych; aliasy skrótami
`M/D/C/B/N/Ms/W` dla zwięzłości. Kanoniczne są **nazwane stałe**.)

### 7.2. Funkcje

```python
def odmien(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA) -> str:
    """Zwróć główną formę `wyraz` w danym przypadku i liczbie.

    >>> odmien("wydział", DOPEŁNIACZ)
    'wydziału'
    >>> odmien("jednostka", BIERNIK)
    'jednostkę'
    >>> odmien("wydział", DOPEŁNIACZ, liczba=MNOGA)
    'wydziałów'
    """

def podaj(wyraz: str, liczba: str | None = None) -> list[Analiza]:
    """Zwróć listę analiz danej formy (kierunek zwrotny).

    Zwraca LISTĘ — polszczyzna ma synkretyzm (jedna forma = wiele przypadków)
    i homografię (jedna forma = wiele lematów). Opcjonalny `liczba` zawęża,
    ale rzadko do jednego wyniku.

    >>> podaj("wydział")
    [Analiza(lemat='wydział', przypadek=MIANOWNIK, liczba=POJEDYNCZA, ...),
     Analiza(lemat='wydział', przypadek=BIERNIK,   liczba=POJEDYNCZA, ...)]
    >>> podaj("jednostki", liczba=MNOGA)
    [Analiza(lemat='jednostka', przypadek=MIANOWNIK, liczba=MNOGA, ...),
     Analiza(lemat='jednostka', przypadek=BIERNIK,   liczba=MNOGA, ...)]
    """
```

`Analiza` — lekki `NamedTuple`/`dataclass`: `(lemat, przypadek, liczba, rodzaj)`.

### 7.3. Zachowanie brzegowe

- **Słowo spoza słownika** (`odmien`): brak wpisu → wyjątek dedykowany
  (`BrakOdmiany`/`LemmaNotFound`) zamiast cichego zwrotu wejścia. Konsument
  (BPP) decyduje o fallbacku. (Do decyzji w planie: wyjątek vs `None` vs sentinel.)
- **Oboczności** (`odmien`): wiele poprawnych form → zwracamy **główną**;
  wariant `warianty=True` lub osobna funkcja zwraca listę (decyzja w planie).
- **Rodzaj**: atrybut lematu, nie parametr. Gdy string-lemat mapuje się na
  wiele leksemów o różnym rodzaju/paradygmacie → `odmien` zwraca formę
  najczęstszego/pierwszego, a `podaj` ujawnia wszystkie (nieś `lemat` + `rodzaj`).

---

## 8. Struktura repozytorium

```
polish-inflection/
├── README.md                 # NAJPIERW polski, POTEM angielski
├── LICENSE                   # licencja KODU pakietu (np. BSD-2 / MIT — decyzja w planie)
├── NOTICE / THIRD_PARTY.md   # licencja DANYCH: klauzula BSD-2 SGJP + atrybucja
├── pyproject.toml            # build: uv; deps: dawg2/DAWG-Python
├── docs/
│   ├── 2026-07-02-polish-inflection-design.md   # ten spec
│   └── budowanie.md          # jak działa BUILD + refresh-sgjp + vendoring
├── data/
│   └── sgjp/
│       ├── sgjp-<wersja>.tab.gz   # vendorowany, przypięty SGJP (durability)
│       ├── PIN.json               # wersja + sha256 + url + data
│       └── LICENSE.sgjp           # plik licencji jadący z wydaniem SGJP (verbatim)
├── src/
│   └── polish_inflection/
│       ├── __init__.py       # eksport: odmien, podaj, stałe
│       ├── const.py          # PRZYPADEK / LICZBA
│       ├── core.py           # ładowanie DAWG + odmien + podaj
│       ├── build.py          # pipeline BUILD (offline)
│       └── data/             # zbudowane .dawg (shipowane w wheelu)
└── tests/
    └── test_*.py
```

---

## 9. Licencje

Dwie warstwy, jawnie rozdzielone:

1. **Kod pakietu** — permisywna licencja (BSD-2 lub MIT; decyzja w planie),
   plik `LICENSE`.
2. **Dane SGJP** — na **2-clause BSD**; redystrybucja dozwolona pod warunkiem
   zachowania noty copyright + tekstu licencji + atrybucji. **Wymóg twardy.**
   - Do repo dołączamy **verbatim** plik licencji jadący z pobranym wydaniem
     SGJP (`data/sgjp/LICENSE.sgjp`) — autorytatywne źródło podróżuje z danymi,
     bez ręcznego przepisywania tekstu prawnego.
   - `NOTICE` / `THIRD_PARTY.md` cytuje klauzulę i wskazuje atrybucję.

Osadzona klauzula (do zweryfikowania z `LICENSE.sgjp` pinu; copyright wg strony
licencyjnej Morfeusza):

```
Copyright © Institute of Computer Science PAS, 2014–2026.
SGJP inflectional data © Zygmunt Saloni, Włodzimierz Gruszczyński,
Marcin Woliński, Robert Wołosz, Danuta Skowrońska.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES ... HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY ... EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
```

Źródło: https://morfeusz.sgjp.pl/doc/license/en (2-clause BSD; program + dane
Polimorf © ICS PAS, dane SGJP © autorzy wymienieni wyżej).

---

## 10. README (PL → EN)

Kolejność wymuszona: **sekcja polska, potem angielska** (ten sam plik `README.md`).
Zawartość obu: cel, instalacja, przykłady `odmien`/`podaj`, źródło danych (SGJP +
atrybucja), licencja, ograniczenia (tylko rzeczowniki v1).

---

## 11. Testy (TDD)

- Testy charakteryzacyjne na znanym zbiorze słów domenowych (jednostka, dział,
  wydział, klinika, koło, instytut, katedra, zakład, oddział, poradnia) — pełne
  7×2 form wpisane ręcznie jako oczekiwane, weryfikowane wobec `odmien`.
- Testy `podaj` na formach synkretycznych (`jednostki` → M/D poj. + M/B mn.).
- Test brzegowy: słowo spoza słownika → zdefiniowane zachowanie (wyjątek).
- Test spójności build: liczba lematów/form > próg; oba DAWG-i ładują się i
  round-trip `odmien`↔`podaj` zgadza się na próbce.
- pytest, funkcje bez klas.

---

## 12. Ryzyka i mitygacje

| Ryzyko | Mitygacja |
|---|---|
| Rozmiar DAWG za duży na PyPI | Pomiar w planie; git-lfs dla vendora; ewentualny wariant kompresji storage |
| Zniknięcie źródła SGJP | Vendoring pinowanej kopii w repo (wymóg usera) |
| Nieaktualność danych | Komenda `refresh-sgjp` + pin z sumą kontrolną |
| Synkretyzm/homografia mylące konsumenta | `podaj` zwraca listę z lematem+rodzajem; dokumentacja |
| Oboczności w slocie | `odmien` → forma główna; opcja `warianty` |
| Niejednoznaczność licencyjna | Verbatim `LICENSE.sgjp` z pinu + `NOTICE` + atrybucja |
| Nazwa zajęta na PyPI | Sprawdzić dostępność `polish-inflection` w planie |

---

## 13. Kryteria sukcesu

- `odmien("wydział", DOPEŁNIACZ) == "wydziału"` i analogicznie dla całego zbioru
  domenowego (7×2 form) — zielone testy charakteryzacyjne.
- `podaj("jednostki")` zwraca komplet analiz synkretycznych.
- `pip install polish-inflection` daje działający pakiet bez SGJP, bez C++,
  bez narzędzi build; import nie ładuje słownika do RAM (mmap/leniwie).
- Build reprodukowalny z vendorowanego pinu bez dostępu do sieci.
- README PL+EN, LICENSE kodu, NOTICE z klauzulą BSD-2 SGJP + atrybucją.
- Zero zależności od Django.

---

## 14. Decyzje odłożone do planu

1. Licencja kodu pakietu: BSD-2 vs MIT.
2. Stałe jako `enum.Enum` vs stałe modułowe; aliasy skrótowe `M/D/C/…`.
3. Zachowanie `odmien` dla słowa spoza słownika: wyjątek vs `None` vs sentinel.
4. Zwrot oboczności: `warianty=True` vs osobna funkcja vs zawsze lista.
5. git-lfs dla vendorowanego SGJP; czy `.tab.gz` wchodzi do sdist.
6. Dokładna biblioteka DAWG: `dawg2` vs `marisa-trie` (pomiar rozmiar/szybkość).
7. Weryfikacja wolności nazwy `polish-inflection` na PyPI.
