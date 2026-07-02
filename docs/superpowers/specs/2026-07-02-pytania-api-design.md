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

1. `analizy = podaj(wyraz)`.
2. `nom = [a for a in analizy if a.przypadek == MIANOWNIK]`.
3. Ustal liczbę:
   - `liczba` podane → użyj go;
   - inaczej z `nom`: jeśli wszystkie `nom` mają jedną liczbę → ta liczba;
     jeśli `nom` jest niejednoznaczne co do liczby (nieodmienne, np. *attaché*
     mian. l.poj. = l.mn.) → **POJEDYNCZA**;
   - brak `nom` (wejście nie jest mianownikiem, np. *jednostce*), ale wyraz
     znany → **POJEDYNCZA** (best-effort, udokumentowane);
   - wyraz nieznany → obsługa `default` (patrz 5).
4. Ustal lemat: ze zbioru `nom` (lub, gdy pusty, z wszystkich `analizy`) weź
   **pierwszy po sortowaniu** lemat (deterministycznie; homografia → pierwszy).
5. `forma = odmien(lemat, przypadek, liczba_efektywna, default=None)`;
   jeśli `None` (slot nie istnieje, np. brak żądanej liczby) → obsługa `default`.

---

## 4. `podstawowa_forma`

Operacja **odwrotna** do funkcji pytaniowych: przyjmuje wyraz w DOWOLNYM
przypadku i zwraca **formę podstawową** (lemat = mianownik l.poj.).

```python
def podstawowa_forma(wyraz: str, *, default=TEN_SAM_WYRAZ) -> str | None:
    """Forma podstawowa (mianownik l.poj., lemat) dowolnej formy fleksyjnej.

    Zawsze zwraca l.poj. (forma podstawowa kolapsuje liczbę). Homografia ->
    pierwszy lemat deterministycznie. `default` jak w funkcjach pytaniowych.
    """
```

Mechanizm: `analizy = podaj(wyraz)`; brak → obsługa `default`; inaczej zwróć
`sorted(a.lemat for a in analizy)[0]`. (Lemat SGJP JEST mianownikiem l.poj.)

Uwaga: nie ma parametru `liczba` — forma podstawowa jest z definicji l.poj.
`podstawowa_forma("wydział")` (już mianownik l.poj.) → `"wydział"` (idempotencja).

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

`odmien` używa dziś wewnętrznego `_BRAK`. Zamieniamy na publiczny `RAISES`:
- `odmien(..., default=RAISES)` staje się wartością domyślną — zachowanie
  identyczne (brak formy bez podania `default` nadal rzuca `BrakOdmiany`).
- To czysto wewnętrzna spójność; API `odmien` bez zmian obserwowalnych.

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
- `podstawowa_forma`: `"wydziałów"->"wydział"`, `"jednostce"->"jednostka"`,
  idempotencja na mianowniku, nieznane→`default`.
- Round-trip: `kogo_czego(podstawowa_forma(x))` spójne dla próbki.
- Testy fixture-owe (jak w `test_core`) — bez realnych 42 MB.

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
