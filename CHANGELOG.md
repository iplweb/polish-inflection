# Changelog

Wszystkie istotne zmiany w `polish-inflection`. Format wzorowany na
[Keep a Changelog](https://keepachangelog.com/pl/1.1.0/); wersjonowanie wg
[SemVer](https://semver.org/lang/pl/).

Wydania na GitHubie: <https://github.com/iplweb/polish-inflection/releases> ·
PyPI: <https://pypi.org/project/polish-inflection/>

## [Nieopublikowane]

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

[Nieopublikowane]: https://github.com/iplweb/polish-inflection/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/iplweb/polish-inflection/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/iplweb/polish-inflection/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/iplweb/polish-inflection/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/iplweb/polish-inflection/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/iplweb/polish-inflection/releases/tag/v0.1.0
