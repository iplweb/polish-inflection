# polish-inflection-data

Dane SGJP dla [`polish-inflection`](https://pypi.org/project/polish-inflection/) —
tylko zbudowane artefakty, zero logiki.

Zawartość (`polish_inflection_data/data/`):

- `odmien.marisa` / `podaj.marisa` — indeksy odmiany i analizy zwrotnej
  **rzeczowników**.
- `przymiotniki.marisa` — zbiór baz deklinacyjnych przymiotników/imiesłowów
  (leksykalny grunt rozpoznawania).
- `BUILD_INFO.json` — metadane buildu (edycja SGJP, schemat, rozmiary).

Nie instaluj tego pakietu ręcznie — ciągnie go `polish-inflection` jako zależność.

## Wersjonowanie

Wersja pakietu = **edycja słownika SGJP** (kalendarzowo `YYYY.M.D`, np. `2026.6.28`
dla SGJP `20260628`). Nowa edycja SGJP → nowe wydanie **tego** pakietu, bez ruszania
kodu `polish-inflection`. Sufiks `.postN` przy przebudowie tych samych danych po
zmianie schematu artefaktów.

## Licencja

- **Kod pakietu** (trywialny `__init__.py`) — BSD-2-Clause, © Michał Pasternak.
- **Dane SGJP** — BSD-2-Clause, © autorzy SGJP. Nota licencyjna i atrybucja jadą
  w pakiecie (`LICENSE.sgjp`, `NOTICE.md`). Źródło: <https://morfeusz.sgjp.pl/>.
