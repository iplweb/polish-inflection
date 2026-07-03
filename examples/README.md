# Przykłady / Examples

Proste, samodzielne skrypty pokazujące użycie `polish-inflection`.
Wymagają zainstalowanego pakietu (`pip install polish-inflection` lub
`pip install -e .` w repo).

| Plik | Co pokazuje |
|---|---|
| [`01_odmien.py`](01_odmien.py) | Odmiana rzeczownika przez 7 przypadków × 2 liczby (`odmien`). |
| [`02_podaj.py`](02_podaj.py) | Analiza zwrotna forma → analizy; synkretyzm i filtr liczby (`podaj`). |
| [`03_fallbacki.py`](03_fallbacki.py) | Zachowanie przy braku formy: wyjątek / `None` / passthrough / własny `default`. |
| [`04_szablony_ui.py`](04_szablony_ui.py) | Zastosowanie źródłowe: nazwy typów jednostek w komunikatach UI. |
| [`05_pytania.py`](05_pytania.py) | API pytań przypadkowych (`kogo_czego`…) + `podstawowa_forma`. |
| [`06_liczebnikowa.py`](06_liczebnikowa.py) | Zgoda liczebnikowa: forma rzeczownika przy liczbie (`odmiana_liczebnikowa`). |
| [`07_przymiotniki.py`](07_przymiotniki.py) | Odmiana przymiotnika (`odmien_przymiotnik`) i leksykalna analiza zwrotna (`podaj_przymiotnik`). |
| [`08_frazy.py`](08_frazy.py) | Odmiana wielowyrazowych nazw instytucji (`odmien_fraze`): zgoda, l.mn., reguła małej litery. |

Uruchomienie:

```bash
python examples/01_odmien.py
python examples/07_przymiotniki.py
python examples/08_frazy.py
```
