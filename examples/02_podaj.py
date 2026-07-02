"""Analiza zwrotna: forma -> lista możliwych analiz (lemat, przypadek, liczba, rodzaj).

Polszczyzna ma synkretyzm (jedna forma = wiele przypadków) i homografię
(jedna forma = wiele lematów), więc `podaj` zawsze zwraca LISTĘ.

Uruchom:  python examples/02_podaj.py
"""

from polish_inflection import MNOGA, podaj


def pokaz(forma: str, liczba=None) -> None:
    etykieta = forma if liczba is None else f"{forma} (liczba={liczba})"
    print(f"\npodaj({etykieta!r}):")
    analizy = podaj(forma, liczba=liczba)
    if not analizy:
        print("  — brak (forma spoza słownika)")
        return
    for a in analizy:
        print(
            f"  lemat={a.lemat:12} przypadek={a.przypadek:4} liczba={a.liczba:2} rodzaj={a.rodzaj}"
        )


if __name__ == "__main__":
    # 'jednostki' = dopełniacz l.poj. ORAZ mianownik/biernik/wołacz l.mn.
    pokaz("jednostki")
    # zawężenie do liczby mnogiej
    pokaz("jednostki", liczba=MNOGA)
    # 'wydział' = mianownik i biernik l.poj. (synkretyzm)
    pokaz("wydział")
    # forma nieznana
    pokaz("qwerty")
