"""Testy budowy indeksów i round-tripu build -> zapis -> odczyt readerem."""

from pathlib import Path

import marisa_trie

from polish_inflection.build import _pary_dawg, parsuj_linie, zbuduj_z_tab

FIXTURES = Path(__file__).parent / "fixtures"
DOMAIN_TAB = FIXTURES / "sgjp_domain.tab"


def _load(path: Path) -> marisa_trie.BytesTrie:
    t = marisa_trie.BytesTrie()
    t.load(str(path))
    return t


def test_routing_depr_tylko_do_podaj():
    linie = [
        "wydziału\twydział\tsubst:sg:gen:m3\tx\t",
        "chłopy\tchłop\tdepr:pl:nom.acc.voc:m2\tx\t",
    ]
    odmien_pary, podaj_pary = _pary_dawg(parsuj_linie(linie))
    odmien_klucze = {k for k, _ in odmien_pary}
    podaj_klucze = {k for k, _ in podaj_pary}
    # depr NIE trafia do odmien
    assert "chłop\tnom\tpl" not in odmien_klucze
    assert "wydział\tgen\tsg" in odmien_klucze
    # depr trafia do podaj
    assert "chłopy" in podaj_klucze


def test_wartosc_odmien_to_sama_forma():
    odmien_pary, _ = _pary_dawg(parsuj_linie(["wydziału\twydział\tsubst:sg:gen:m3\tx\t"]))
    assert odmien_pary == [("wydział\tgen\tsg", "wydziału".encode())]


def test_round_trip_build_i_odczyt(tmp_path):
    info = zbuduj_z_tab(DOMAIN_TAB, tmp_path, data_build="test")
    assert (tmp_path / "odmien.marisa").exists()
    assert (tmp_path / "podaj.marisa").exists()
    assert (tmp_path / "BUILD_INFO.json").exists()
    assert info["liczba_lematow"] > 5
    assert info["liczba_rekordow"] > 100

    odmien_d = _load(tmp_path / "odmien.marisa")
    podaj_d = _load(tmp_path / "podaj.marisa")

    assert [v.decode() for v in odmien_d["wydział\tgen\tsg"]] == ["wydziału"]
    assert "wydziałów" in [v.decode() for v in odmien_d["wydział\tgen\tpl"]]

    # depr: forma 'chłopy' jest analizowalna przez podaj, ale NIGDY nie jest
    # formą główną w odmien — tam nom pl to subst 'chłopi', nie deprecjatywne 'chłopy'.
    assert "chłopy" in podaj_d
    nom_pl_formy = [v.decode() for v in odmien_d["chłop\tnom\tpl"]]
    assert "chłopi" in nom_pl_formy
    assert "chłopy" not in nom_pl_formy
    # a w podaj 'chłopy' ma analizę deprecjatywną (pl, m2)
    assert any(v.decode().startswith("chłop\t") for v in podaj_d["chłopy"])


def test_build_info_ma_wersje(tmp_path):
    # fixtura nie ma nagłówka #!DICT-ID -> wersja None, ale klucz obecny
    info = zbuduj_z_tab(DOMAIN_TAB, tmp_path)
    assert "wersja_sgjp" in info
    assert info["rozmiar_odmien_marisa"] > 0
    assert info["rozmiar_podaj_marisa"] > 0


def test_round_trip_gz(tmp_path):
    # zbuduj z .tab.gz — sprawdza gałąź gzip w _otworz_tab
    import gzip

    gz = tmp_path / "src.tab.gz"
    with gzip.open(gz, "wt", encoding="utf-8") as f:
        f.write("wydziału\twydział\tsubst:sg:gen:m3\tx\t\n")
    out = tmp_path / "out"
    zbuduj_z_tab(gz, out)
    d = _load(out / "odmien.marisa")
    assert d["wydział\tgen\tsg"][0].decode() == "wydziału"
