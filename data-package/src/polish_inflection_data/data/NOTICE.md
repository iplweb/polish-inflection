# NOTICE — licencje i atrybucja

Pakiet `polish-inflection` łączy dwie warstwy o **osobnych** właścicielach praw
autorskich i osobnych (choć identycznych co do treści) licencjach. Obie są
2-clause BSD; obie wymagają zachowania noty copyright i tekstu licencji przy
redystrybucji.

---

## 1. Kod pakietu

Copyright © 2026 Michał Pasternak.
Licencja: **BSD-2-Clause**. Pełny tekst: plik [`LICENSE`](LICENSE) w tym repo.

Obejmuje kod źródłowy w `src/polish_inflection/` (runtime, build, CLI), testy
oraz dokumentację. **Nie** obejmuje danych fleksyjnych ani zbudowanych z nich
indeksów `.marisa` — te podlegają warstwie 2.

---

## 2. Dane SGJP (Słownik gramatyczny języka polskiego)

Indeksy `.marisa` w `src/polish_inflection/data/` są zbudowane z danych
fleksyjnych SGJP i stanowią ich utwór zależny. Podlegają licencji i atrybucji
SGJP.

**Copyright © 2007–2026 Marcin Woliński, Zbigniew Bronk, Włodzimierz
Gruszczyński, Witold Kieraś, Zygmunt Saloni, Danuta Skowrońska, Robert Wołosz.**

Licencja: **BSD-2-Clause**.
Strona licencyjna: <https://morfeusz.sgjp.pl/doc/license/en>.

Autorytatywny, verbatim tekst licencji jadący z konkretnym wydaniem SGJP
znajduje się w pliku **`data/sgjp/LICENSE.sgjp`** (wyodrębniony z nagłówka
`#<COPYRIGHT>` pobranego pliku `.tab.gz` przez komendę `refresh-sgjp`). W razie
jakiejkolwiek rozbieżności rozstrzygający jest tamten plik, nie ten dokument.

### Warunki 2-clause BSD (cytat)

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### Konsekwencje redystrybucji

Redystrybuując `polish-inflection` (w tym wheel/sdist zawierające `.marisa`),
zachowujesz notę copyright SGJP, powyższe warunki i atrybucję — co realizuje ten
plik `NOTICE.md` (dołączany do dystrybucji) wraz z verbatim `data/sgjp/LICENSE.sgjp`
podróżującym z danymi w repozytorium.
