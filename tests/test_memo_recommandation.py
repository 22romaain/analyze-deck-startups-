"""Tests de la tranche 2 : recommandation (forces, faiblesses, question décisive).

On teste les sous-fonctions isolément : build_memo_data reste en construction.
"""

from src.analysis import ROUND_WEIGHTS
from src.models import (
    DIMENSION_LABELS,
    AnalysisResult,
    DeckSignals,
    DimensionScore,
    RedFlag,
)
from src.output.memo_data import (
    load_memo_config,
    select_faiblesses,
    select_forces,
    select_question_decisive,
)

CONFIG = load_memo_config()


def dscore(dim: str, score: float, weight: float, rationale=None) -> DimensionScore:
    """Fabrique un DimensionScore minimal pour les tests."""
    return DimensionScore(
        dimension=dim, label=DIMENSION_LABELS.get(dim, dim), score=score,
        weight=weight, rationale=rationale or ["Base neutre : 60."],
    )


def analysis_for(round_name: str, scores: dict[str, float], red_flags=None) -> AnalysisResult:
    """Construit un AnalysisResult avec les poids réels du round."""
    weights = ROUND_WEIGHTS[round_name]
    dims = [
        dscore(d, scores.get(d, 60.0), weights.get(d, 0.0))
        for d in DIMENSION_LABELS
    ]
    return AnalysisResult(
        round=round_name, global_score=0.0, dimension_scores=dims,
        red_flags=red_flags or [],
    )


# --- Forces ---

def test_forces_nominal_trie_par_score():
    dims = [
        dscore("traction", 88, 0.30), dscore("business_model", 82, 0.20),
        dscore("equipe", 75, 0.15), dscore("ask", 95, 0.05),
    ]
    forces = select_forces(dims)
    assert [f.dimension for f in forces] == ["ask", "traction", "business_model"]


def test_forces_departage_egalite_poids_puis_alphabetique():
    # Scores égaux : poids décroissant, puis alphabétique. Poids 0 exclu.
    dims = [
        dscore("traction", 80, 0.30), dscore("marche", 80, 0.10),
        dscore("equipe", 80, 0.10), dscore("solution", 80, 0.0),
    ]
    forces = select_forces(dims)
    assert [f.dimension for f in forces] == ["traction", "equipe", "marche"]


def test_forces_moins_de_trois_dimensions_notees():
    # Poids 0 exclu, ET une dimension à la base neutre (60) n'est pas une force.
    dims = [dscore("equipe", 70, 0.40), dscore("probleme", 60, 0.25), dscore("solution", 90, 0.0)]
    forces = select_forces(dims)
    assert [f.dimension for f in forces] == ["equipe"]  # probleme (60 neutre) et solution (poids 0) exclues


# --- Faiblesses ---

def test_faiblesses_priorite_critique_puis_majeur_puis_faible():
    dims = [
        dscore("equipe", 40, 0.25), dscore("marche", 55, 0.15),
        dscore("traction", 30, 0.25), dscore("solution", 60, 0.15),
    ]
    flags = [RedFlag(dimension="marche", severity="MAJEUR", message="TAM top-down"),
             RedFlag(dimension="equipe", severity="CRITIQUE", message="Pas de CTO")]
    faiblesses = select_faiblesses(dims, flags)
    assert [f.dimension for f in faiblesses] == ["equipe", "marche", "traction"]
    assert faiblesses[0].preuve == "Pas de CTO"  # message du red flag critique


def test_faiblesses_dedup_dimension():
    # Une dimension déjà remontée par un red flag n'est pas répétée par les scores faibles.
    dims = [dscore("traction", 20, 0.30), dscore("equipe", 50, 0.15)]
    flags = [RedFlag(dimension="traction", severity="CRITIQUE", message="Churn > croissance")]
    faiblesses = select_faiblesses(dims, flags)
    assert [f.dimension for f in faiblesses] == ["traction", "equipe"]


# --- Question décisive : les 3 règles de priorité ---

def test_question_regle1_red_flag_critique():
    flags = [RedFlag(dimension="business_model", severity="CRITIQUE", message="NRR 80%")]
    analysis = analysis_for("serie-a", {}, red_flags=flags)
    # Tous les attendus présents pour ne pas déclencher la règle 2 par erreur.
    signals = _signals_complets_serie_a()
    q = select_question_decisive(analysis, signals, CONFIG)
    assert q.origine == "red_flag"
    assert q.question == CONFIG.questions_referentiel["serie-a"]["business_model"].question


def test_question_regle2_donnee_manquante_majeure():
    analysis = analysis_for("serie-a", {})  # aucun red flag
    signals = DeckSignals()  # tout à None -> tous les attendus manquants
    q = select_question_decisive(analysis, signals, CONFIG)
    assert q.origine == "donnee_manquante"
    assert "ARR" in q.question  # attendu MAJEUR prioritaire (premier en config)


def test_question_regle3_dimension_la_plus_faible():
    # Aucun critique, tous les attendus présents -> dimension pondérée la plus faible.
    scores = {d: 70.0 for d in DIMENSION_LABELS}
    scores["business_model"] = 25.0
    analysis = analysis_for("serie-a", scores)
    signals = _signals_complets_serie_a()
    q = select_question_decisive(analysis, signals, CONFIG)
    assert q.origine == "dimension_faible"
    assert q.question == CONFIG.questions_referentiel["serie-a"]["business_model"].question


def _signals_complets_serie_a() -> DeckSignals:
    """Signaux où tous les attendus série A sont renseignés (pas de donnée manquante)."""
    return DeckSignals(
        revenue_amount=200000.0, revenue_currency="EUR",
        growth_rate_pct=10.0, growth_period="MoM",
        churn_rate_pct=2.0, churn_period="monthly",
        runway_months=18.0, founder_ownership_pct=70.0,
    )
