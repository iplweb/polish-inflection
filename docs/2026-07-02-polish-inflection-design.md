# polish-inflection — specyfikacja projektowa

- **Data:** 2026-07-02
- **Status:** projekt zaakceptowany (brainstorming); zaktualizowano po implementacji (marisa-trie)
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

Research (2026-07-02) pokazał, że nie istnieje lekkie, łatwe do wdrożenia
(instalacja bez kompilatora), przyjazne rozwiązanie do odmiany polskich
rzeczowników:

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
**lekką bibliotekę opartą o dane SGJP, instalowalną bez kompilatora**, realnie
istnieje.

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
│      │  (liczba/przypadek dot-collapsed → rozwiń; obetnij fleksem)    │
│      ▼                                                                 │
│  budowa DWÓCH indeksów marisa-trie (BytesTrie):                       │
│      • odmien.marisa  klucz=(lemat, przypadek, liczba) → forma(y)     │
│      • podaj.marisa   klucz=forma → [(lemat, przypadek, liczba, rodzaj)]│
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  artefakty .marisa shipowane w wheelu
┌───────────────────────────────▼──── RUNTIME (bez kompilatora) ─────────┐
│  odmien("wydział", DOPEŁNIACZ, liczba=POJEDYNCZA) → "wydziału"         │
│  podaj("jednostki")  → [(jednostka, DOPEŁNIACZ, poj.),                 │
│                         (jednostka, MIANOWNIK, mn.),                   │
│                         (jednostka, BIERNIK, mn.)]                     │
└────────────────────────────────────────────────────────────────────────┘
```

Runtime ładuje gotowe `.marisa` (mmap, stała pamięć) — nie widzi ani SGJP `.tab`,
ani Morfeusza, ani narzędzi build. Tę samą bibliotekę `marisa-trie` używa build
(zapis) i runtime (odczyt) — brak podziału na osobne biblioteki build/runtime.

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

**Tag SGJP NIE rozpakowuje się 1:1** (weryfikacja na realnych danych):

- Pola **liczby i przypadka są „dot-collapsed"** — jeden rekord koduje wiele
  kombinacji przez kropkę. Np. `subst:sg:nom.acc:m3` = *ta sama forma* dla
  mianownika **i** biernika liczby pojedynczej; tak samo kolapsuje się liczba.
  Build **rozwija** iloczyn kartezjański (`nom.acc` → `nom` + `acc`) na osobne
  klucze — stąd naturalnie bierze się synkretyzm w indeksach.
- Kolumna lematu może nieść **sufiks fleksemu po `:`** (np. `profesor:Sm1`),
  identyfikujący konkretny leksem/paradygmat. Build **obcina** go do gołego
  lematu (`profesor`).
- Formy **`depr`** (deprecjatywne) trafiają **wyłącznie do `podaj`** (analiza),
  **nigdy do `odmien`** (generacja formy głównej).

Cały build to zatem "wczytaj `.tab` → filtruj → rozbij i **rozwiń** tag,
**obetnij fleksem** → wsyp do marisa-trie".

---

## 5. Reprezentacja danych: marisa-trie

**Wybór: marisa-trie (`marisa_trie.BytesTrie`), nie SQLite.**

> **Uwaga (decyzja pomiarowa).** Pierwotnym wyborem był **DAWG** (`BytesDAWG`
> z `dawg2`/`DAWG-Python`) — patrz uzasadnienie strukturalne niżej, które nadal
> obowiązuje co do klasy struktury (trie/automat nad zbiorem kluczy). Po
> zbudowaniu obu wariantów na **pełnym SGJP** okazało się jednak, że payloady
> wartości `BytesDAWG` napompowały artefakty do **~254 MB** (odmien ~150 MB +
> podaj ~104 MB) — powyżej limitu 100 MB/plik na PyPI. Te same dane w
> marisa-trie zajmują **~49 MB** (odmien ~24 MB + podaj ~25 MB). Dlatego
> **przełączyliśmy warstwę storage z DAWG na marisa-trie**; to była zmiana
> zmierzona, nie spekulacja.

Uzasadnienie klasy struktury (dlaczego trie/automat, nie SQLite):

- Dane to **read-only słownik ładowany raz** — nie potrzeba zapytań ad-hoc,
  zakresów, mutowalności (mocne strony SQLite).
- Indeks SQLite (B-drzewo) przyspiesza *wyszukanie*, ale **nie kompresuje**:
  każda forma leży w wierszu w całości, zero współdzielenia wspólnych rdzeni i
  końcówek. SQLite nie ma typu "trie/automat".
- Trie/automat kompresuje **strukturalnie**: scala wspólne prefiksy zbioru
  kluczy. Polska fleksja = ~1116 wzorców końcówek na setki tysięcy leksemów →
  końcówki (`-ach`, `-owi`, `-ami`, `-em`) powtarzają się miliony razy; struktura
  scala tę redundancję. marisa-trie (Matching Algorithm with Recursively
  Implemented StorAge) buduje bardzo zwięzły, statyczny automat nad zbiorem
  kluczy.
- Lookup = przejście automatu w O(długość słowa), stała pamięć (mmap).

**Biblioteka:** `marisa-trie` — **ta sama** biblioteka buduje (zapis) i czyta
(odczyt); brak podziału na osobne biblioteki build vs runtime. `BytesTrie` mapuje
klucz-string → **listę** rekordów binarnych (wiele wartości pod jednym kluczem),
co wprost daje nam synkretyzm i oboczności. Instalacja **bez kompilatora**:
marisa-trie to rozszerzenie C++, ale dostarcza gotowe binarne wheele (cp39–cp313
dla Linux/macOS/Windows), więc `pip install` nie wymaga toolchainu.

- `odmien.marisa` — `BytesTrie`, klucz `"lemat\tprzypadek\tliczba"` → forma(y).
  Oboczności (wiele poprawnych form w jednym slocie) = wiele rekordów pod kluczem.
- `podaj.marisa` — `BytesTrie`, klucz `"forma"` → rekordy `(lemat, przypadek,
  liczba, rodzaj)`. Synkretyzm/homografia = wiele rekordów pod kluczem.

**Reader wykorzystuje mmap:** pojedynczy lookup stronicuje do RAM tylko O(długość
słowa) węzłów automatu (~1 µs/lookup, ~1 mln/s), więc **import nie ładuje słownika
do RAM**. Pomiar: pojedynczy lookup to ~+1,5 MB RSS, wobec ~+23 MB przy pełnym
wczytaniu słownika — spełnia to kryterium sukcesu z §13.

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
- Rozmiar: skompresowany `.tab.gz` rzędu kilkudziesięciu MB. Kopia vendorowana
  trzymana w **git-lfs** i wykluczona z sdist/wheel (rozstrzygnięte — patrz §14).

### 6.2. Budowa indeksów

1. Rozpakuj vendorowany `.tab.gz`.
2. Filtruj linie: zostaw `subst` i `depr`, odrzuć resztę.
3. Parsuj tag → `(liczba, przypadek, rodzaj)`; **rozwiń** pola dot-collapsed
   (`nom.acc`, kolaps liczby) na osobne kombinacje; **obetnij sufiks fleksemu**
   z kolumny lematu (`profesor:Sm1` → `profesor`); odrzuć wpisy
   niekompletne/nietypowe.
4. Zbuduj `odmien.marisa` (bez `depr`) i `podaj.marisa` (z `depr`).
5. Zapisz artefakty do `src/polish_inflection/data/`.
6. Zapisz `BUILD_INFO.json` (wersja SGJP, data build, liczba lematów/form,
   rozmiary plików) — do diagnostyki i do README.

### 6.3. Co ląduje gdzie

| Artefakt | Repo/git | sdist | wheel |
|---|---|---|---|
| Vendorowany SGJP `.tab.gz` + `PIN.json` | ✅ (git-lfs, durability) | ❌ | ❌ |
| Zbudowane `.marisa` | ✅ (lub build w CI) | ✅ | ✅ |
| Skrypt build + `refresh-sgjp` | ✅ | ✅ | ❌ |

Wheel wiezie tylko kompaktowe `.marisa` (~49 MB danych, wheel ≈ 27 MB) —
użytkownik dostaje działający pakiet bez SGJP i bez narzędzi build.

---

## 7. API runtime

Moduł `polish_inflection` (odczyt przez `marisa-trie`).

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

TEN_SAM_WYRAZ = ...   # sentinel dla default= (patrz odmien_lub_wyraz)
```

Rozstrzygnięto: **stałe modułowe** (string), bez `enum.Enum` i bez aliasów
skrótowych `M/D/C/…`. Dodatkowo sentinel `TEN_SAM_WYRAZ` używany jako wartość
`default=` w `odmien` (przepuszcza wejście, gdy brak odmiany).

### 7.2. Funkcje

```python
def odmien(wyraz: str, przypadek: str, liczba: str = POJEDYNCZA,
           *, default=...) -> str:
    """Zwróć główną formę `wyraz` w danym przypadku i liczbie.

    Brak wpisu → domyślnie wyjątek `BrakOdmiany`. Parametr `default=`
    (na wzór `dict.get`) pozwala zwrócić wartość zastępczą zamiast wyjątku;
    `default=TEN_SAM_WYRAZ` przepuszcza wejściowy `wyraz`.

    >>> odmien("wydział", DOPEŁNIACZ)
    'wydziału'
    >>> odmien("jednostka", BIERNIK)
    'jednostkę'
    >>> odmien("wydział", DOPEŁNIACZ, liczba=MNOGA)
    'wydziałów'
    """

def odmien_lub_none(wyraz: str, przypadek: str,
                    liczba: str = POJEDYNCZA) -> str | None:
    """Jak `odmien`, ale słowo spoza słownika → `None` (bez wyjątku)."""

def odmien_lub_wyraz(wyraz: str, przypadek: str,
                     liczba: str = POJEDYNCZA) -> str:
    """Jak `odmien`, ale słowo spoza słownika → zwraca wejściowy `wyraz`
    (odpowiednik `default=TEN_SAM_WYRAZ`)."""

def odmien_warianty(wyraz: str, przypadek: str,
                    liczba: str = POJEDYNCZA) -> list[str]:
    """Zwróć WSZYSTKIE poprawne formy (oboczności) dla slotu, listą.
    `odmien` zwraca tylko formę główną; tu dostajemy komplet wariantów."""

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

- **Słowo spoza słownika** (`odmien`): brak wpisu → domyślnie wyjątek
  `BrakOdmiany` zamiast cichego zwrotu wejścia. Konsument (BPP) decyduje o
  fallbacku. Rozstrzygnięto: obok wyjątku dostępne są `odmien_lub_none` (→`None`),
  `odmien_lub_wyraz` (→wejściowy wyraz) oraz ogólny `default=` (styl `dict.get`,
  w tym `default=TEN_SAM_WYRAZ`).
- **Oboczności** (`odmien`): wiele poprawnych form → `odmien` zwraca **główną**;
  komplet wariantów zwraca osobna funkcja `odmien_warianty() -> list[str]`.
- **Rodzaj**: atrybut lematu, nie parametr. Gdy string-lemat mapuje się na
  wiele leksemów o różnym rodzaju/paradygmacie → `odmien` zwraca formę
  najczęstszego/pierwszego, a `podaj` ujawnia wszystkie (nieś `lemat` + `rodzaj`).

---

## 8. Struktura repozytorium

```
polish-inflection/
├── README.md                 # NAJPIERW polski, POTEM angielski
├── LICENSE                   # licencja KODU pakietu (BSD-2-Clause)
├── NOTICE / THIRD_PARTY.md   # licencja DANYCH: klauzula BSD-2 SGJP + atrybucja
├── pyproject.toml            # build: uv; runtime dep: marisa-trie; [build]: requests
├── docs/
│   ├── 2026-07-02-polish-inflection-design.md   # ten spec
│   └── budowanie.md          # jak działa BUILD + refresh-sgjp + vendoring
├── data/
│   └── sgjp/
│       ├── sgjp-<wersja>.tab.gz   # vendorowany, przypięty SGJP (git-lfs, durability)
│       ├── PIN.json               # wersja + sha256 + url + data
│       └── LICENSE.sgjp           # plik licencji jadący z wydaniem SGJP (verbatim)
├── examples/                 # uruchamialne skrypty użycia (odmien / podaj)
├── src/
│   └── polish_inflection/
│       ├── __init__.py       # eksport: odmien, podaj, stałe, wyjątki
│       ├── const.py          # PRZYPADEK / LICZBA / TEN_SAM_WYRAZ
│       ├── core.py           # ładowanie .marisa + odmien + podaj
│       ├── build.py          # pipeline BUILD (offline)
│       ├── errors.py         # BrakOdmiany i inne wyjątki
│       └── data/             # zbudowane .marisa (shipowane w wheelu)
└── tests/
    ├── fixtures/             # dane testowe (próbki .tab / oczekiwane formy)
    └── test_*.py
```

---

## 9. Licencje

Dwie warstwy, jawnie rozdzielone:

1. **Kod pakietu** — **BSD-2-Clause** (rozstrzygnięte), plik `LICENSE`.
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
- Test brzegowy: słowo spoza słownika → zdefiniowane zachowanie (`BrakOdmiany`,
  `odmien_lub_none` → `None`, `odmien_lub_wyraz` → wejście, `default=`).
- Test spójności build: liczba lematów/form > próg; oba indeksy `.marisa`
  ładują się i round-trip `odmien`↔`podaj` zgadza się na próbce.
- pytest, funkcje bez klas.

---

## 12. Ryzyka i mitygacje

| Ryzyko | Mitygacja |
|---|---|
| Rozmiar indeksu za duży na PyPI | **Rozstrzygnięte pomiarem**: DAWG (`BytesDAWG`) dawał ~254 MB (>100 MB/plik PyPI); marisa-trie daje ~49 MB (wheel ≈ 27 MB) → wybrano marisa-trie |
| Zniknięcie źródła SGJP | Vendoring pinowanej kopii w repo (wymóg usera) |
| Nieaktualność danych | Komenda `refresh-sgjp` + pin z sumą kontrolną |
| Synkretyzm/homografia mylące konsumenta | `podaj` zwraca listę z lematem+rodzajem; dokumentacja |
| Oboczności w slocie | `odmien` → forma główna; `odmien_warianty()` → lista |
| Niejednoznaczność licencyjna | Verbatim `LICENSE.sgjp` z pinu + `NOTICE` + atrybucja |
| Nazwa zajęta na PyPI | **Rozstrzygnięte**: nazwa `polish-inflection` jest wolna |

---

## 13. Kryteria sukcesu

- `odmien("wydział", DOPEŁNIACZ) == "wydziału"` i analogicznie dla całego zbioru
  domenowego (7×2 form) — zielone testy charakteryzacyjne.
- `podaj("jednostki")` zwraca komplet analiz synkretycznych.
- `pip install polish-inflection` daje działający pakiet bez SGJP, bez
  kompilatora (gotowe binarne wheele marisa-trie), bez narzędzi build; import
  nie ładuje słownika do RAM (mmap — lookup stronicuje tylko O(długość słowa)
  węzłów; ~+1,5 MB RSS vs ~+23 MB przy pełnym wczytaniu).
- Build reprodukowalny z vendorowanego pinu bez dostępu do sieci.
- README PL+EN, LICENSE kodu, NOTICE z klauzulą BSD-2 SGJP + atrybucją.
- Zero zależności od Django.

---

## 14. Decyzje (rozstrzygnięte w implementacji)

Pierwotnie odłożone do planu; poniżej z rozstrzygnięciem po implementacji.

1. **Licencja kodu pakietu → BSD-2-Clause** (plik `LICENSE`).
2. **Stałe → stałe modułowe (string)**; bez `enum.Enum`, bez aliasów skrótowych
   `M/D/C/…`.
3. **`odmien` dla słowa spoza słownika → wyjątek `BrakOdmiany`** (domyślnie),
   plus `odmien_lub_none` (→`None`), `odmien_lub_wyraz` (→wejściowy wyraz, przez
   `default=TEN_SAM_WYRAZ`) oraz ogólny parametr `default=` (styl `dict.get`).
4. **Zwrot oboczności → osobna funkcja `odmien_warianty() -> list[str]`.**
5. **git-lfs** dla vendorowanego `.tab.gz`; wykluczony ze sdist i wheela.
6. **Biblioteka storage → marisa-trie** (zamiast DAWG). Pomiar na pełnym SGJP:
   DAWG `BytesDAWG` ~254 MB vs marisa-trie ~49 MB — decydujący był limit
   100 MB/plik na PyPI.
7. **Nazwa `polish-inflection` na PyPI → wolna.**

Kontekst pomiaru z pkt. 6: pełny SGJP to 223 748 lematów / 3 864 426 rekordów
form (wersja `pl.sgjp.sgjp-2026.06.29`, pin `sgjp-20260628`); artefakty
`odmien.marisa` ≈ 24 MB i `podaj.marisa` ≈ 25 MB, wheel ≈ 27 MB.
