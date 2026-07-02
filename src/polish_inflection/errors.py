"""Typy wyników i wyjątki publicznego API."""

from __future__ import annotations

from typing import NamedTuple


class Analiza(NamedTuple):
    """Pojedyncza analiza morfologiczna formy (kierunek zwrotny ``podaj``)."""

    lemat: str
    przypadek: str  # jedna ze stałych PRZYPADKI: "nom".."voc"
    liczba: str  # "sg" / "pl"
    rodzaj: str  # tag rodzaju SGJP: "m1","m2","m3","f","n","ncol",...


class BrakOdmiany(KeyError):
    """Brak formy dla (wyraz, przypadek, liczba) i nie podano ``default``.

    Dziedziczy po ``KeyError`` — bo to w istocie brak klucza w słowniku form.
    """
