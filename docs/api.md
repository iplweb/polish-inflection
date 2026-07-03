# API — polish-inflection

Pełny opis publicznego API. Wszystkie nazwy z sekcji „top-level" importujesz
wprost: `from polish_inflection import odmien, kogo_czego, ...`.

---

## Odmiana — `odmien`

```python
odmien(wyraz, przypadek, liczba=POJEDYNCZA, *, rodzaj=None, default=RAISES) -> str | None
```

Zwraca główną formę `wyraz` w danym przypadku i liczbie. `wyraz` to lemat
(forma słownikowa, mianownik l.poj.).

Zachowanie przy braku formy (słowo spoza słownika lub liczba nieistniejąca dla
lematu) steruje `default`:

| `default` | wynik przy braku |
|---|---|
| `RAISES` (domyślnie) | rzuca `BrakOdmiany` |
| `TEN_SAM_WYRAZ` | zwraca wejściowy `wyraz` |
| `None` | zwraca `None` |
| dowolna wartość | zwraca tę wartość |

```python
odmien("wydział", DOPEŁNIACZ)          # "wydziału"
odmien("wydział", DOPEŁNIACZ, MNOGA)   # "wydziałów"
odmien("qwerty", DOPEŁNIACZ, default=None)  # None
```

### Homografy rodzajowe i `rodzaj=`

Niektóre słowa to homografy rodzajów — jedno pisownia, dwa różne wyrazy, np.
`profesor`: **męski** (odmienny: `profesora`) i **żeński** nieodmienny (`profesor`,
jak „pani profesor"). Slot zawiera wtedy obie formy.

- **Domyślnie** (`rodzaj=None`) `odmien` nie wykrywa rodzaju — przy kilku formach
  w slocie wybiera **odmienioną** (różną od lematu) zamiast tożsamościowej. Dzięki
  temu `odmien("profesor", DOPEŁNIACZ)` → `"profesora"` „za darmo".
- **Opcjonalnie** możesz wymusić rodzaj stałą `MĘSKI` / `ŻEŃSKI` / `NIJAKI`. Gdy
  słownik nie ma formy tego rodzaju w slocie — traktujemy to jak brak (`default`).

```python
from polish_inflection import odmien, DOPEŁNIACZ, MNOGA, MĘSKI, ŻEŃSKI

odmien("profesor", DOPEŁNIACZ)                 # "profesora"  (domyślnie: odmieniona)
odmien("profesor", DOPEŁNIACZ, rodzaj=ŻEŃSKI)  # "profesor"   (żeński nieodmienny)
odmien("profesor", DOPEŁNIACZ, MNOGA, rodzaj=MĘSKI)  # "profesorów"
```

Warianty skrótowe i oboczności:

| funkcja | znaczenie |
|---|---|
| `odmien_lub_none(wyraz, przypadek, liczba=POJEDYNCZA)` | jak `odmien(..., default=None)` |
| `odmien_lub_wyraz(wyraz, przypadek, liczba=POJEDYNCZA)` | jak `odmien(..., default=TEN_SAM_WYRAZ)` |
| `odmien_warianty(wyraz, przypadek, liczba=POJEDYNCZA) -> list[str]` | wszystkie poprawne formy w slocie (oboczności); `[]` gdy brak |

---

## Analiza zwrotna — `podaj`

```python
podaj(wyraz, liczba=None) -> list[Analiza]
```

Forma → lista analiz. Zwraca listę, bo polszczyzna ma synkretyzm (jedna forma =
wiele przypadków) i homografię (jedna forma = wiele lematów). Uwzględnia formy
deprecjatywne (`depr`). Opcjonalny `liczba` (`POJEDYNCZA`/`MNOGA`) zawęża.
Nieznana forma → `[]`.

`Analiza` to `NamedTuple`: `(lemat, przypadek, liczba, rodzaj)`. `rodzaj` jest
publiczny — `MĘSKI` (`"m"`) / `ŻEŃSKI` (`"f"`) / `NIJAKI` (`"n"`).

```python
podaj("jednostki")
# [Analiza('jednostka','gen','sg','f'), Analiza('jednostka','nom','pl','f'),
#  Analiza('jednostka','acc','pl','f'), Analiza('jednostka','voc','pl','f')]
```

---

## Pytania przypadkowe — `pytania`

Ergonomiczna warstwa: funkcje nazwane pytaniami przypadków. **Zakładają, że
wejściowy wyraz jest w mianowniku**, zgadują jego liczbę i zwracają żądany
przypadek w tej liczbie.

```python
kogo_czego("wydział")     # "wydziału"    (mianownik l.poj. -> dopełniacz l.poj.)
kogo_czego("wydziały")    # "wydziałów"   (liczba zgadnięta z mianownika)
kogo_czego("wydział", liczba=MNOGA)  # "wydziałów"  (liczba wymuszona)
```

Sygnatura (identyczna dla wszystkich): `f(wyraz, *, liczba=None, default=TEN_SAM_WYRAZ)`.
`liczba=None` → zgadnij z mianownika; `default` domyślnie **passthrough**
(`TEN_SAM_WYRAZ`) — pod UI, żeby nie wywalać widoku; opcje jak w `odmien`
(`None` / wartość / `RAISES`).

### Funkcje i aliasy

| Przypadek | Nazwa kanoniczna (top-level) | Aliasy (`polish_inflection.pytania`) |
|---|---|---|
| dopełniacz | `kogo_czego` | — |
| celownik | `komu_czemu` | `komu`, `czemu` |
| biernik | `kogo_co` | — |
| narzędnik | `z_kim_z_czym` | `z_kim`, `z_czym` |
| miejscownik | `o_kim_o_czym` | `o_kim`, `o_czym` |

Aliasy to **te same obiekty funkcji** (`komu is komu_czemu`). Kanoniczne nazwy są
na top-level; pełny zestaw aliasów importujesz z `polish_inflection.pytania`:

```python
from polish_inflection.pytania import komu, z_kim, o_czym
```

Świadomie NIE ma `kto_co` (dla wyrazu w mianowniku to tożsamość), ani aliasów
`kogo`/`co` (niejednoznaczne między przypadkami), ani wołacza (brak wyróżniającego
pytania — użyj `odmien(x, WOŁACZ)`).

### Zachowania brzegowe

- **Wejście oblique** (nie mianownik, np. `"wydziałów"`): best-effort — liczba
  brana z faktycznej analizy (l.mn. zachowana).
- **Homograf / niejednoznaczność liczby** (nieodmienne): wybór jednej analizy
  deterministycznie, przy remisie preferowana l.poj.
- **Wyraz nieznany**: obsługa przez `default` (domyślnie passthrough).

---

## Forma podstawowa — `podstawowa_forma`

```python
podstawowa_forma(wyraz, *, default=TEN_SAM_WYRAZ) -> str | None
```

Operacja odwrotna: dowolna forma fleksyjna → lemat (forma słownikowa).

```python
podstawowa_forma("wydziałów")   # "wydział"
podstawowa_forma("jednostce")   # "jednostka"
podstawowa_forma("drzwiach")    # "drzwi"   (plurale tantum — lemat l.mn.)
```

Lemat SGJP to mianownik l.poj. dla rzeczowników policzalnych; dla plurale tantum
(np. `drzwi`, `spodnie`) lemat jest l.mnogiej. Homografia → pierwszy lemat
deterministycznie. `default` jak wyżej.

---

## Zgoda liczebnikowa — `odmiana_liczebnikowa`

```python
odmiana_liczebnikowa(wyraz, count, przypadek=MIANOWNIK, *, default=TEN_SAM_WYRAZ) -> str | None
```

Zwraca **sam rzeczownik** w formie narzuconej przez liczbę `count`, w zadanym
przypadku frazy. Liczebnik słownie NIE jest generowany — numer doklejasz sam:
`f"{count} {odmiana_liczebnikowa(wyraz, count)}"`.

```python
odmiana_liczebnikowa("wydział", 1)              # "wydział"
odmiana_liczebnikowa("wydział", 2)              # "wydziały"
odmiana_liczebnikowa("wydział", 5)              # "wydziałów"
odmiana_liczebnikowa("wydział", 5, NARZĘDNIK)   # "wydziałami"
f"{5} {odmiana_liczebnikowa('wydział', 5)}"     # "5 wydziałów"
```

Reguła (dla rzeczowników **nie-męskoosobowych**):

| count | mianownik/biernik frazy | przypadki zależne (D/C/N/Ms) |
|---|---|---|
| 1 | l.poj. (`wydział`) | l.poj. (`wydziałem`) |
| końcówka 2–4 (nie 12–14) | l.mn., zgoda (`wydziały`) | l.mn. w tym przypadku (`wydziałami`) |
| reszta (0, 5–21, 12–14, …) | dopełniacz l.mn., rząd (`wydziałów`) | l.mn. w tym przypadku (`wydziałami`) |

Rzeczowniki **męskoosobowe** (np. `student`, `profesor`) mają odmienny rząd —
mianownik/biernik rządzą dopełniaczem l.mn. już od 2 (`2 → "studentów"` = „dwóch
studentów"). To rozróżnienie (podtyp rodzaju męskiego) jest **wykrywane
wewnętrznie** z danych SGJP i niewidoczne w API — nie musisz go podawać ani znać;
publicznie rodzaj to zawsze `MĘSKI`/`ŻEŃSKI`/`NIJAKI`. `default` jak wyżej.

---

## Przymiotniki — `odmien_przymiotnik` / `zgadnij_przymiotnik`

Przymiotniki są **regułowe, bez indeksu** — ich deklinacja jest regularna, więc
generujemy ją i rozpoznajemy z reguł (zero przyrostu danych SGJP).

```python
odmien_przymiotnik(lemat, przypadek, rodzaj, liczba=POJEDYNCZA, *, default=TEN_SAM_WYRAZ) -> str | None
```

Odmienia przymiotnik. `lemat` to mianownik l.poj. rodzaju męskiego (forma
słownikowa, np. `lubelski`, `medyczny`); `rodzaj` to rodzaj słowa określanego
(`MĘSKI`/`ŻEŃSKI`/`NIJAKI`). Zwalidowane przeciw SGJP: l.poj. 99,9%, l.mn. 99,6%.

```python
odmien_przymiotnik("lubelski", DOPEŁNIACZ, MĘSKI)     # "lubelskiego"
odmien_przymiotnik("medyczny", DOPEŁNIACZ, ŻEŃSKI)    # "medycznej"
odmien_przymiotnik("medyczny", DOPEŁNIACZ, ŻEŃSKI, MNOGA)  # "medycznych"
```

```python
zgadnij_przymiotnik(forma) -> list[Analiza]
```

Kierunek zwrotny (forma → `[Analiza]`), odwrotność `odmien_przymiotnik`. Zwraca
wszystkie `(lemat, przypadek, liczba, rodzaj)`, dla których reguły generują `forma`
(synkretyzm → wiele analiz). `lemat` zawsze małą literą; niewrażliwe na wielkość
liter. Nieznana / nieprzymiotnikowa forma → `[]`.

```python
zgadnij_przymiotnik("wołowa")
# [Analiza('wołowy','nom','sg','f'), Analiza('wołowy','voc','sg','f')]
```

**To ZGADYWANIE, nie leksykalny lookup.** Rozpoznaje *kształt*, nie sprawdza czy
lemat istnieje w słowniku — może więc nadgenerować analizy dla form, które tylko
wyglądają jak przymiotnik (rzeczownik `dupa` → zgadnięty `dupy`). Dlatego `podaj`
(rzeczowniki, leksykalne) i `zgadnij_przymiotnik` (przymiotniki, regułowe) są
**rozdzielone** — `podaj` nic nie robi z przymiotnikami. Rozstrzyganie
rzeczownik-vs-przymiotnik łączysz sam (np. `podaj` najpierw, `zgadnij_przymiotnik`
gdy pusto).

---

## Nazwy wielowyrazowe — `odmien_fraze`

```python
odmien_fraze(fraza, przypadek, liczba=POJEDYNCZA, *, default=TEN_SAM_WYRAZ) -> str | None
```

Odmienia wielowyrazową **nazwę własną instytucji**: heurystyczny parser wykrywa
rzeczownik-głowę, uzgadnia z nią przymiotniki (także w l.mn.), a od pierwszego
dopełnienia zależnego (dopełniacz) lub markera `im.` zamraża ogon.

```python
odmien_fraze("Uniwersytet Lubelski", DOPEŁNIACZ)          # "Uniwersytetu Lubelskiego"
odmien_fraze("Uniwersytet Lubelski", DOPEŁNIACZ, MNOGA)   # "Uniwersytetów Lubelskich"
odmien_fraze("Instytut Fizyki", DOPEŁNIACZ)               # "Instytutu Fizyki"  (ogon zamrożony)
```

**Reguła wielkości liter.** Fraza w całości małą literą jest traktowana jak
**zwykłe rzeczowniki**, nie nazwy własne: parser nie sięga do gazeteera nazw
miejscowych (żaden homograf nazwy wsi nie ukradnie roli głowy) i nie kapitalizuje
wyniku. Do gazeteera schodzimy tylko, gdy inaczej głowy nie znajdziemy.

```python
odmien_fraze("dupa wołowa", DOPEŁNIACZ)   # "dupy wołowej"  (nie "dupa Wołowa")
```

---

## Stałe i sentinele

| Nazwa | Wartość / znaczenie |
|---|---|
| `MIANOWNIK, DOPEŁNIACZ, CELOWNIK, BIERNIK, NARZĘDNIK, MIEJSCOWNIK, WOŁACZ` | tagi przypadków (`"nom".."voc"`) |
| `POJEDYNCZA, MNOGA` | liczba (`"sg"`, `"pl"`) |
| `MĘSKI, ŻEŃSKI, NIJAKI` | rodzaj (`"m"`, `"f"`, `"n"`) — do `odmien(rodzaj=…)` i `Analiza.rodzaj` |
| `PRZYPADKI, LICZBY, RODZAJE` | krotki wszystkich powyższych |
| `TEN_SAM_WYRAZ` | sentinel `default=` → passthrough wejścia |
| `RAISES` | sentinel `default=` → rzuć `BrakOdmiany` |

Uwaga: rodzaj męski w SGJP dzieli się wewnętrznie na podtypy (męskoosobowy,
męskozwierzęcy, męskorzeczowy) — potrzebne np. do poprawnego rządu liczebnika
(`dwóch studentów` vs `dwa stoły`). To rozróżnienie jest ukryte; publicznie widać
tylko trzy rodzaje.

## Wyjątki

- `BrakOdmiany(KeyError)` — brak formy, gdy `default=RAISES` (lub domyślnie w `odmien`).
