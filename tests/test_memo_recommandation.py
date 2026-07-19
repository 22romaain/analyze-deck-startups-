"""Tests de la tranche 2 : recommandation (forces, faiblesses).

On teste les sous-fonctions isolément : build_memo_data reste en construction.
"""

from src.models import (
    DIMENSION_LABELS,
    DimensionScore,
    RedFlag,
)
from src.output.memo_data import (
    load_memo_config,
    select_faiblesses,
    select_forces,
)

CONFIG = load_memo_config()


def dscore(dim: str, score: float, weight: float, rationale=None) -> DimensionScore:
    """Fabrique un DimensionScore minimal pour les tests."""
    return DimensionScore(
        dimension=dim, label=DIMENSION_LABELS.get(dim, dim), score=score,
        weight=weight, rationale=rationale or ["Base neutre : 60."],
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
