"""Testy parsowania i EKSPANSJI tagów SGJP (build.parsuj_linie)."""

from pathlib import Path

from polish_inflection.build import Rekord, goly_lemat, parsuj_linie

FIXTURES = Path(__file__).parent / "fixtures"


def _rekordy(linie):
    return list(parsuj_linie(linie))


def test_goly_lemat_ucina_fleksem():
    assert goly_lemat("profesor:Sm1") == "profesor"
    assert goly_lemat("AA:Sm3.n_ncol") == "AA"
    assert goly_lemat("wydział") == "wydział"


def test_ekspansja_nom_acc():
    # jedna linia z nom.acc -> DWA rekordy
    rekordy = _rekordy(["wydział\twydział\tsubst:sg:nom.acc:m3\tnazwa_pospolita\t"])
    kombo = {(r.przypadek, r.liczba) for r in rekordy}
    assert kombo == {("nom", "sg"), ("acc", "sg")}
    assert all(r.forma == "wydział" and r.lemat == "wydział" and not r.depr for r in rekordy)


def test_ekspansja_sg_pl_i_wszystkie_przypadki():
    # subst:sg.pl:nom.gen.dat.acc.inst.loc.voc -> 2*7 = 14 rekordów
    rekordy = _rekordy(["AA\tAA:Sm3.n_ncol\tsubst:sg.pl:nom.gen.dat.acc.inst.loc.voc:m3\tx\t"])
    assert len(rekordy) == 14
    assert all(r.lemat == "AA" and r.rodzaj == "m3" for r in rekordy)


def test_depr_oflagowane():
    rekordy = _rekordy(["chłopy\tchłop\tdepr:pl:nom.acc.voc:m2\tnazwa_pospolita\t"])
    assert rekordy
    assert all(r.depr and r.forma == "chłopy" and r.lemat == "chłop" for r in rekordy)


def test_depr_lemat_ma_fleksem():
    rekordy = _rekordy(["profesory\tprofesor:Sm1\tdepr:pl:nom.acc.voc:m2\tx\t"])
    assert all(r.lemat == "profesor" and r.depr for r in rekordy)


def test_pomija_naglowki_i_puste():
    linie = [
        "#!DICT-ID pl.sgjp.sgjp-2026.06.29",
        "#<COPYRIGHT>",
        "Copyright ...",
        "",
        "wydziału\twydział\tsubst:sg:gen:m3\tnazwa_pospolita\t",
    ]
    rekordy = _rekordy(linie)
    assert rekordy == [Rekord("wydziału", "wydział", "sg", "gen", "m3", False)]


def test_pomija_nie_subst():
    # inne części mowy odrzucone
    linie = [
        "biegać\tbiegać\tverb:...",
        "szybki\tszybki\tadj:sg:nom:m1:pos",
        "wydziału\twydział\tsubst:sg:gen:m3\tx\t",
    ]
    rekordy = _rekordy(linie)
    assert len(rekordy) == 1
    assert rekordy[0].lemat == "wydział"


def test_pomija_niekompletne():
    # za mało pól tagu / za mało kolumn
    assert _rekordy(["forma\tlemat\tsubst:sg"]) == []
    assert _rekordy(["forma\tlemat"]) == []


def test_pomija_nieznany_przypadek():
    # 'foo' nie jest przypadkiem -> tylko gen przechodzi
    rekordy = _rekordy(["x\tx\tsubst:sg:gen.foo:m3\ty\t"])
    assert [r.przypadek for r in rekordy] == ["gen"]


def test_na_realnej_fixturze():
    linie = (FIXTURES / "sgjp_domain.tab").read_text(encoding="utf-8").splitlines()
    rekordy = _rekordy(linie)
    assert len(rekordy) > 100
    # 'koło' ma w SGJP lemat z sufiksem fleksemu -> goły lemat "koło"
    lematy = {r.lemat for r in rekordy}
    assert "wydział" in lematy
    assert "jednostka" in lematy
    # żaden goły lemat nie zawiera dwukropka
    assert all(":" not in lem for lem in lematy)
