"""Tests des builders du mémo qualitatif : doctrine, grille, dimensions, cap table."""

import pytest

from src.analysis import collecter_findings
from src.captable import LiquidationPref
from src.models import DeckAnalysis, DeckSignals
from src.output.memo_data import (
    REVIEW_BANDEAU_DISPONIBLE,
    REVIEW_BANDEAU_INDISPONIBLE,
    build_captable_section,
    build_dimensions_qualitatives,
    build_grille,
    build_review_block,
    load_memo_config,
)

CONFIG = load_memo_config()


# --- Doctrine RAG (citation des cours) ---

def test_cite_doctrine_filtre_les_matchs_trop_lointains():
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [
            SearchHit(text="Pertinent.", source="c.md", section="A", distance=0.9),   # gardé
            SearchHit(text="Hors sujet.", source="c.md", section="B", distance=1.5),  # filtré
        ]

    cites = cite_doctrine("marché", retriever=fake_retriever)
    assert len(cites) == 1 and cites[0].section == "A"


def test_cite_doctrine_seuil_ajustable():
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="Loin.", source="c.md", section="B", distance=1.5)]

    # Seuil large : le passage lointain passe. Seuil par défaut : il est filtré.
    assert len(cite_doctrine("m", retriever=fake_retriever, max_distance=2.0)) == 1
    assert cite_doctrine("m", retriever=fake_retriever) == []


def test_doctrine_extrait_sans_balisage_markdown():
    """Un passage de cours est du Markdown : cité brut, il casserait la mise en page."""
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    brut = "**Traction et PMF (25%)**\n- Excellent : rétention démontrée\n- Bon : clients payants"

    def fake_retriever(query, k):
        return [SearchHit(text=brut, source="criteres.md", section="Critères", distance=0.2)]

    extrait = cite_doctrine("traction", retriever=fake_retriever)[0].extrait
    assert "*" not in extrait
    assert "\n" not in extrait
    assert not extrait.startswith("-")
    assert extrait.startswith("Traction et PMF (25%)")


def test_doctrine_extrait_coupe_a_la_fin_d_un_mot():
    """Une citation tronquée en plein mot fait douter de la source."""
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="rétention " * 60, source="c.md", section="s", distance=0.2)]

    extrait = cite_doctrine("t", retriever=fake_retriever)[0].extrait
    assert len(extrait) <= 300
    assert extrait.endswith("rétention…")


# --- Grille d'attendus (présent / absent / inconnu) ---

def test_grille_present_absent_inconnu():
    # Un signal renseigné -> PRESENT ; un booléen nié -> ABSENT ; un None -> INCONNU.
    signals = DeckSignals(
        revenue_amount=1_000_000.0, revenue_currency="EUR",  # revenus présents
        has_why_now=False,                                    # why now nié
    )
    rows = {r.label: r for r in build_grille(signals, "seed", CONFIG)}
    assert rows["Why now (pourquoi maintenant)"].statut == "ABSENT"
    assert rows["Premiers revenus / preuves d'usage"].statut == "PRESENT"
    assert rows["Cap table (part fondateurs)"].statut == "INCONNU"


def test_grille_valeur_formatee_si_presente():
    rows = {r.label: r for r in build_grille(DeckSignals(runway_months=18.0), "serie-a", CONFIG)}
    assert rows["Burn et runway"].statut == "PRESENT"
    assert rows["Burn et runway"].valeur == "18 mois"


# --- Analyse par dimension (sans score) ---

def _deck_min(**champs):
    base = {d: d for d in ("equipe", "probleme", "solution", "marche", "business_model",
                           "traction", "concurrence", "go_to_market", "financials", "ask")}
    base.update(detected_round="serie-a", ask_amount="8M EUR", **champs)
    return DeckAnalysis(**base)


def test_dimensions_qualitatives_sans_score_avec_constats():
    deck = _deck_min(equipe="Deux fondateurs experimentes.")
    findings = collecter_findings(DeckSignals(ltv_cac_ratio=0.7, founder_prior_exit=True), "serie-a")
    secs = {s.dimension: s for s in build_dimensions_qualitatives(deck, findings, "serie-a")}
    # Toutes les dimensions sont présentes, chacune avec son narratif.
    assert len(secs) == 10
    assert secs["equipe"].narratif == "Deux fondateurs experimentes."
    # Les constats sont rattachés à leur dimension et triés par gravité (rédhibitoire d'abord).
    cats = [f.categorie for f in secs["business_model"].findings]
    assert cats and cats[0] == "redhibitoire"


def test_dimensions_qualitatives_ordonnees_par_pertinence_du_round():
    # En série A, la traction est la dimension la plus lourde : elle passe en tête.
    secs = build_dimensions_qualitatives(_deck_min(), [], "serie-a")
    assert secs[0].dimension == "traction"


def test_dimensions_qualitatives_doctrine_ciblee():
    # Un faux retriever déterministe : la couche mémo se teste sans ChromaDB ni réseau.
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="Exiger un TAM bottom-up. " * 40, source="cours_marche.md",
                          section="TAM", distance=0.12)]

    secs = {s.dimension: s for s in build_dimensions_qualitatives(
        _deck_min(), [], "serie-a", retriever=fake_retriever, doctrine_dimensions={"marche"})}
    # Seule 'marche' est enrichie ; les autres restent sans doctrine.
    assert len(secs["marche"].doctrine) == 1
    assert secs["marche"].doctrine[0].source == "cours_marche.md"
    assert len(secs["marche"].doctrine[0].extrait) <= 300
    assert secs["traction"].doctrine == []


# --- Contre-analyse ---

def test_review_block_indisponible():
    r = build_review_block(None)
    assert r.disponible is False
    assert r.bandeau == REVIEW_BANDEAU_INDISPONIBLE
    assert r.contenu is None


def test_review_block_disponible():
    r = build_review_block("Le moat repose sur un accord exclusif non contractualise.")
    assert r.disponible is True
    assert r.bandeau == REVIEW_BANDEAU_DISPONIBLE
    assert "moat" in r.contenu


# --- Cap table et dilution ---

def test_captable_calculable_dilution():
    # Valo 8M (avec devise), ask 2M, fondateurs 80%, pool 10% -> post 10M, fondateurs 56%.
    signals = DeckSignals(pre_money_valuation=8_000_000, pre_money_currency="EUR",
                          founder_ownership_pct=80.0, new_option_pool_pct=10.0)
    c = build_captable_section(signals, "2M EUR")
    assert c.calculable is True
    assert c.dilution.post_money == 10_000_000
    assert c.dilution.new_investor_pct == pytest.approx(20.0)
    assert c.dilution.founder_pct_post == pytest.approx(56.0)
    assert c.dilution.founder_dilution_points == pytest.approx(24.0)
    assert c.waterfall is None


def test_captable_degrade_si_donnee_manquante():
    # Sans montant (ask None) : non calculable, le manque est nommé, aucun chiffre inventé.
    signals = DeckSignals(pre_money_valuation=8_000_000, pre_money_currency="EUR",
                          founder_ownership_pct=80.0)
    c = build_captable_section(signals, None)
    assert c.calculable is False
    assert c.dilution is None
    assert "Montant levé (l'ask)" in c.donnees_absentes


def test_captable_termes_incoherents():
    # Investisseur + pool > 100% : le moteur renonce, on ne sort pas de faux chiffre.
    signals = DeckSignals(pre_money_valuation=1_000_000, pre_money_currency="EUR",
                          founder_ownership_pct=80.0, new_option_pool_pct=95.0)
    c = build_captable_section(signals, "5M EUR")
    assert c.calculable is False
    assert c.dilution is None
    assert c.donnees_absentes  # une raison est donnée


def test_captable_waterfall_si_prefs():
    # Des liquidation prefs connues -> waterfall calculé (sortie au post-money).
    prefs = [LiquidationPref(name="Serie A", invested=2_000_000, multiple=1.0, as_converted_pct=20.0)]
    signals = DeckSignals(pre_money_valuation=8_000_000, pre_money_currency="EUR",
                          founder_ownership_pct=80.0, liquidation_prefs=prefs)
    c = build_captable_section(signals, "2M EUR")
    assert c.calculable is True
    assert c.waterfall is not None
    assert c.waterfall.exit_value == c.dilution.post_money
