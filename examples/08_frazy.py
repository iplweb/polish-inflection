"""Odmiana wielowyrazowych nazw własnych instytucji (`odmien_fraze`).

Parser heurystyczny: wykrywa rzeczownik-głowę, uzgadnia przymiotniki (także w
l.mn.), a dopełniaczowy "ogon" (dopełnienie) zamraża. Reguła wielkości liter:
fraza w CAŁOŚCI małą literą jest traktowana jak zwykłe rzeczowniki (nie nazwa
własna) — bez sięgania do gazeteera nazw miejscowych i bez kapitalizacji.

Uruchom:  python examples/08_frazy.py
"""

from polish_inflection import CELOWNIK, DOPEŁNIACZ, MIEJSCOWNIK, MNOGA, odmien_fraze

if __name__ == "__main__":
    print("Nazwy uczelni/wydziałów (rzeczownik + uzgadniający przymiotnik):")
    for fraza in ("Uniwersytet Lubelski", "Akademia Medyczna", "Politechnika Warszawska"):
        print(f"  {fraza:26} (dop.) -> {odmien_fraze(fraza, DOPEŁNIACZ)}")

    print("\nDopełniaczowy ogon zamrożony (odmienia się tylko głowa):")
    for fraza in ("Instytut Technologii Stosowanej", "Wydział Matematyki i Informatyki"):
        print(f"  {fraza:34} (dop.) -> {odmien_fraze(fraza, DOPEŁNIACZ)}")

    print("\nMarker patronatu 'im.' zamraża resztę:")
    fr = "Uniwersytet im. Marii Curie-Skłodowskiej"
    print(f"  {fr}\n    (cel.) -> {odmien_fraze(fr, CELOWNIK)}")

    print("\nLiczba mnoga — przymiotnik uzgadnia liczbę:")
    for fraza in ("Uniwersytet Lubelski", "Wydział Lekarski"):
        print(f"  {fraza:22} (dop. l.mn.) -> {odmien_fraze(fraza, DOPEŁNIACZ, MNOGA)}")

    print("\nReguła małej litery = zwykłe rzeczowniki (bez kapitalizacji):")
    for fraza in ("sala gimnastyczna", "czerwony samochód", "uniwersytet warszawski"):
        print(f"  {fraza:24} (msc.) -> {odmien_fraze(fraza, MIEJSCOWNIK)}")
