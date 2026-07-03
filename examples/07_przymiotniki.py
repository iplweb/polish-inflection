"""Przymiotniki: odmiana regułowa (forward) i analiza zwrotna leksykalna (reverse).

Odmiana przymiotnika jest regułowa (bez indeksu), a rozpoznawanie zwrotne
(`podaj_przymiotnik`) jest LEKSYKALNE — filtruje kandydatów zbiorem prawdziwych
baz z SGJP, więc forma rzeczownika (np. "Michała") nie udaje przymiotnika.

Uruchom:  python examples/07_przymiotniki.py
"""

from polish_inflection import (
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    MĘSKI,
    NIJAKI,
    ŻEŃSKI,
    odmien_przymiotnik,
    podaj_przymiotnik,
)

if __name__ == "__main__":
    print("Odmiana przymiotnika (lemat = mianownik l.poj. rodzaju męskiego):")
    print(f"  lubelski (M, dop.):  {odmien_przymiotnik('lubelski', DOPEŁNIACZ, MĘSKI)}")
    print(f"  lubelski (Ż, dop.):  {odmien_przymiotnik('lubelski', DOPEŁNIACZ, ŻEŃSKI)}")
    print(f"  medyczny (N, msc.):  {odmien_przymiotnik('medyczny', MIEJSCOWNIK, NIJAKI)}")

    print("\nZgoda z rodzajem głowy (ten sam przypadek, różny rodzaj):")
    for rodzaj, etykieta in ((MĘSKI, "M"), (ŻEŃSKI, "Ż"), (NIJAKI, "N")):
        print(f"  {etykieta}: {odmien_przymiotnik('główny', MIANOWNIK, rodzaj)}")

    # "m1" (męskoosobowy) to zaawansowany podtyp — NIE publiczna stała, ale
    # przyjmowany, bo l.mn. mianownik zależy od męskoosobowości ("lekarscy" vs
    # "lekarskie"). Publiczne API to MĘSKI/ŻEŃSKI/NIJAKI.
    print("\nLiczba mnoga — męskoosobowa (m1) vs niemęskoosobowa:")
    print(f"  m1 (mian.):  {odmien_przymiotnik('lekarski', MIANOWNIK, 'm1', MNOGA)}")
    print(f"  Ż  (mian.):  {odmien_przymiotnik('lekarski', MIANOWNIK, ŻEŃSKI, MNOGA)}")

    print("\nAnaliza zwrotna (forma -> baza), LEKSYKALNA:")
    for forma in ("wołowa", "lekarskiego", "wyższej"):
        analizy = podaj_przymiotnik(forma)
        opis = ", ".join(f"{a.lemat}/{a.przypadek}/{a.rodzaj}" for a in analizy)
        print(f"  {forma:14} -> {opis}")

    print("\nGrunt leksykalny: formy rzeczowników NIE są przymiotnikami:")
    for forma in ("Michała", "dupa", "kobieta"):
        print(f"  {forma:10} -> {podaj_przymiotnik(forma)}   (regułowe zgadywanie dałoby atrapę)")
