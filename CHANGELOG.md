# Changelog

Wszystkie istotne zmiany w `polish-inflection`. Format wzorowany na
[Keep a Changelog](https://keepachangelog.com/pl/1.1.0/); wersjonowanie wg
[SemVer](https://semver.org/lang/pl/).

Wydania na GitHubie: <https://github.com/iplweb/polish-inflection/releases> ·
PyPI: <https://pypi.org/project/polish-inflection/>

## [Nieopublikowane]

## [0.7.3] — 2026-07-03

### Dodano
- **`odmien_fraze`: koordynacja PRZECINKOWA głów.** Nazwy typu „Katedra, Zakład i
  Klinika Chirurgii" odmieniają wszystkie głowy → `"Katedry, Zakładu i Kliniki
  Chirurgii"`. Końcowe przecinki są oddzielane od rdzenia tokenu (analiza) i
  doklejane z powrotem (wynik), więc „Katedra," jest poprawnie rozpoznana jako głowa.

### Poprawiono
- **`odmien_fraze`: dopełnienie dopełniaczowe będące homografem mianownika l.mn.**
  („Matematyki" = dop. l.poj. / mian. l.mn. od „matematyka") nie jest już brane za
  głowę skoordynowaną. Wykrywanie głów po głowie wymaga mianownika w LICZBIE frazy
  (l.poj.), więc „Wydział Matematyki i Informatyki" pozostaje `"Wydziału Matematyki
  i Informatyki"` (ogon zamrożony), a prawdziwe głowy w mianowniku l.poj. („Klinika",
  „Zakład") odmieniają się.

## [0.7.2] — 2026-07-03

### Poprawiono
- **`odmien_fraze`: głowy SKOORDYNOWANE spójnikiem** („i"/„oraz"). W nazwach typu
  „Katedra i Zakład Hematologii Onkologicznej" druga głowa („Zakład", też w
  mianowniku) zostawała nieodmieniona, bo pętla łamała się na spójniku. Teraz obie
  głowy się odmieniają → `"Katedry i Zakładu Hematologii Onkologicznej"` (ogon
  dopełniaczowy „Hematologii Onkologicznej" nadal zamrożony).
- **`odmien_fraze`: wielkoliterowy rzeczownik pospolity przesłaniany przez nazwisko-
  homograf.** „Klinika" nie była kandydatem na głowę, bo `podaj("Klinika")` zwracał
  najpierw nazwisko „Klinik" (acc/gen, bez mianownika) i przesłaniał pospolite
  „klinika" (nom). Wybór głowy szuka teraz mianownika po wszystkich wariantach
  wielkości liter → `"Klinika i Katedra Chirurgii"` = `"Kliniki i Katedry Chirurgii"`.
- **Pakowanie: sdist pakietu kodu nie wiezie już `data-package/` (~49 MB `.marisa`).**
  Hatchlingowy `include` był addytywny do całego drzewa VCS; `only-include` ogranicza
  twardo. Sdist kodu spadł z ~28 MB do ~68 KB (wheel był poprawny od 0.7.0).

## [0.7.1] — 2026-07-03

### Poprawiono
- **`odmien_fraze`: przymiotnik PRZED głową odmienia się** (homograf rodzajowy).
  `odmien_fraze("Polski Instytut Weterynaryjny", DOPEŁNIACZ)` daje
  `"Polskiego Instytutu Weterynaryjnego"` (było: cała fraza zamrożona, bo „Polski"
  było błędnie brane za rzeczownik-głowę „Polska"). Wybór głowy jest teraz
  LEKSYKALNY (`podaj_przymiotnik`) — token będący prawdziwym przymiotnikiem nie
  zostaje głową, gdy obok jest rzeczownik; przydawka przed głową ma pierwszeństwo
  nad zamrożeniem na dopełniaczu. `"Instytut Polski"` → `"Instytutu Polski"`
  zachowane (pozycja rozstrzyga homograf: przed głową = przymiotnik, po głowie z
  czytaniem dopełniacza = nazwa własna).

### Dodano
- `examples/07_przymiotniki.py`, `examples/08_frazy.py` — przykłady dla
  `odmien_przymiotnik`/`podaj_przymiotnik` i `odmien_fraze`.

## [0.7.0] — 2026-07-03

### Zmieniono (BREAKING)
- **Dane SGJP wydzielone do osobnego pakietu `polish-inflection-data`** (twarda
  zależność, wersjonowana wg edycji SGJP `YYYY.M.D`). Wheel `polish-inflection`
  spada z ~28 MB do ~35 KB — wydania kodu nie re-publikują już ~49 MB słownika, a
  nowa edycja SGJP wymaga wydania tylko pakietu danych. `pip install
  polish-inflection` ciągnie komplet jak dawniej. Strażnik schematu (`SCHEMA`)
  pilnuje zgodności formatu artefaktów.
- **`zgadnij_przymiotnik` → `podaj_przymiotnik`** (rename) i **rozpoznawanie stało
  się LEKSYKALNE**: kandydaci na bazę są filtrowani zbiorem prawdziwych baz
  deklinacyjnych z SGJP (`przymiotniki.marisa`, 0,5 MB — przymiotniki + imiesłowy
  `pact`/`ppas`, wszystkie stopnie). Koniec nadgeneracji: `podaj_przymiotnik("Michała")`
  → `[]` (było zmyślone `michały`). Nazwa `zgadnij_przymiotnik` usunięta.

### Dodano
- **Pakiet `polish-inflection-data`** — indeksy rzeczowników (`odmien`/`podaj`) +
  zbiór baz przymiotników, z notą licencyjną SGJP w wheelu.

## [0.6.0] — 2026-07-03

### Dodano
- **`zgadnij_przymiotnik(forma)`** — kierunek zwrotny dla przymiotnika (forma →
  `[Analiza]`), odwrotność `odmien_przymiotnik`. **Regułowe zgadywanie** bez
  indeksu (odwrócenie paradygmatu przez generate-and-test), więc zero przyrostu
  danych. Nazwa mówi wprost, że to heurystyka: rozpoznaje *kształt* i może
  nadgenerować analizy dla form, które tylko wyglądają jak przymiotnik (np.
  rzeczownik `dupa` → zgadnięty `dupy`). Zwalidowane przeciw SGJP (recall l.poj.
  ~99,6%). `podaj` (rzeczowniki, leksykalne) pozostaje rozdzielone — **NIC nie
  robi z przymiotnikami**, żeby nie zatruwać pewnych wyników zgadywankami.

### Poprawiono
- **`odmien_fraze`: frazy pisane w całości małą literą traktowane jak zwykłe
  rzeczowniki**, nie nazwy własne. Wcześniej homograf nazwy miejscowej z
  gazeteera SGJP mógł „ukraść" rolę głowy i wymusić kapitalizację —
  `odmien_fraze("dupa wołowa", DOPEŁNIACZ)` dawało błędne `"dupa Wołowa"` (wieś
  Wołowo), teraz poprawnie `"dupy wołowej"` (małą literą). Do gazeteera schodzimy
  tylko, gdy inaczej słowa nie znajdziemy.
- **`odmien_fraze`: zgoda przymiotnika w liczbie mnogiej.** Rozpoznanie lematu
  przydawki jest teraz niezależne od docelowej liczby (przez `zgadnij_przymiotnik`),
  więc `odmien_fraze("Uniwersytet Lubelski", DOPEŁNIACZ, MNOGA)` daje
  `"Uniwersytetów Lubelskich"` (było `"Uniwersytetów Lubelski"` — przymiotnik
  zostawał w l.poj.).

## [0.5.2] — 2026-07-03

### Poprawiono
- **`odmien_fraze`: zgoda przymiotnika w bierniku wg żywotności głowy.** Biernik
  l.poj. przymiotnika zależy od żywotności rzeczownika-głowy (żywotny: biernik =
  dopełniacz — `nowego pracownika`; nieżywotny: biernik = mianownik — `Uniwersytet
  Lubelski`). Żywotność jest czytana z form głowy.

## [0.5.1] — 2026-07-03

### Poprawiono
- **`odmien_fraze` zamraża ogon tylko na dopełniaczu, nie na bierniku.** Homografy
  przymiotników odmiejscowych (nom/acc/voc, np. `polski`, `Lubelski`) muszą się
  odmieniać jak przydawki, a nie zamrażać — zamrażamy dopiero na kanonicznym
  sygnale dopełnienia zależnego (dopełniacz).

### Dodano
- **Alias `odmien_rzeczownik`** dla `odmien` (symetria z `odmien_przymiotnik` /
  `odmien_fraze`) — ta sama funkcja.

## [0.5.0] — 2026-07-03

### Dodano
- **`odmien_przymiotnik(lemat, przypadek, rodzaj, liczba=POJEDYNCZA)`** — regułowa
  odmiana przymiotnika (stopień równy), bez indeksu SGJP: deklinacja przymiotnika
  jest regularna, więc generujemy ją regułą (kilka KB kodu zamiast +46 MB danych).
  Zwalidowane przeciw SGJP: l.poj. 99,9%, l.mn. 99,6%.
- **`odmien_fraze(fraza, przypadek, liczba=POJEDYNCZA)`** — odmiana wielowyrazowych
  **nazw własnych instytucji** (heurystyczny parser): wykrywa rzeczownik-głowę,
  uzgadnia przymiotniki, zamraża ogon od pierwszego dopełnienia zależnego lub
  markera `im.`.

## [0.4.1] — 2026-07-03

### Dodano
- **Marker PEP 561 `py.typed`** — mypy/pyright u użytkowników uwzględniają teraz
  adnotacje typów pakietu (wcześniej były ignorowane mimo pełnego otypowania).

### Zmieniono
- **`odmiana_liczebnikowa` obsługuje ułamki** — wartość ułamkowa (`2.5`) daje
  dopełniacz l.poj. (`2,5 wydziału`), niezależnie od przypadka frazy, zamiast
  cichego zaokrąglenia przez `int()` do `2` (`wydziały`). Wartości całkowite
  zapisane jako `float` (`2.0`) nadal działają jak `int`.

### Poprawiono
- **`wersja_sgjp` czyta wersję niezależnie od kolejności nagłówka SGJP** —
  wspólny iterator nagłówka respektuje blok `#<COPYRIGHT>…#</COPYRIGHT>` (którego
  treść nie ma prefiksu `#`), więc przestawienie `#!DICT-ID` za blok licencji nie
  da już po cichu `wersja_sgjp: null` w `BUILD_INFO.json`.

## [0.4.0] — 2026-07-03

### Dodano
- **`odmien(..., rodzaj=…)`** — opcjonalne wymuszenie rodzaju dla homografów
  rodzajowych (`profesor`: `rodzaj=MĘSKI` → `profesora`, `rodzaj=ŻEŃSKI` →
  `profesor`). Stałe rodzaju: **`MĘSKI` / `ŻEŃSKI` / `NIJAKI`** (`RODZAJE`).

### Zmieniono
- **Domyślny wybór głównej formy w `odmien`**: przy kilku formach w slocie
  (homograf/oboczność) preferujemy formę **odmienioną** (różną od lematu) nad
  tożsamościową — `odmien("profesor", DOPEŁNIACZ)` → `"profesora"` bez podawania
  rodzaju.
- **`Analiza.rodzaj` (z `podaj`) zwężony do trzech rodzajów** — `MĘSKI`/`ŻEŃSKI`/
  `NIJAKI` (`"m"`/`"f"`/`"n"`). Podtypy rodzaju męskiego SGJP (męskoosobowy itd.)
  są ukryte; potrzebny wewnętrznie podtyp męskoosobowy (rząd liczebnika,
  `dwóch studentów` vs `dwa stoły`) jest wykrywany automatycznie i niewidoczny.
  (Zmiana łamiąca dla kodu polegającego na `"m1"`/`"m2"`/`"m3"` w `Analiza.rodzaj`.)

## [0.3.1] — 2026-07-03

### Poprawiono
- **Homograf rodzajowy w `odmiana_liczebnikowa`.** Dla lematu będącego
  homografem rodzajów (np. `profesor` = męskoosobowy + żeński nieodmienny)
  funkcja zwracała formę alfabetycznie pierwszą (`profesor`) zamiast poprawnej
  męskoosobowej. Teraz forma jest dobierana zgodnie z wykrytym rodzajem:
  `odmiana_liczebnikowa("profesor", 5)` → `"profesorów"` (było `"profesor"`).

## [0.3.0] — 2026-07-03

### Dodano
- **`odmiana_liczebnikowa(wyraz, count, przypadek=MIANOWNIK)`** — poprawna forma
  rzeczownika przy liczbie (zgoda liczebnikowa: 1 / 2–4 / 5+, wyjątek 12–14;
  rząd dopełniaczem w mianowniku/bierniku; zgoda l.mn. w przypadkach zależnych).
  Zwraca sam rzeczownik — liczebnik słownie doklejasz sam.
- **Automatyczne wykrywanie rodzaju męskoosobowego (m1)** z danych SGJP —
  `odmiana_liczebnikowa("student", 2)` → `"studentów"` („dwóch studentów").
- `examples/06_liczebnikowa.py`, sekcja w README (PL+EN), wpis w `docs/api.md`.

## [0.2.0] — 2026-07-02

### Dodano
- **API pytań przypadkowych** (`pytania`): `kogo_czego`, `komu_czemu`, `kogo_co`,
  `z_kim_z_czym`, `o_kim_o_czym` (+ aliasy `komu`/`czemu`/`z_kim`/`z_czym`/
  `o_kim`/`o_czym` w `polish_inflection.pytania`). Zakładają mianownik, zgadują
  liczbę, zwracają żądany przypadek. Domyślnie passthrough (pod UI).
- **`podstawowa_forma(wyraz)`** — dowolna forma fleksyjna → lemat (forma
  słownikowa).
- **Sentinel `RAISES`** dla `default=` (opt-in wyjątek `BrakOdmiany`);
  ujednolicony wewnętrzny sentinel `odmien` (bez zmian obserwowalnych).
- `docs/api.md` (pełna referencja API), `examples/05_pytania.py`.

## [0.1.0] — 2026-07-02

### Dodano
- Pierwsze wydanie. Odmiana polskich **rzeczowników** przez 7 przypadków × 2
  liczby, w obie strony:
  - **`odmien(wyraz, przypadek, liczba=POJEDYNCZA, *, default=...)`** oraz
    `odmien_lub_none`, `odmien_lub_wyraz`, `odmien_warianty`;
  - **`podaj(wyraz, liczba=None)`** — analiza zwrotna (forma → `[Analiza]`).
- Nazwane stałe przypadków/liczby, sentinel `TEN_SAM_WYRAZ`, wyjątek
  `BrakOdmiany`.
- Dane ze **Słownika gramatycznego języka polskiego (SGJP)** (pin 20260628,
  git-lfs), kompaktowy indeks **marisa-trie** (mmap, ~1 µs/lookup, ~49 MB).
  Instalacja bez kompilatora (gotowe binarne wheele), zero zależności od Django.
- Pipeline BUILD (`polish-inflection-build build` / `refresh-sgjp`), CI
  (Python 3.9–3.13), pre-commit, README PL→EN, licencje (kod BSD-2 + dane SGJP).

[Nieopublikowane]: https://github.com/iplweb/polish-inflection/compare/v0.7.3...HEAD
[0.7.3]: https://github.com/iplweb/polish-inflection/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/iplweb/polish-inflection/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/iplweb/polish-inflection/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/iplweb/polish-inflection/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/iplweb/polish-inflection/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/iplweb/polish-inflection/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/iplweb/polish-inflection/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/iplweb/polish-inflection/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/iplweb/polish-inflection/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/iplweb/polish-inflection/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/iplweb/polish-inflection/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/iplweb/polish-inflection/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/iplweb/polish-inflection/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/iplweb/polish-inflection/releases/tag/v0.1.0
