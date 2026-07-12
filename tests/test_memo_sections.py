"""Tests de la tranche 4 : builders des sections 2 à 5 (dashboard, dimensions,
red flags, données manquantes)."""

from src.analysis import run_analysis
from src.models import DeckSignals, RedFlag
from src.output.memo_data import (
    _grade_for,
    build_dashboard,
    build_dimensions,
    build_missing_data,
    build_red_flag_rows,
    filter_incoherences,
    load_memo_config,
)

CONFIG = load_memo_config()


# --- Tableau de bord (section 2) ---

def test_dashboard_statuts_par_metrique():
    signals = DeckSignals(
        churn_rate_pct=1.5, churn_period="monthly",  # top quartile (<= 2)
        runway_months=9.0,                            # sous la barre (< 12)
        revenue_amount=200000.0, revenue_currency="EUR",  # pas de benchmark -> non évaluable
    )
    rows = {r.metrique: r for r in build_dashboard(signals, "serie-a", CONFIG)}
    assert rows["Churn ou rétention"].statut == "TOP_QUARTILE"
    assert rows["Burn et runway"].statut == "SOUS_LA_BARRE"
    assert rows["ARR"].statut == "NON_EVALUABLE"
    assert rows["Croissance"].statut == "ABSENT"  # growth absent (couple invalidé)


def test_dashboard_churn_annuel_non_comparable():
    # Le benchmark churn est mensuel : un churn annuel ne se compare pas.
    signals = DeckSignals(churn_rate_pct=8.0, churn_period="annual")
    rows = {r.metrique: r for r in build_dashboard(signals, "serie-a", CONFIG)}
    assert rows["Churn ou rétention"].statut == "NON_EVALUABLE"


# --- Grades ---

def test_grade_for_bornes():
    assert _grade_for(80.0, CONFIG) == "A"
    assert _grade_for(79.9, CONFIG) == "B"
    assert _grade_for(50.0, CONFIG) == "C"
    assert _grade_for(0.0, CONFIG) == "E"


# --- Analyse par dimension (section 3) ---

def test_dimensions_ordre_poids_decroissant():
    analysis = run_analysis(DeckSignals(), "serie-a")
    dims = build_dimensions(analysis, CONFIG)
    ordre = [d.dimension for d in dims]
    assert ordre[0] == "traction"  # poids 0.30, ouvre la série A
    # Départage alphabétique à poids égal (0.10) : concurrence < go_to_market < marche.
    assert ordre.index("concurrence") < ordre.index("go_to_market") < ordre.index("marche")
    assert "financials" not in ordre  # poids 0 en série A -> exclu


def test_dimensions_red_flags_inline_groupes():
    # Produit tech sans fondateur technique -> red flag CRITIQUE sur equipe.
    signals = DeckSignals(product_is_tech=True, has_technical_founder=False)
    analysis = run_analysis(signals, "serie-a")
    dims = {d.dimension: d for d in build_dimensions(analysis, CONFIG)}
    inline = dims["equipe"].red_flags_inline
    assert len(inline) == 1 and inline[0].severity == "CRITIQUE"


# --- Red flags (section 4) ---

def test_red_flag_rows_tri_severite_et_incoherence():
    flags = [
        RedFlag(dimension="traction", severity="MINEUR", message="Incohérence interne : revenu élevé."),
        RedFlag(dimension="equipe", severity="CRITIQUE", message="Pas de CTO."),
        RedFlag(dimension="marche", severity="MAJEUR", message="TAM top-down."),
    ]
    rows = build_red_flag_rows(flags)
    assert [r.severity for r in rows] == ["CRITIQUE", "MAJEUR", "MINEUR"]
    incoherences = filter_incoherences(rows)
    assert len(incoherences) == 1 and incoherences[0].dimension == "traction"


# --- Données manquantes (section 5) ---

def test_missing_data_signaux_absents():
    missing = build_missing_data(DeckSignals(), "serie-a", CONFIG)
    labels = {m.label: m for m in missing}
    assert "ARR" in labels  # revenue_amount None
    assert labels["ARR"].criticite == "MAJEUR"
    assert "référentiel §1.1" in labels["ARR"].justification
