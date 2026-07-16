"""Tests des règles déterministes de red flags (detect_red_flags), volet cap table §4.3."""

from src.analysis import detect_dilution_flag, detect_red_flags
from src.models import DeckSignals


def test_fondateurs_sous_seuil_seed_flag_majeur():
    # Doctrine : > 75% post-seed. 65% déclenche donc un flag en seed.
    flags = detect_red_flags(DeckSignals(founder_ownership_pct=65.0), "seed")
    seuil = [f for f in flags if "sous le seuil" in f.message]
    assert len(seuil) == 1 and seuil[0].severity == "MAJEUR"


def test_fondateurs_au_dessus_seuil_seed_pas_de_flag():
    flags = detect_red_flags(DeckSignals(founder_ownership_pct=80.0), "seed")
    assert not [f for f in flags if "sous le seuil" in f.message]


def test_cap_table_absente_serie_a_flag_majeur():
    # founder_ownership_pct absent en série A+ : cap table exigible manquante.
    flags = detect_red_flags(DeckSignals(), "serie-a")
    cap = [f for f in flags if "Cap table non fournie" in f.message]
    assert len(cap) == 1 and cap[0].severity == "MAJEUR"


def test_cap_table_absente_preseed_pas_de_flag():
    # En pre-seed, la cap table n'est pas encore exigible : aucun flag d'absence.
    flags = detect_red_flags(DeckSignals(), "pre-seed")
    assert not [f for f in flags if "Cap table" in f.message]


def test_cap_table_presente_serie_a_pas_de_flag_absence():
    # Détention fournie et au-dessus du seuil : ni flag d'absence, ni flag de seuil.
    flags = detect_red_flags(DeckSignals(founder_ownership_pct=70.0), "serie-a")
    assert not [f for f in flags if "Cap table non fournie" in f.message]
    assert not [f for f in flags if "sous le seuil" in f.message]


def test_dilution_post_tour_sous_seuil_flag_majeur():
    # Fondateurs 55% pre-tour, pre-money 10M, tour 10M -> investisseur 50%,
    # fondateurs post = 55% x 0,5 = 27,5% < seuil serie-a (50%). Alerte.
    signals = DeckSignals(founder_ownership_pct=55.0, pre_money_valuation=10_000_000,
                          pre_money_currency="EUR")
    flag = detect_dilution_flag(signals, "serie-a", "10M EUR")
    assert flag is not None and flag.severity == "MAJEUR"
    assert "Après ce tour" in flag.message


def test_dilution_post_tour_au_dessus_seuil_pas_de_flag():
    # Fondateurs 80%, pre-money 40M, tour 10M -> investisseur 20%, fondateurs post = 64% > 50%.
    signals = DeckSignals(founder_ownership_pct=80.0, pre_money_valuation=40_000_000,
                          pre_money_currency="EUR")
    assert detect_dilution_flag(signals, "serie-a", "10M EUR") is None


def test_dilution_sans_valo_pas_de_flag():
    # Sans valorisation pre-money, la dilution n'est pas calculable : aucune alerte.
    signals = DeckSignals(founder_ownership_pct=55.0)
    assert detect_dilution_flag(signals, "serie-a", "10M EUR") is None
