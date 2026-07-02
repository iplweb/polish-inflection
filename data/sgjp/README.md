# data/sgjp — zwendorowany, przypięty SGJP

Ten katalog trzyma **surowe źródło danych** budowy: przypiętą kopię wydania
Słownika gramatycznego języka polskiego (SGJP). Nie jest częścią wheela — służy
wyłącznie do offline'owego builda indeksów `.marisa` (patrz
[`docs/budowanie.md`](../../docs/budowanie.md)).

Powód vendoringu: reprodukowalność i **odporność na zniknięcie źródła**. Upstream
(`download.sgjp.pl`) może kiedyś zniknąć albo zmienić układ — przypięta kopia
podróżuje z repozytorium i pozwala odtworzyć build bit w bit.

## Zawartość

| Plik | Rola |
|---|---|
| `sgjp-<wersja>.tab.gz` | przypięte wydanie SGJP (tab-separated, gzip). **git-lfs.** |
| `PIN.json` | metadane pinu: `wersja`, `data_pobrania`, `sha256`, `url_zrodlowy` |
| `LICENSE.sgjp` | verbatim tekst licencji + copyright wyodrębniony z nagłówka `.tab.gz` |

`sgjp-<wersja>.tab.gz` (rzędu kilkudziesięciu MB, np. ≈ 42,7 MB dla wydania
`20260628`) jest śledzony przez **git-lfs** — reguła `data/sgjp/*.tab.gz` w
`.gitattributes`. Po sklonowaniu repo pobierz realny plik przez:

```bash
git lfs pull
```

Bez git-lfs w miejscu `.tab.gz` znajdziesz tekstowy wskaźnik LFS, nie dane.

## Skąd się to bierze

Plików tu **nie edytujemy ręcznie**. Aktualizuje je komenda maintainerska:

```bash
polish-inflection-build refresh-sgjp
```

Pobiera najnowsze wydanie, liczy `sha256`, re-vendoruje `.tab.gz`, aktualizuje
`PIN.json` i wyodrębnia `LICENSE.sgjp`. Szczegóły: [`docs/budowanie.md`](../../docs/budowanie.md).

## Licencja danych

Dane SGJP są na 2-clause BSD i wymagają zachowania noty copyright oraz atrybucji.
Autorytatywny tekst to `LICENSE.sgjp`; podsumowanie i atrybucja — [`NOTICE.md`](../../NOTICE.md).
