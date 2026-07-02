"""Zastosowanie źródłowe: wstawianie nazw typów jednostek do komunikatów UI.

To jest problem, dla którego powstała biblioteka: w interfejsie nazwa typu
jednostki (wydział / klinika / instytut / …) musi pojawić się w różnych
przypadkach — "lista pracowników *wydziału*", "wybierz *jednostkę*".

Uruchom:  python examples/04_szablony_ui.py
"""

from polish_inflection import BIERNIK, DOPEŁNIACZ, MIEJSCOWNIK, odmien_lub_wyraz

TYPY = ["wydział", "klinika", "instytut", "katedra", "zakład", "koło"]


def naglowek_listy(typ: str) -> str:
    # "lista pracowników wydziału / kliniki / instytutu ..."
    return f"Lista pracowników {odmien_lub_wyraz(typ, DOPEŁNIACZ)}"


def przycisk_wyboru(typ: str) -> str:
    # "wybierz wydział / klinikę / instytut ..."
    return f"Wybierz {odmien_lub_wyraz(typ, BIERNIK)}"


def opis_lokalizacji(typ: str) -> str:
    # "informacje o wydziale / klinice / instytucie ..."
    return f"Informacje o {odmien_lub_wyraz(typ, MIEJSCOWNIK)}"


if __name__ == "__main__":
    for typ in TYPY:
        print(f"[{typ}]")
        print("  ", naglowek_listy(typ))
        print("  ", przycisk_wyboru(typ))
        print("  ", opis_lokalizacji(typ))
        print()

    # Uwaga: `odmien_lub_wyraz` gwarantuje, że nawet dla nieznanego typu
    # UI nie wywali się wyjątkiem — zostawi wyraz w formie podstawowej.
    print("[typ spoza słownika]")
    print("  ", naglowek_listy("cośtam"))
