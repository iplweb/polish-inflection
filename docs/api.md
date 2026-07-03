# API — polish-inflection

Pełny opis publicznego API. Wszystkie nazwy z sekcji „top-level" importujesz
wprost: `from polish_inflection import odmien, kogo_czego, ...`.

---

## Odmiana — `odmien`

```python
odmien(wyraz, przypadek, liczba=POJEDYNCZA, *, default=RAISES) -> str | None
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

`Analiza` to `NamedTuple`: `(lemat, przypadek, liczba, rodzaj)`.

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

Reguła (rzeczowniki nie-męskoosobowe):

| count | mianownik/biernik frazy | przypadki zależne (D/C/N/Ms) |
|---|---|---|
| 1 | l.poj. (`wydział`) | l.poj. (`wydziałem`) |
| końcówka 2–4 (nie 12–14) | l.mn., zgoda (`wydziały`) | l.mn. w tym przypadku (`wydziałami`) |
| reszta (0, 5–21, 12–14, …) | dopełniacz l.mn., rząd (`wydziałów`) | l.mn. w tym przypadku (`wydziałami`) |

Ograniczenie v1: rzeczowniki **męskoosobowe** (m1: `profesorowie` / `pięciu
profesorów`) mają odmienny rząd i nie są objęte tą regułą. `default` jak wyżej.

---

## Stałe i sentinele

| Nazwa | Wartość / znaczenie |
|---|---|
| `MIANOWNIK, DOPEŁNIACZ, CELOWNIK, BIERNIK, NARZĘDNIK, MIEJSCOWNIK, WOŁACZ` | tagi przypadków (`"nom".."voc"`) |
| `POJEDYNCZA, MNOGA` | liczba (`"sg"`, `"pl"`) |
| `PRZYPADKI, LICZBY` | krotki wszystkich powyższych |
| `TEN_SAM_WYRAZ` | sentinel `default=` → passthrough wejścia |
| `RAISES` | sentinel `default=` → rzuć `BrakOdmiany` |

## Wyjątki

- `BrakOdmiany(KeyError)` — brak formy, gdy `default=RAISES` (lub domyślnie w `odmien`).
