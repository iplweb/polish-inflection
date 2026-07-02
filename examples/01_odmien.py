"""Podstawowa odmiana rzeczownika przez przypadki (kierunek generacji).

Uruchom:  python examples/01_odmien.py
"""

from polish_inflection import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    NARZĘDNIK,
    POJEDYNCZA,
    WOŁACZ,
    odmien,
)

PRZYPADKI = [
    ("mianownik  (kto? co?)", MIANOWNIK),
    ("dopełniacz (kogo? czego?)", DOPEŁNIACZ),
    ("celownik   (komu? czemu?)", CELOWNIK),
    ("biernik    (kogo? co?)", BIERNIK),
    ("narzędnik  (z kim? z czym?)", NARZĘDNIK),
    ("miejscownik(o kim? o czym?)", MIEJSCOWNIK),
    ("wołacz     (o!)", WOŁACZ),
]


def wypisz_tabele(wyraz: str) -> None:
    print(f"\nOdmiana wyrazu: {wyraz!r}")
    print(f"{'przypadek':30} {'poj.':16} mnoga")
    print("-" * 60)
    for etykieta, przypadek in PRZYPADKI:
        poj = odmien(wyraz, przypadek, POJEDYNCZA)
        mn = odmien(wyraz, przypadek, MNOGA)
        print(f"{etykieta:30} {poj:16} {mn}")


if __name__ == "__main__":
    for wyraz in ("wydział", "jednostka", "instytut"):
        wypisz_tabele(wyraz)

    print("\nSzybkie pojedyncze wywołania:")
    print("  odmien('wydział', DOPEŁNIACZ)        =", odmien("wydział", DOPEŁNIACZ))
    print("  odmien('wydział', DOPEŁNIACZ, MNOGA) =", odmien("wydział", DOPEŁNIACZ, MNOGA))
