"""Tests de la tranche 1 : chargement/validation de config + verdict."""

import json

import pytest

from src.models import RedFlag
from src.output.memo_data import compute_verdict, load_memo_config

# Config réelle du projet, chargée une fois pour les tests de verdict.
CONFIG = load_memo_config()


def rf(severity: str, dimension: str = "marche") -> RedFlag:
    """Fabrique un red flag minimal pour les tests."""
    return RedFlag(dimension=dimension, severity=severity, message="test")


# --- Verdict : les trois branches ---

def test_passer_par_score():
    v = compute_verdict(30.0, [], CONFIG)
    assert v.decision == "PASSER"
    assert "< 40" in v.justification


def test_passer_par_red_flag_critique():
    # Score élevé mais un critique domine tout.
    v = compute_verdict(85.0, [rf("CRITIQUE")], CONFIG)
    assert v.decision == "PASSER"
    assert v.nb_critiques == 1


def test_approfondir_par_deux_majeurs():
    # Score qui vaudrait POURSUIVRE, ramené à APPROFONDIR par 2 majeurs.
    v = compute_verdict(85.0, [rf("MAJEUR"), rf("MAJEUR")], CONFIG)
    assert v.decision == "APPROFONDIR"
    assert v.nb_majeurs == 2


def test_approfondir_par_score_median():
    v = compute_verdict(50.0, [], CONFIG)
    assert v.decision == "APPROFONDIR"


def test_poursuivre():
    v = compute_verdict(80.0, [], CONFIG)
    assert v.decision == "POURSUIVRE"


# --- Cas limites : convention de borne large vers APPROFONDIR ---

def test_borne_basse_exacte_est_approfondir():
    # 40 n'est pas < 40 -> pas PASSER ; convention large -> APPROFONDIR.
    v = compute_verdict(40.0, [], CONFIG)
    assert v.decision == "APPROFONDIR"


def test_borne_haute_exacte_est_approfondir():
    # 65 n'est pas > 65 -> pas POURSUIVRE ; convention large -> APPROFONDIR.
    v = compute_verdict(65.0, [], CONFIG)
    assert v.decision == "APPROFONDIR"


# --- Validation de la config ---

def _ecris_config(tmp_path, data) -> "Path":
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_config_seuils_incoherents_leve_valueerror(tmp_path):
    data = {
        "verdict": {"seuil_bas": 70, "seuil_haut": 65, "majeurs_pour_approfondir": 2},
        "grades": [{"min": 0, "grade": "E"}],
        "societe_fallback": "X", "version_referentiel": "v",
    }
    with pytest.raises(ValueError):
        load_memo_config(_ecris_config(tmp_path, data))


def test_config_grades_non_decroissants_leve_valueerror(tmp_path):
    data = {
        "verdict": {"seuil_bas": 40, "seuil_haut": 65, "majeurs_pour_approfondir": 2},
        "grades": [{"min": 50, "grade": "C"}, {"min": 80, "grade": "A"}, {"min": 0, "grade": "E"}],
        "societe_fallback": "X", "version_referentiel": "v",
    }
    with pytest.raises(ValueError):
        load_memo_config(_ecris_config(tmp_path, data))
