"""polish-inflection-data — dane SGJP dla ``polish-inflection`` (tylko artefakty).

Pakiet wiezie zbudowane indeksy ``marisa-trie``:

- ``odmien.marisa`` / ``podaj.marisa`` — odmiana i analiza zwrotna RZECZOWNIKÓW,
- ``przymiotniki.marisa`` — zbiór baz deklinacyjnych przymiotników/imiesłowów
  (mianownik l.poj. rodzaju męskiego) do LEKSYKALNEGO ugruntowania rozpoznawania.

Zero logiki — czyta je kod ``polish_inflection`` (mmap). Wersja pakietu = edycja
SGJP (kalendarzowa ``YYYY.M.D``); ``.postN`` przy zmianie schematu bez zmiany SGJP.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

__all__ = ["SCHEMA", "KATALOG", "WERSJA_SGJP"]

#: Wersja formatu artefaktów .marisa (CONTRACT §D). MUSI zgadzać się z
#: ``BUILD_INFO.json['schema']`` (walidowane testem) oraz z oczekiwaniem kodu
#: (``polish_inflection._dane._SCHEMA``).
SCHEMA = 1

#: Katalog z artefaktami danych (realny ``Path`` na dysku — mmap tego wymaga).
KATALOG = Path(str(files("polish_inflection_data") / "data"))


def _build_info() -> dict:
    return json.loads((KATALOG / "BUILD_INFO.json").read_text(encoding="utf-8"))


#: Identyfikator edycji SGJP, np. ``"pl.sgjp.sgjp-20260628"`` (None gdy brak).
WERSJA_SGJP = _build_info().get("wersja_sgjp")
