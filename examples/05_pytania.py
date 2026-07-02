"""API pytań przypadkowych: funkcje nazwane pytaniami + forma podstawowa.

Uruchom:  python examples/05_pytania.py
"""

from polish_inflection import (
    kogo_co,
    kogo_czego,
    komu_czemu,
    o_kim_o_czym,
    podstawowa_forma,
    z_kim_z_czym,
)

if __name__ == "__main__":
    print("Pytania przypadkowe (zakładają wyraz w mianowniku):\n")
    for wyraz in ("wydział", "jednostka", "klinika"):
        print(f"[{wyraz}]")
        print("  kogo? czego?      ->", kogo_czego(wyraz))
        print("  komu? czemu?      ->", komu_czemu(wyraz))
        print("  kogo? co?         ->", kogo_co(wyraz))
        print("  (z) kim? (z) czym?->", z_kim_z_czym(wyraz))
        print("  o kim? o czym?    ->", o_kim_o_czym(wyraz))
        print()

    print("Liczba zgadywana z mianownika (l.mn. na wejściu -> l.mn. na wyjściu):")
    print("  kogo_czego('wydziały') ->", kogo_czego("wydziały"))
    print("  kogo_czego('wydział', liczba='pl') ->", kogo_czego("wydział", liczba="pl"))
    print()

    print("Forma podstawowa (dowolna forma -> lemat):")
    for forma in ("wydziałów", "jednostce", "kliniką", "drzwiach"):
        print(f"  podstawowa_forma({forma!r}) -> {podstawowa_forma(forma)!r}")
