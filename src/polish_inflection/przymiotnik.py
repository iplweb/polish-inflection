"""Regułowa odmiana przymiotników (stopień równy) — bez indeksu, czysto z reguł.

Odmiana przymiotnika w polszczyźnie jest REGULARNA (zamknięty system paradygmatów
twardo-/miękko-/welarnotematowych), inaczej niż leksykalna odmiana rzeczownika —
dlatego nie trzymamy przymiotników w indeksie SGJP (to +46 MB), tylko generujemy
je regułą (kilka KB kodu). Zwalidowane przeciw SGJP: l.poj. 99,9% zgodności.

Wejście ``lemat`` to mianownik l.poj. rodzaju męskiego (forma słownikowa, np.
``lubelski``, ``medyczny``, ``stosowany``). ``rodzaj`` to rodzaj GŁOWY, którą
przymiotnik określa (zgoda) — przyjmujemy publiczne stałe ``MĘSKI``/``ŻEŃSKI``/
``NIJAKI``; zgrubny ``MĘSKI`` traktujemy jako nieżywotny (nazwy instytucji).
"""

from __future__ import annotations

from .const import (
    BIERNIK,
    CELOWNIK,
    DOPEŁNIACZ,
    MIANOWNIK,
    MIEJSCOWNIK,
    MNOGA,
    MĘSKI,
    NARZĘDNIK,
    NIJAKI,
    POJEDYNCZA,
    PRZYPADKI,
    TEN_SAM_WYRAZ,
    WOŁACZ,
    ŻEŃSKI,
)
from .core import _rozwiaz_brak
from .errors import Analiza

__all__ = ["odmien_przymiotnik", "zgadnij_przymiotnik"]

# Podtypy rodzaju męskiego (m1 męskoosobowy, m2 męskozwierzęcy) są w SGJP, ale
# NIE mają publicznych stałych (biblioteka wystawia tylko MĘSKI/ŻEŃSKI/NIJAKI).
# Przyjmujemy je jako opcjonalne wejście dla zaawansowanych wywołań.
_M1 = "m1"
_M2 = "m2"

# Abstrakcyjne końcówki l.poj.: (grupa_rodzaju, przypadek) -> końcówka.
# grupa_rodzaju: MĘSKI (m1/m2/m3 wspólne poza biernikiem), ŻEŃSKI, NIJAKI.
_SG = {
    (MĘSKI, MIANOWNIK): "y",
    (MĘSKI, DOPEŁNIACZ): "ego",
    (MĘSKI, CELOWNIK): "emu",
    (MĘSKI, NARZĘDNIK): "ym",
    (MĘSKI, MIEJSCOWNIK): "ym",
    (MĘSKI, WOŁACZ): "y",
    (ŻEŃSKI, MIANOWNIK): "a",
    (ŻEŃSKI, DOPEŁNIACZ): "ej",
    (ŻEŃSKI, CELOWNIK): "ej",
    (ŻEŃSKI, BIERNIK): "ą",
    (ŻEŃSKI, NARZĘDNIK): "ą",
    (ŻEŃSKI, MIEJSCOWNIK): "ej",
    (ŻEŃSKI, WOŁACZ): "a",
    (NIJAKI, MIANOWNIK): "e",
    (NIJAKI, DOPEŁNIACZ): "ego",
    (NIJAKI, CELOWNIK): "emu",
    (NIJAKI, BIERNIK): "e",
    (NIJAKI, NARZĘDNIK): "ym",
    (NIJAKI, MIEJSCOWNIK): "ym",
    (NIJAKI, WOŁACZ): "e",
}

# Końcówki l.mn. NIEmęskoosobowe (m2/m3/f/n) — wspólne dla wszystkich rodzajów
# poza mianownikiem/wołaczem męskoosobowym (patrz _mn_meskoosobowy_mianownik).
_PL_NIEMESK = {
    MIANOWNIK: "e",
    DOPEŁNIACZ: "ych",
    CELOWNIK: "ym",
    BIERNIK: "e",
    NARZĘDNIK: "ymi",
    MIEJSCOWNIK: "ych",
    WOŁACZ: "e",
}

# Tablica alternacji tematu dla mianownika l.mn. MĘSKOOSOBOWEGO (m1):
# temat -> (nowa_koncowka_tematu, samogloska). Dłuższe wzorce najpierw.
_MESK_ALT = [
    ("sk", "sc", "y"),
    ("st", "śc", "i"),
    ("zk", "zc", "y"),
    ("ch", "s", "i"),
    ("sz", "s", "i"),
    ("cz", "cz", "y"),
    ("k", "c", "y"),
    ("g", "dz", "y"),
    ("r", "rz", "y"),
    ("ł", "l", "i"),
    ("t", "c", "i"),
    ("d", "dz", "i"),
    ("sł", "śl", "i"),
    ("zł", "źl", "i"),
    ("ż", "z", "i"),
    ("n", "n", "i"),
    ("ni", "ni", ""),
]


def _klasa_temat(lemat: str):
    """(klasa, temat). Klasa steruje samogłoską łączącą i/y w formach zależnych."""
    if lemat.endswith("y"):
        return "HARD", lemat[:-1]
    if lemat.endswith("i"):
        temat = lemat[:-1]
        if temat and temat[-1] in "kg":
            return "VELAR", temat
        if temat and temat[-1] == "l":
            return "LTWARDA", temat  # -li: 'l' funkcjonalnie twarde (anieli->aniela)
        return "SOFT", temat
    return None, lemat


def _sklej(klasa: str, temat: str, koncowka: str) -> str:
    if klasa == "HARD":
        return temat + koncowka
    if klasa == "LTWARDA":
        return temat + ("i" + koncowka[1:] if koncowka[0] == "y" else koncowka)
    if klasa == "VELAR":
        if koncowka[0] == "y":
            return temat + "i" + koncowka[1:]
        if koncowka[0] == "e":
            return temat + "i" + koncowka
        return temat + koncowka  # a, ą — samogłoski tylne bez zmiękczenia
    # SOFT: "i" przed każdą końcówką; y->i
    return temat + ("i" + koncowka[1:] if koncowka[0] == "y" else "i" + koncowka)


def _grupa(rodzaj: str) -> str:
    if rodzaj in (MĘSKI, _M1, _M2, "m3"):
        return MĘSKI
    if rodzaj == NIJAKI:
        return NIJAKI
    return ŻEŃSKI


def _zywotny(rodzaj: str) -> bool:
    # Zgrubne MĘSKI traktujemy jako NIEżywotne (nazwy instytucji: uniwersytet, wydział).
    return rodzaj in (_M1, _M2)


def _mn_meskoosobowy_mianownik(temat: str) -> str:
    for konc, nowy, sam in _MESK_ALT:
        if temat.endswith(konc):
            return temat[: -len(konc)] + nowy + sam
    return temat + "i"  # brak alternacji -> miękczenie samą samogłoską


def _forma_sg(klasa, temat, rodzaj, przypadek):
    grupa = _grupa(rodzaj)
    if grupa == MĘSKI and przypadek == BIERNIK:
        klucz = (MĘSKI, DOPEŁNIACZ) if _zywotny(rodzaj) else (MĘSKI, MIANOWNIK)
    else:
        klucz = (grupa, przypadek)
    konc = _SG.get(klucz)
    return _sklej(klasa, temat, konc) if konc else None


def _forma_pl(klasa, temat, rodzaj, przypadek):
    meskoosobowy = rodzaj == _M1
    if meskoosobowy and przypadek in (MIANOWNIK, WOŁACZ):
        return _mn_meskoosobowy_mianownik(temat)
    if meskoosobowy and przypadek == BIERNIK:
        konc = _PL_NIEMESK[DOPEŁNIACZ]  # biernik m1 l.mn. = dopełniacz
    else:
        konc = _PL_NIEMESK.get(przypadek)
    return _sklej(klasa, temat, konc) if konc else None


def odmien_przymiotnik(
    lemat: str,
    przypadek: str,
    rodzaj: str,
    liczba: str = POJEDYNCZA,
    *,
    default=TEN_SAM_WYRAZ,
):
    """Odmień przymiotnik ``lemat`` do (``przypadek``, ``rodzaj``, ``liczba``).

    ``lemat`` — mianownik l.poj. m (forma słownikowa). ``przypadek`` — stała
    przypadka (``DOPEŁNIACZ`` itd.). ``rodzaj`` — rodzaj głowy (``MĘSKI``/
    ``ŻEŃSKI``/``NIJAKI``; zgrubny ``MĘSKI`` = nieżywotny). Przy niepoprawnym
    wejściu stosuje ``default`` (jak reszta API).

    >>> from polish_inflection import DOPEŁNIACZ, MIEJSCOWNIK, MĘSKI, ŻEŃSKI, NIJAKI
    >>> odmien_przymiotnik("lubelski", DOPEŁNIACZ, MĘSKI)
    'lubelskiego'
    >>> odmien_przymiotnik("stosowany", DOPEŁNIACZ, ŻEŃSKI)
    'stosowanej'
    >>> odmien_przymiotnik("medyczny", MIEJSCOWNIK, NIJAKI)
    'medycznym'
    """
    klasa, temat = _klasa_temat(lemat)
    if klasa is None:
        return _rozwiaz_brak(lemat, default)
    if liczba == MNOGA:
        forma = _forma_pl(klasa, temat, rodzaj, przypadek)
    else:
        forma = _forma_sg(klasa, temat, rodzaj, przypadek)
    if forma is None:
        return _rozwiaz_brak(lemat, default)
    return forma


# ── Rozpoznawanie zwrotne (forma → lemat) ────────────────────────────────────
# Odwrotność ``odmien_przymiotnik`` BEZ indeksu SGJP: generujemy zbiór lematów-
# kandydatów z kształtu formy, po czym przez oracle (sam ``odmien_przymiotnik``)
# sprawdzamy, które sloty paradygmatu faktycznie dają tę formę. Dzięki temu
# alternacje tematu (welarne, męskoosobowe l.mn.) są obsłużone „za darmo" —
# nie parsujemy końcówek, tylko potwierdzamy generacją.

# Rodzaje do wygenerowania paradygmatu przy rozpoznawaniu: MĘSKI (nieżywotny sg +
# niemęskoosobowa l.mn.), m2 (żywotny — biernik l.poj. = dopełniacz), m1
# (męskoosobowa l.mn.: mianownik/wołacz z alternacją), oraz f/n. Wszystkie mapują
# na publiczny rodzaj (m/f/n).
_RODZAJE_ROZPOZNANIA = (
    (MĘSKI, MĘSKI),
    (_M2, MĘSKI),
    (_M1, MĘSKI),
    (ŻEŃSKI, ŻEŃSKI),
    (NIJAKI, NIJAKI),
)


def _kandydaci_lematow(forma: str):
    """Zbiór hipotetycznych lematów (mian. l.poj. m, -y/-i) dla ``forma``.

    Nadgenerowuje świadomie — fałszywe trafienia odsiewa późniejsza weryfikacja
    generacją. Pokrywa (1) proste ucięcie końcówki + doklejenie -y/-i oraz (2)
    odwrócenie alternacji tematu mianownika l.mn. męskoosobowego (sk→sc itd.).
    """
    kand = set()
    if forma[-1:] in ("y", "i"):
        kand.add(forma)  # sama forma bywa lematem (mianownik l.poj. m)
    for i in range(2, len(forma)):
        stem = forma[:i]
        kand.add(stem + "y")
        kand.add(stem + "i")
    # odwrócenie alternacji: forma na -scy/-ści/... może pochodzić od -sk/-st/...
    for konc, nowy, sam in _MESK_ALT:
        suf = nowy + sam
        if suf and forma.endswith(suf):
            baza = forma[: -len(suf)] + konc
            kand.add(baza + "i")
            kand.add(baza + "y")
    return kand


def zgadnij_przymiotnik(forma: str) -> list[Analiza]:
    """ZGADNIJ analizy przymiotnika dla ``forma`` (kierunek zwrotny) → ``[Analiza]``.

    Nazwa mówi wprost: to ZGADYWANIE regułowe, nie leksykalny lookup jak
    :func:`podaj`. Odwrotność :func:`odmien_przymiotnik`: zwraca wszystkie
    ``(lemat, przypadek, liczba, rodzaj)``, dla których reguły generują ``forma``
    (synkretyzm → wiele analiz). ``lemat`` to mianownik l.poj. rodzaju męskiego
    (forma słownikowa), zawsze małą literą; ``rodzaj`` publiczny (``MĘSKI``/
    ``ŻEŃSKI``/``NIJAKI``). Niewrażliwe na wielkość liter.

    REGUŁOWE, nie leksykalne: rozpoznaje KSZTAŁT, nie sprawdza czy lemat istnieje
    w słowniku. Dlatego NADGENERUJE analizy dla form, które tylko wyglądają jak
    przymiotnik (np. rzeczownik ``dupa`` → zgadnięty ``dupy``). ``podaj`` (rzeczo-
    wniki) i ``zgadnij_przymiotnik`` są rozdzielone celowo — ``podaj`` NIC nie robi
    z przymiotnikami; rozstrzyganie rzeczownik-vs-przymiotnik łącz sam z ``podaj``.

    >>> from polish_inflection import Analiza, MIANOWNIK, POJEDYNCZA, ŻEŃSKI
    >>> Analiza("wołowy", MIANOWNIK, POJEDYNCZA, ŻEŃSKI) in zgadnij_przymiotnik("wołowa")
    True
    """
    f = forma.lower()
    if not f:
        return []
    wynik = set()
    for lemat in _kandydaci_lematow(f):
        if _klasa_temat(lemat)[0] is None:
            continue
        for rodz_gen, rodz_pub in _RODZAJE_ROZPOZNANIA:
            for liczba in (POJEDYNCZA, MNOGA):
                for przypadek in PRZYPADKI:
                    if odmien_przymiotnik(lemat, przypadek, rodz_gen, liczba, default=None) == f:
                        wynik.add(Analiza(lemat, przypadek, liczba, rodz_pub))
    return sorted(wynik, key=lambda a: (a.liczba, a.przypadek, a.lemat, a.rodzaj))
