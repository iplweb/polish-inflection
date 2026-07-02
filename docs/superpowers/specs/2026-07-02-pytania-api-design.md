# pytania — API pytań przypadkowych + forma podstawowa (spec)

- **Data:** 2026-07-02
- **Status:** projekt zaakceptowany (brainstorming), przed implementacją
- **Autor:** Michał Pasternak (+ Claude)
- **Wersja docelowa pakietu:** 0.2.0 (minor — nowe funkcje, bez zmian łamiących)

---

## 1. Cel

Ergonomiczna warstwa nad istniejącym `odmien`/`podaj`: funkcje nazwane
**pytaniami przypadków**, czytające się jak zdanie w kodzie konsumenta (BPP):

```python
from polish_inflection import kogo_czego, komu_czemu

kogo_czego("wydział")     # "wydziału"   (mianownik l.poj. -> dopełniacz l.poj.)
kogo_czego("wydziały")    # "wydziałów"  (mianownik l.mn. -> dopełniacz l.mn.)
komu_czemu(nazwa_typu)    # np. "wydziałowi"
```

Plus operacja odwrotna — sprowadzenie dowolnej formy do **formy podstawowej**
(lematu = mianownik l.poj.):

```python
from polish_inflection import podstawowa_forma

podstawowa_forma("wydziałów")   # "wydział"
podstawowa_forma("jednostce")   # "jednostka"
```

Zero nowych danych — to cienka warstwa kompozycji `podaj` + `odmien`.

---

## 2. Zakres

**W zakresie (v0.2.0):**
- 5 funkcji pytań przypadkowych (dopełniacz, celownik, biernik, narzędnik,
  miejscownik) + aliasy.
- `podstawowa_forma` — lematyzacja (dowolna forma → mianownik l.poj.).
- Nowy sentinel `RAISES` (opcja „rzuć wyjątek" dla `default=`).
- Ujednolicenie wewnętrznego sentinela `odmien` na publiczny `RAISES`
  (zachowanie bez zmian).
- `docs/api.md` — pełny opis API (w tym tabela aliasów).

**Poza zakresem:**
- Mianownik jako funkcja pytaniowa (`kto_co`) — dla wyrazu zakładanego w
  mianowniku to tożsamość, bez sensu. Świadomie pominięty.
- Wołacz w zestawie pytań (brak wyróżniającego pytania „o!"). Dostępny przez
  `odmien(x, WOŁACZ)`.
- Guesser/analiza tekstu — jak w rdzeniu, YAGNI.

---

## 3. Funkcje pytaniowe

Każda odpowiada jednemu przypadkowi docelowemu i **zakłada, że wejściowy wyraz
jest w mianowniku**. Zgaduje liczbę z mianownika wejścia i zwraca żądany
przypadek w tej liczbie.

| Przypadek | Nazwa kanoniczna | Aliasy |
|---|---|---|
| dopełniacz (gen) | `kogo_czego` | — |
| celownik (dat) | `komu_czemu` | `komu`, `czemu` |
| biernik (acc) | `kogo_co` | — |
| narzędnik (inst) | `z_kim_z_czym` | `z_kim`, `z_czym` |
| miejscownik (loc) | `o_kim_o_czym` | `o_kim`, `o_czym` |

Aliasy to **te same obiekty funkcji** związane pod wieloma nazwami (nie kopie).
Świadomie NIE ma aliasów `kogo`, `co` (niejednoznaczne: dopełniacz vs biernik,
mianownik vs biernik) ani `kto`, `czego`.

### 3.1 Sygnatura (identyczna dla wszystkich pięciu)

```python
def kogo_czego(wyraz: str, *, liczba: str | None = None, default=TEN_SAM_WYRAZ):
    """Dopełniacz wyrazu (zakładanego w mianowniku).

    liczba=None  -> zgadnij z mianownika wejścia; POJEDYNCZA/MNOGA wymusza.
    default:
      TEN_SAM_WYRAZ (domyślnie) -> przy braku zwróć wejściowy `wyraz` (passthrough)
      None                      -> zwróć None
      RAISES                    -> rzuć BrakOdmiany
      <cokolwiek>               -> zwróć tę wartość
    """
```

### 3.2 Mechanizm

KLUCZOWA zasada: **lemat i liczbę bierzemy z JEDNEJ, tej samej analizy** —
nigdy nie mieszamy lematu z jednej analizy z liczbą z innej (inaczej dla
homografów międzyleksemowych powstaje niespójna para → zły wynik lub cichy
fallback).

```python
def _pytanie(wyraz, przypadek, liczba, default):
    analizy = podaj(wyraz)
    if not analizy:                         # wyraz nieznany
        return _rozwiaz_brak(wyraz, default)
    nom = [a for a in analizy if a.przypadek == MIANOWNIK]
    kandydaci = nom or analizy              # preferuj mianownik; inaczej best-effort
    # jedna analiza deterministycznie: alfabetycznie po lemacie, przy remisie sg < pl
    wybrana = min(kandydaci, key=lambda a: (a.lemat, 0 if a.liczba == POJEDYNCZA else 1))
    liczba_efektywna = liczba if liczba is not None else wybrana.liczba
    forma = odmien(wybrana.lemat, przypadek, liczba_efektywna, default=None)
    if forma is None:                       # slot nie istnieje (np. brak danej liczby)
        return _rozwiaz_brak(wyraz, default)
    return forma
```

Konsekwencje (wszystkie zamierzone i pokryte testami):
- **Mianownik l.poj./l.mn.** → liczba z wybranej analizy mianownikowej;
  `kogo_czego("wydziały")` → l.mn.
- **Nieodmienne / niejednoznaczne co do liczby** (np. *attaché* mian. l.poj. =
  l.mn.) → klucz sortowania preferuje `sg` → **POJEDYNCZA**.
- **Homograf międzyleksemowy** (forma = mian. l.poj. lematu B i mian. l.mn.
  lematu A, np. plurale tantum): `min` wybiera JEDEN leksem i JEGO liczbę →
  `odmien` dostaje spójną parę (bez cichego błędu z B1).
- **Wejście oblique** (nie mianownik, np. *wydziałów* = dop. l.mn.): brak `nom`
  → `kandydaci = analizy` → bierzemy liczbę z wybranej analizy (l.mn.
  zachowana, nie degradowana do l.poj.). To best-effort poza kontraktem
  „wejście w mianowniku" — udokumentowane.

---

## 4. `podstawowa_forma`

Operacja **odwrotna** do funkcji pytaniowych: przyjmuje wyraz w DOWOLNYM
przypadku i zwraca **formę podstawową** (lemat = mianownik l.poj.).

```python
def podstawowa_forma(wyraz: str, *, default=TEN_SAM_WYRAZ) -> str | None:
    """Forma podstawowa (lemat SGJP) dowolnej formy fleksyjnej.

    Zwraca lemat = forma słownikowa: mianownik l.poj. dla rzeczowników
    policzalnych; dla plurale tantum (np. `drzwi`, `spodnie`) lemat jest
    l.MNOGIEJ (nie ma l.poj.). Homografia -> pierwszy lemat deterministycznie.
    `default` jak w funkcjach pytaniowych.
    """
```

Mechanizm: `analizy = podaj(wyraz)`; brak → `_rozwiaz_brak(wyraz, default)`;
inaczej zwróć `sorted(a.lemat for a in analizy)[0]`. (Lemat SGJP to forma
słownikowa.)

Uwaga: nie ma parametru `liczba`. `podstawowa_forma("wydział")` (już mianownik
l.poj.) → `"wydział"` (idempotencja). `podstawowa_forma("drzwiach")` → `"drzwi"`
(plurale tantum — lemat l.mn.; testowane, by zachowanie było przypięte).

---

## 5. Sentinel `RAISES` i rozwiązywanie braku

Nowa stała w `const.py`:

```python
class _Raises:
    __slots__ = ()
    def __repr__(self): return "RAISES"
RAISES = _Raises()   # default=RAISES -> rzuć BrakOdmiany
```

Wspólny helper (w `core.py`, importowany przez `pytania`):

```python
def _rozwiaz_brak(wyraz, default):
    if default is RAISES:
        raise BrakOdmiany(wyraz)
    if default is TEN_SAM_WYRAZ:
        return wyraz
    return default        # None lub dowolna wartość
```

### 5.1 Ujednolicenie `odmien`

`odmien` używa dziś wewnętrznego `_BRAK`. Zamieniamy TYLKO nazwę sentinela na
publiczny `RAISES` (`default=RAISES` jako wartość domyślna). `odmien` zachowuje
**własny inline `raise`** z dotychczasowym payloadem `BrakOdmiany((wyraz,
przypadek, liczba))` — NIE deleguje do `_rozwiaz_brak` (który rzuca
`BrakOdmiany(wyraz)`), żeby nie zmienić `exc.args`. Zachowanie obserwowalne
`odmien` bez zmian; to czysto wewnętrzna zmiana nazwy.

(Funkcje `pytania` oraz `podstawowa_forma` używają `_rozwiaz_brak`, którego
`BrakOdmiany(wyraz)` niesie tylko wyraz — to nowe API, spójne wewnętrznie.)

Różnica domyślnych: `odmien` domyślnie **RAISES** (twarde), funkcje pytaniowe i
`podstawowa_forma` domyślnie **TEN_SAM_WYRAZ** (miękkie/passthrough — pod UI).

---

## 6. Namespace i eksport

- Nowy moduł `src/polish_inflection/pytania.py` — wszystkie funkcje + aliasy.
- **Top-level** (`polish_inflection`): kanoniczne `kogo_czego`, `komu_czemu`,
  `kogo_co`, `z_kim_z_czym`, `o_kim_o_czym`, `podstawowa_forma`, oraz `RAISES`.
- **Pełny zestaw aliasów** (`komu`, `czemu`, `z_kim`, `z_czym`, `o_kim`,
  `o_czym`) dostępny z `polish_inflection.pytania`.
- `__all__` zaktualizowane w obu miejscach.

---

## 7. Testy (TDD)

`tests/test_pytania.py`:
- Pytania na słowach domenowych: `kogo_czego("wydział")=="wydziału"`,
  `kogo_czego("wydziały")=="wydziałów"`, `komu_czemu("jednostka")=="jednostce"`,
  `kogo_co("jednostka")=="jednostkę"`, `z_kim_z_czym("klinika")=="kliniką"`,
  `o_kim_o_czym("wydział")=="wydziale"`.
- Zgadywanie liczby: wejście l.mn. → wynik l.mn.; `liczba=MNOGA` wymusza.
- Aliasy: `komu is komu_czemu` itd. (ten sam obiekt) i równość wyników.
- `default`: passthrough (domyślnie), `None`, wartość, `RAISES`→`BrakOdmiany`.
- **Wejście oblique** (best-effort, S4): `kogo_czego("wydziałów")` zachowuje
  l.mn. (nie degraduje do l.poj.).
- **Nieznany wyraz** (S1): nie rzuca `IndexError`, idzie przez `default`.
- `podstawowa_forma`: `"wydziałów"->"wydział"`, `"jednostce"->"jednostka"`,
  idempotencja na mianowniku, nieznane→`default`, **plurale tantum**
  `"drzwiach"->"drzwi"` (lemat l.mn. — przypięte, S2).
- Round-trip: `kogo_czego(podstawowa_forma(x))` spójne dla próbki.
- Testy fixture-owe (jak w `test_core`) — bez realnych 42 MB. Fixtura
  domenowa dostaje kilka form pluralia-tantum (`drzwi`) do testu S2/charakteryzacji.

Testy charakteryzacyjne na realnych danych (guarded) — dopisać kilka asertów w
`test_characterization.py` (opcjonalnie).

---

## 8. Dokumentacja

- **`docs/api.md`** — nowy plik: pełne API rdzenia (`odmien` + rodzina, `podaj`,
  `Analiza`, `BrakOdmiany`, stałe, `TEN_SAM_WYRAZ`, `RAISES`) ORAZ warstwy
  `pytania` z tabelą aliasów i przykładami.
- **README** — krótka sekcja „Pytania przypadkowe / Case questions" (PL+EN) z
  2–3 przykładami i wskazaniem na `docs/api.md`.
- Wersja pakietu → **0.2.0** (`pyproject.toml` + `__init__.__version__`).

---

## 9. Kryteria sukcesu

- `kogo_czego("wydział")=="wydziału"`, `kogo_czego("wydziały")=="wydziałów"`.
- `podstawowa_forma("wydziałów")=="wydział"`.
- Aliasy są tym samym obiektem; passthrough domyślny; `RAISES` rzuca.
- Zielone testy + lint; `pip install` nadal działa; zero nowych zależności.
- README + `docs/api.md` opisują nowe funkcje.
