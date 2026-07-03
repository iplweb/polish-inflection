"""Zgoda liczebnikowa: poprawna forma rzeczownika przy dowolnej liczbie.

Uruchom:  python examples/06_liczebnikowa.py
"""

from polish_inflection import NARZĘDNIK, odmiana_liczebnikowa

if __name__ == "__main__":
    print("Rzeczownik przy liczbie (mianownik frazy):")
    for n in (0, 1, 2, 3, 4, 5, 11, 12, 21, 22, 25, 102):
        print(f"  {n:>3} {odmiana_liczebnikowa('wydział', n)}")

    print("\nW przypadku zależnym (narzędnik) — 'z N wydziałami':")
    for n in (1, 2, 5, 12):
        print(f"  z {n} {odmiana_liczebnikowa('wydział', n, NARZĘDNIK)}")

    print("\nInne rzeczowniki:")
    for wyraz in ("jednostka", "klinika", "instytut"):
        formy = [f"{n} {odmiana_liczebnikowa(wyraz, n)}" for n in (1, 2, 5)]
        print("  " + "  |  ".join(formy))
