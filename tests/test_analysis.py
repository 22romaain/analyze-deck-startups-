"""Tests des règles déterministes de red flags (detect_red_flags), volet cap table §4.3."""

from src.analysis import detect_dilution_flag, detect_red_flags, run_analysis
from src.models import DeckSignals


def _score(result, dim):
    return next(d.score for d in result.dimension_scores if d.dimension == dim)


def test_majeur_plafonne_la_dimension_a_40():
    # TAM top-down -> MAJEUR sur marche : la dimension est plafonnee a 40, bonus compris.
    result = run_analysis(DeckSignals(tam_methodology="top-down", has_why_now=True), "serie-a")
    assert _score(result, "marche") == 40.0


def test_mineur_retire_dix_points():
    # TAM absent hors pre-seed -> MINEUR sur marche : base 60 - 10 = 50.
    result = run_analysis(DeckSignals(), "serie-a")
    assert _score(result, "marche") == 50.0


def test_critique_plafonne_le_global_a_35():
    # Produit tech sans fondateur technique -> CRITIQUE : score global plafonne a 35.
    result = run_analysis(DeckSignals(product_is_tech=True, has_technical_founder=False,
                                      founder_ownership_pct=80.0), "serie-a")
    assert result.global_score <= 35.0


def test_trois_majeurs_plafonnent_le_global():
    # 3 MAJEURS accumules = 1 CRITIQUE (§5.2) -> global plafonne a 35, sans aucun CRITIQUE.
    signals = DeckSignals(tam_methodology="top-down", founder_ownership_pct=30.0,
                          customer_concentration_top1_pct=60.0)  # marche + equipe + traction
    result = run_analysis(signals, "serie-a")
    assert sum(1 for f in result.red_flags if f.severity == "CRITIQUE") == 0
    assert sum(1 for f in result.red_flags if f.severity == "MAJEUR") >= 3
    assert result.global_score <= 35.0


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


def test_revenu_derisoire_ne_donne_pas_de_bonus():
    # Bug reel Square : revenu extrait a 1 USD ne doit pas valoir "revenu etabli".
    result = run_analysis(DeckSignals(revenue_amount=1.0, revenue_currency="USD"), "serie-a")
    traction = next(d for d in result.dimension_scores if d.dimension == "traction")
    assert not any("Revenu établi" in r for r in traction.rationale)


def test_vrai_revenu_donne_le_bonus():
    result = run_analysis(DeckSignals(revenue_amount=200_000.0, revenue_currency="EUR"), "serie-a")
    traction = next(d for d in result.dimension_scores if d.dimension == "traction")
    assert any("Revenu établi" in r for r in traction.rationale)
