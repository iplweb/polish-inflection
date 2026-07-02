"""Zachowanie przy braku formy: wyjątek, None, passthrough lub własny default.

`odmien` domyślnie RZUCA wyjątek `BrakOdmiany`, żeby brak nie przeszedł
niezauważony. Gdy wolisz miękkie zachowanie, wybierz wariant.

Uruchom:  python examples/03_fallbacki.py
"""

from polish_inflection import (
    DOPEŁNIACZ,
    TEN_SAM_WYRAZ,
    BrakOdmiany,
    odmien,
    odmien_lub_none,
    odmien_lub_wyraz,
)

NIEZNANE = "qwerty123"  # celowo spoza słownika

if __name__ == "__main__":
    # 1) domyślnie: wyjątek
    try:
        odmien(NIEZNANE, DOPEŁNIACZ)
    except BrakOdmiany:
        print("odmien(...)                -> BrakOdmiany (wyjątek)")

    # 2) None
    print("odmien_lub_none(...)       ->", odmien_lub_none(NIEZNANE, DOPEŁNIACZ))

    # 3) passthrough — zwraca wejściowy wyraz (wygodne w UI)
    print("odmien_lub_wyraz(...)      ->", odmien_lub_wyraz(NIEZNANE, DOPEŁNIACZ))

    # 4) dowolny default (parametr, jak dict.get)
    print("odmien(..., default='—')   ->", odmien(NIEZNANE, DOPEŁNIACZ, default="—"))
    print("odmien(..., default=None)  ->", odmien(NIEZNANE, DOPEŁNIACZ, default=None))
    print(
        "odmien(..., default=TEN_SAM_WYRAZ) ->",
        odmien(NIEZNANE, DOPEŁNIACZ, default=TEN_SAM_WYRAZ),
    )

    # dla znanego wyrazu wszystkie warianty zwracają tę samą formę
    print("\nznany wyraz 'wydział':")
    print("  odmien             ->", odmien("wydział", DOPEŁNIACZ))
    print("  odmien_lub_none    ->", odmien_lub_none("wydział", DOPEŁNIACZ))
