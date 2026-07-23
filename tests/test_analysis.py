"""Tests des règles déterministes de red flags (detect_red_flags), volet cap table §4.3."""

from src.analysis import (
    collecter_findings,
    detect_dilution_flag,
    detect_red_flags,
    redflag_to_finding,
    run_analysis,
)
from src.models import DeckSignals, RedFlag


def test_trois_majeurs_detectes():
    # marche (TAM top-down) + equipe (dilution) + traction (concentration) -> 3 MAJEURS.
    signals = DeckSignals(tam_methodology="top-down", founder_ownership_pct=30.0,
                          customer_concentration_top1_pct=60.0)
    result = run_analysis(signals, "serie-a")
    assert sum(1 for f in result.red_flags if f.severity == "CRITIQUE") == 0
    assert sum(1 for f in result.red_flags if f.severity == "MAJEUR") >= 3


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


# --- Couche qualitative : constats tagués (collecter_findings) ---

def test_redflag_to_finding_mappe_les_severites():
    assert redflag_to_finding(RedFlag(dimension="x", severity="CRITIQUE", message="m")).categorie == "redhibitoire"
    assert redflag_to_finding(RedFlag(dimension="x", severity="MAJEUR", message="m")).categorie == "faiblesse"
    assert redflag_to_finding(RedFlag(dimension="x", severity="MINEUR", message="m")).categorie == "vigilance"


def test_collecter_findings_inclut_les_constats_des_detecteurs():
    # Runway de 4 mois -> red flag CRITIQUE code -> constat redhibitoire dans la liste.
    findings = collecter_findings(DeckSignals(runway_months=4.0), "serie-a")
    redhibitoires = [f for f in findings if f.categorie == "redhibitoire"]
    assert any(f.source == "detecteur" and "Runway" in f.message for f in redhibitoires)


def test_collecter_findings_fusionne_code_et_yaml():
    # Un signal purement YAML (exit fondateur) et un signal purement code (runway court)
    # doivent tous deux ressortir, avec des sources distinctes.
    signals = DeckSignals(founder_prior_exit=True, runway_months=4.0)
    sources = {f.source for f in collecter_findings(signals, "serie-a")}
    assert "detecteur" in sources
    assert any(s.startswith("critere:") for s in sources)
