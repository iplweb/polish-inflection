# polish-inflection

[![PyPI](https://img.shields.io/pypi/v/polish-inflection.svg)](https://pypi.org/project/polish-inflection/)
[![Python versions](https://img.shields.io/pypi/pyversions/polish-inflection.svg)](https://pypi.org/project/polish-inflection/)
[![CI](https://github.com/iplweb/polish-inflection/actions/workflows/ci.yml/badge.svg)](https://github.com/iplweb/polish-inflection/actions/workflows/ci.yml)
[![License: BSD-2-Clause](https://img.shields.io/badge/License-BSD--2--Clause-blue.svg)](LICENSE)

Lekka, dane-only odmiana polskich **rzeczowników** przez przypadki.
Dane pochodzą ze [Słownika gramatycznego języka polskiego (SGJP)](https://morfeusz.sgjp.pl/),
wyszukiwanie oparte jest o kompaktowy indeks `marisa-trie` (mmap, ~1 µs/lookup).
Instalacja bez kompilatora (gotowe binarne wheele), zero Django, jedna
zależność runtime.

---

## 🇵🇱 Wersja polska

### Cel

Chcesz z wyrazu `wydział` dostać `wydziału` (dopełniacz), `wydziałowi`
(celownik), `wydziałów` (dopełniacz liczby mnogiej) — programowo, bez trzymania
form ręcznie w tabeli. `polish-inflection` odmienia rzeczowniki przez
**7 przypadków × 2 liczby** w obie strony:

- generacja: `lemat + przypadek + liczba → forma` (`odmien`);
- analiza (kierunek zwrotny): `forma → [analizy]` (`podaj`).

### Dlaczego — luka w ekosystemie

Nie istniało lekkie, dane-only, przyjazne wdrożeniu rozwiązanie do
odmiany polskich rzeczowników przez przypadki:

- **gettext / formy mnogie** rozwiązują *inny* problem — wybór wariantu wg
  **liczby** (`nplurals`), a nie odmianę przez **przypadki**. gettext nie zna
  pojęcia przypadka i nie potrafi odmienić rzeczownika.
- **Morfeusz 2** to kanoniczny analizator i generator morfologii polskiej, ale
  natywny silnik C++ + bindingi SWIG + kompilacja słownika rzędu dziesiątek MB.
  Armata na muchę i ból wdrożeniowy w kontenerze. Tu nie ma silnika, SWIG-a ani
  kompilacji słownika — tylko dane i `pip install`.
- **pymorphy2 / pymorphy3** obsługują tylko rosyjski i ukraiński — nie polski.
- **inflection / inflect / pyinflect** — tylko angielski.

Kluczowa idea: bierzemy **dane** SGJP (trójki `forma / lemat / tag`), a odrzucamy
**silnik**. Zbiór form jest zamknięty i w pełni wyliczony — nic nie generujemy
w locie, tylko indeksujemy i wyszukujemy.

### Instalacja

```bash
pip install polish-inflection
```

Jedyna zależność runtime to `marisa-trie` — kompilowane rozszerzenie C++, które
dostarcza gotowe binarne wheele (Linux/macOS/Windows, cp39–cp313), więc
`pip install` nie potrzebuje kompilatora ani narzędzi build. Pakiet wiezie gotowe
indeksy `.marisa` w wheelu — bez SGJP. Czytnik używa **mmap**: import nie ładuje
słownika do RAM, a pojedynczy lookup stronicuje tylko O(długość słowa) węzłów
(~1 µs, mierzony narzut RSS ~1,5 MB zamiast ~23 MB pełnego wczytania).

### Przykłady — `odmien`

```python
from polish_inflection import odmien, DOPEŁNIACZ, MNOGA

odmien("wydział", DOPEŁNIACZ)          # -> "wydziału"
odmien("wydział", DOPEŁNIACZ, MNOGA)   # -> "wydziałów"
```

Zachowanie przy słowie spoza słownika jest sterowane parametrem `default`:

```python
from polish_inflection import (
    odmien, odmien_lub_none, odmien_lub_wyraz, BrakOdmiany, DOPEŁNIACZ,
)

odmien("wydział", DOPEŁNIACZ)                 # "wydziału"
odmien("qwerty", DOPEŁNIACZ)                  # raise BrakOdmiany
odmien_lub_none("qwerty", DOPEŁNIACZ)         # None
odmien_lub_wyraz("qwerty", DOPEŁNIACZ)        # "qwerty"  (passthrough wejścia)
odmien("qwerty", DOPEŁNIACZ, default="—")     # "—"       (dowolny fallback)
```

Oboczności (kilka poprawnych form w jednym slocie) zwraca `odmien_warianty`:

```python
from polish_inflection import odmien_warianty, MIEJSCOWNIK
odmien_warianty("pokój", MIEJSCOWNIK)   # -> lista wszystkich poprawnych form
```

### Przykłady — `podaj` (kierunek zwrotny)

Polszczyzna ma synkretyzm (jedna forma = wiele przypadków) i homografię (jedna
forma = wiele lematów), więc `podaj` zwraca **listę** analiz:

```python
from polish_inflection import podaj

podaj("jednostki")
# [Analiza(lemat='jednostka', przypadek='gen', liczba='sg', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='nom', liczba='pl', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='acc', liczba='pl', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='voc', liczba='pl', rodzaj='f')]

podaj("jednostki", liczba="pl")   # zawężenie do liczby mnogiej
```

`Analiza` to lekki `NamedTuple`: `(lemat, przypadek, liczba, rodzaj)`.

### Pytania przypadkowe (`pytania`)

Warstwa czytająca się jak zdanie: funkcje nazwane pytaniami przypadków. Zakładają
wyraz w mianowniku, zgadują liczbę i zwracają żądany przypadek:

```python
from polish_inflection import kogo_czego, komu_czemu, podstawowa_forma

kogo_czego("wydział")     # "wydziału"    (dopełniacz l.poj.)
kogo_czego("wydziały")    # "wydziałów"   (liczba zgadnięta z mianownika)
komu_czemu("jednostka")   # "jednostce"

# operacja odwrotna: dowolna forma -> forma podstawowa (lemat)
podstawowa_forma("wydziałów")   # "wydział"
```

Kanoniczne: `kogo_czego`, `komu_czemu`, `kogo_co`, `z_kim_z_czym`, `o_kim_o_czym`
(+ aliasy `komu`/`czemu`/`z_kim`/`z_czym`/`o_kim`/`o_czym` w `polish_inflection.pytania`).
Domyślnie przy braku formy zwracają wejściowy wyraz (passthrough — pod UI).
Pełny opis: [`docs/api.md`](docs/api.md).

Zgoda liczebnikowa — poprawna forma rzeczownika przy liczbie (`odmiana_liczebnikowa`):

```python
from polish_inflection import odmiana_liczebnikowa, NARZĘDNIK

odmiana_liczebnikowa("wydział", 1)             # "wydział"
odmiana_liczebnikowa("wydział", 2)             # "wydziały"
odmiana_liczebnikowa("wydział", 5)             # "wydziałów"
odmiana_liczebnikowa("wydział", 5, NARZĘDNIK)  # "wydziałami"
f"{5} {odmiana_liczebnikowa('wydział', 5)}"    # "5 wydziałów"
```

Zwraca **sam rzeczownik** (liczebnik słownie nie jest generowany). W przeciwieństwie
do `gettext`/`ngettext` nie musisz wpisywać form ręcznie i działa w każdym przypadku,
nie tylko w mianowniku.

### Odmiana przymiotnika (`odmien_przymiotnik`)

Przymiotniki odmieniamy **regułą**, nie indeksem — ich deklinacja jest regularna,
więc nie zajmują miejsca w słowniku (zero przyrostu danych). Zwalidowane przeciw
pełnemu SGJP: l.poj. 99,9%.

```python
from polish_inflection import odmien_przymiotnik

odmien_przymiotnik("lubelski", "gen", "m")        # "lubelskiego"
odmien_przymiotnik("medyczny", "gen", "f")        # "medycznej"
odmien_przymiotnik("stosowany", "loc", "n")       # "stosowanym"
```

`lemat` to mianownik l.poj. rodzaju męskiego (forma słownikowa); `rodzaj` to
rodzaj słowa określanego (`m`/`f`/`n`, jak zwraca `podaj`).

### Odmiana nazw wielowyrazowych (`odmien_fraze`)

Odmiana wielowyrazowych **nazw własnych instytucji** — odmienia rzeczownik-głowę
i uzgadniające się przymiotniki, a dopełniaczowe dopełnienie zamraża:

```python
from polish_inflection import odmien_fraze

odmien_fraze("Uniwersytet Lubelski", "gen")            # "Uniwersytetu Lubelskiego"
odmien_fraze("Akademia Medyczna", "loc")               # "Akademii Medycznej"
odmien_fraze("Instytut Technologii Stosowanej", "gen") # "Instytutu Technologii Stosowanej"
odmien_fraze("Uniwersytet im. Marii Curie", "gen")     # "Uniwersytetu im. Marii Curie"
```

Parser jest heurystyczny (pod nazwy własne): wykrywa głowę, uzgadnia przymiotniki,
zamraża ogon od pierwszego dopełnienia zależnego lub markera `im.`. Nieusuwalne
dwuznaczności (np. „Instytut Polski" = przymiotnik czy dopełniacz „Polski"?)
domyślnie zamraża; w warstwie aplikacji warto mieć override na wyjątki.

### Homografy rodzajowe

Niektóre słowa to dwa wyrazy o tej samej pisowni — np. `profesor`: **męski**
(odmienny: `profesora`) i **żeński** nieodmienny (`profesor`, jak „pani profesor").
Domyślnie `odmien` wybiera formę odmienioną; możesz też wymusić rodzaj:

```python
from polish_inflection import odmien, DOPEŁNIACZ, MĘSKI, ŻEŃSKI

odmien("profesor", DOPEŁNIACZ)                 # "profesora"  (domyślnie odmieniona)
odmien("profesor", DOPEŁNIACZ, rodzaj=ŻEŃSKI)  # "profesor"   (żeński nieodmienny)
odmien("profesor", DOPEŁNIACZ, rodzaj=MĘSKI)   # "profesora"
```

### Stałe

Przypadki: `MIANOWNIK`, `DOPEŁNIACZ`, `CELOWNIK`, `BIERNIK`, `NARZĘDNIK`,
`MIEJSCOWNIK`, `WOŁACZ`. Liczby: `POJEDYNCZA`, `MNOGA` (domyślnie `POJEDYNCZA`).
Rodzaje: `MĘSKI`, `ŻEŃSKI`, `NIJAKI`. Sentinele `default`: `TEN_SAM_WYRAZ`
(passthrough) i `RAISES` (wyjątek).

### Źródło danych i atrybucja

Dane fleksyjne pochodzą ze **Słownika gramatycznego języka polskiego (SGJP)**,
w wersji przypiętej i zwendorowanej w repozytorium (patrz `data/sgjp/`).
Zbudowane indeksy pokrywają 223 748 lematów / ~3,86 mln rekordów form i ważą
łącznie ~49 MB (`odmien.marisa` ≈ 24 MB, `podaj.marisa` ≈ 25 MB).

> Copyright © 2007–2026 Marcin Woliński, Zbigniew Bronk, Włodzimierz
> Gruszczyński, Witold Kieraś, Zygmunt Saloni, Danuta Skowrońska, Robert Wołosz.

SGJP jest udostępniany na licencji 2-clause BSD. Strona licencyjna:
<https://morfeusz.sgjp.pl/doc/license/en>. Pełny tekst i szczegóły atrybucji —
patrz [`NOTICE.md`](NOTICE.md) oraz `data/sgjp/LICENSE.sgjp`.

### Licencja

Dwie warstwy, jawnie rozdzielone:

- **Kod pakietu** — BSD-2-Clause, © Michał Pasternak (plik [`LICENSE`](LICENSE)).
- **Dane SGJP** — BSD-2-Clause, © autorzy wymienieni wyżej. Redystrybucja jest
  dozwolona pod warunkiem zachowania noty copyright, tekstu licencji i atrybucji
  (szczegóły w [`NOTICE.md`](NOTICE.md)).

### Ograniczenia (v1)

- Tylko **rzeczowniki**. Bez czasowników, przymiotników, liczebników.
- Bez guessera słów spoza słownika i bez analizy biegnącego tekstu
  (segmentacji/tokenizacji) — świadome YAGNI.
- Zakres: 7 przypadków × 2 liczby, oba kierunki (`odmien` / `podaj`).

---

## 🇬🇧 English version

### Purpose

Turn `wydział` into `wydziału` (genitive), `wydziałowi` (dative), `wydziałów`
(genitive plural) — programmatically, without keeping inflected forms by hand.
`polish-inflection` declines Polish **nouns** across **7 cases × 2 numbers** in
both directions:

- generation: `lemma + case + number → form` (`odmien`);
- analysis (reverse): `form → [analyses]` (`podaj`).

### Why — a gap in the ecosystem

There was no lightweight, data-only, deployment-friendly way to decline Polish
nouns by case:

- **gettext / plural forms** solve a *different* problem — picking a variant by
  **number** (`nplurals`), not declension by **case**. gettext has no concept of
  grammatical case and cannot decline a noun.
- **Morfeusz 2** is the canonical Polish morphological analyzer and generator,
  but ships a native C++ engine + SWIG bindings + a compiled dictionary of tens
  of MB. Overkill and a container-deployment headache. Here there is no engine,
  no SWIG and no dictionary compilation — just data and `pip install`.
- **pymorphy2 / pymorphy3** cover only Russian and Ukrainian — not Polish.
- **inflection / inflect / pyinflect** — English only.

Core idea: take the SGJP **data** (`form / lemma / tag` triples), drop the
**engine**. The set of forms is closed and fully enumerated — we generate
nothing at runtime, we only index and look up.

### Installation

```bash
pip install polish-inflection
```

The only runtime dependency is `marisa-trie` — a compiled C++ extension that
ships prebuilt binary wheels (Linux/macOS/Windows, cp39–cp313), so `pip install`
needs no compiler and no build tooling. The wheel ships prebuilt `.marisa`
indices — no SGJP required. The reader uses **mmap**: import does not load the
dictionary into RAM, and a single lookup pages in only O(word length) nodes
(~1 µs, measured RSS overhead ~1.5 MB instead of ~23 MB for a full load). The
indices cover 223,748 lemmas / ~3.86M form records and weigh ~49 MB total
(`odmien.marisa` ≈ 24 MB, `podaj.marisa` ≈ 25 MB).

### Examples — `odmien`

```python
from polish_inflection import odmien, DOPEŁNIACZ, MNOGA

odmien("wydział", DOPEŁNIACZ)          # -> "wydziału"
odmien("wydział", DOPEŁNIACZ, MNOGA)   # -> "wydziałów"
```

Out-of-dictionary behaviour is controlled by `default`:

```python
from polish_inflection import (
    odmien, odmien_lub_none, odmien_lub_wyraz, BrakOdmiany, DOPEŁNIACZ,
)

odmien("wydział", DOPEŁNIACZ)                 # "wydziału"
odmien("qwerty", DOPEŁNIACZ)                  # raises BrakOdmiany
odmien_lub_none("qwerty", DOPEŁNIACZ)         # None
odmien_lub_wyraz("qwerty", DOPEŁNIACZ)        # "qwerty"  (passthrough)
odmien("qwerty", DOPEŁNIACZ, default="—")     # "—"       (any fallback)
```

`odmien_warianty` returns all valid forms in a slot (variants).

### Examples — `podaj` (reverse direction)

Polish has syncretism (one form = many cases) and homography (one form = many
lemmas), so `podaj` returns a **list** of analyses:

```python
from polish_inflection import podaj

podaj("jednostki")
# [Analiza(lemat='jednostka', przypadek='gen', liczba='sg', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='nom', liczba='pl', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='acc', liczba='pl', rodzaj='f'),
#  Analiza(lemat='jednostka', przypadek='voc', liczba='pl', rodzaj='f')]

podaj("jednostki", liczba="pl")   # narrow to plural
```

`Analiza` is a lightweight `NamedTuple`: `(lemat, przypadek, liczba, rodzaj)`.
Constant names stay Polish (`MIANOWNIK`, `DOPEŁNIACZ`, …, `POJEDYNCZA`, `MNOGA`)
and map to SGJP tags (`nom`, `gen`, …, `sg`, `pl`).

### Case-question helpers (`pytania`)

An ergonomic layer whose functions are named after each case's Polish question.
They assume the input word is nominative, infer its number, and return the
requested case; `podstawowa_forma` does the reverse (any form → lemma):

```python
from polish_inflection import kogo_czego, komu_czemu, podstawowa_forma

kogo_czego("wydział")     # "wydziału"    (genitive sg)
kogo_czego("wydziały")    # "wydziałów"   (number inferred from the nominative)
komu_czemu("jednostka")   # "jednostce"
podstawowa_forma("wydziałów")   # "wydział"   (base/dictionary form)
```

Canonical names: `kogo_czego`, `komu_czemu`, `kogo_co`, `z_kim_z_czym`,
`o_kim_o_czym` (plus aliases in `polish_inflection.pytania`). On a miss they
return the input word by default (UI-friendly passthrough). Full reference:
[`docs/api.md`](docs/api.md).

Numeral agreement — the correct noun form for a count (`odmiana_liczebnikowa`):

```python
from polish_inflection import odmiana_liczebnikowa, NARZĘDNIK

odmiana_liczebnikowa("wydział", 1)             # "wydział"
odmiana_liczebnikowa("wydział", 2)             # "wydziały"
odmiana_liczebnikowa("wydział", 5)             # "wydziałów"
odmiana_liczebnikowa("wydział", 5, NARZĘDNIK)  # "wydziałami"
```

Returns just the **noun** (the numeral word isn't generated). Unlike
`gettext`/`ngettext` you don't hand-write the forms, and it works in every case,
not only the nominative.

### Data source and attribution

The inflectional data comes from the **Grammatical Dictionary of Polish (SGJP)**,
pinned and vendored in this repository (see `data/sgjp/`).

> Copyright © 2007–2026 Marcin Woliński, Zbigniew Bronk, Włodzimierz
> Gruszczyński, Witold Kieraś, Zygmunt Saloni, Danuta Skowrońska, Robert Wołosz.

SGJP is distributed under the 2-clause BSD license. License page:
<https://morfeusz.sgjp.pl/doc/license/en>. Full text and attribution details are
in [`NOTICE.md`](NOTICE.md) and `data/sgjp/LICENSE.sgjp`.

### License

Two clearly separated layers:

- **Package code** — BSD-2-Clause, © Michał Pasternak (see [`LICENSE`](LICENSE)).
- **SGJP data** — BSD-2-Clause, © the authors listed above. Redistribution is
  permitted provided the copyright notice, license text and attribution are
  retained (details in [`NOTICE.md`](NOTICE.md)).

### Limitations (v1)

- **Nouns only.** No verbs, adjectives or numerals.
- No out-of-dictionary guesser and no running-text analysis
  (segmentation/tokenization) — deliberate YAGNI.
- Scope: 7 cases × 2 numbers, both directions (`odmien` / `podaj`).
