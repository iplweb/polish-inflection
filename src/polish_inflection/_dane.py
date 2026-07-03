"""Locator pakietu danych ``polish-inflection-data`` + strażnik schematu.

Dane (indeksy SGJP) mieszkają w OSOBNYM pakiecie ``polish_inflection_data``
(twarda zależność), żeby wydania kodu nie re-publikowały ~49 MB słownika. Ten
moduł jest jedynym miejscem, które sięga po pakiet danych — ``core`` i
``przymiotnik`` proszą go o katalog artefaktów.

Strażnik schematu to guard RUNTIME (nie instalacyjny): dolny pin w zależności
przepuści przyszły pakiet z wyższym ``SCHEMA`` przy instalacji, ale przy pierwszym
użyciu rzucimy czytelny błąd zamiast dawać śmieci z niezgodnego formatu.
"""

from __future__ import annotations

from pathlib import Path

#: Wersja formatu artefaktów .marisa, jakiej oczekuje kod. MUSI zgadzać się z
#: ``polish_inflection_data.SCHEMA`` (i ``build.SCHEMA``, którym stemplowany jest build).
_SCHEMA = 1


def katalog() -> Path:
    """Zwróć katalog artefaktów z zainstalowanego ``polish-inflection-data``.

    Rzuca ``RuntimeError`` z czytelną instrukcją, gdy pakietu danych brak lub jego
    schemat nie zgadza się z oczekiwaniem kodu.
    """
    try:
        import polish_inflection_data as dane
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Brak pakietu danych 'polish-inflection-data'. "
            "Zainstaluj: pip install polish-inflection-data"
        ) from e
    if getattr(dane, "SCHEMA", None) != _SCHEMA:
        raise RuntimeError(
            f"Niezgodny schemat polish-inflection-data: kod oczekuje {_SCHEMA}, "
            f"pakiet ma {getattr(dane, 'SCHEMA', None)}. Zaktualizuj polish-inflection-data."
        )
    return dane.KATALOG
