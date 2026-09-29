"""Tests du chargeur de critères éditables (src/criteres.py).

On vérifie deux choses : qu'un critère bien formé se charge, et que chaque faute
possible dans le YAML est rejetée avec une erreur (plutôt qu'avalée en silence).
"""

import pytest
from pydantic import ValidationError

from src.criteres import Condition, Critere, charger_criteres, evaluer_criteres
from src.models import DeckSignals


def _critere_valide(**overrides):
    """Fabrique un critère minimal valide, surchargé au besoin par les tests."""
    base = dict(
        id="x", dimension="equipe", categorie="atout_equipe", rounds=["seed"],
        quand={"signal": "founder_is_repeat", "est": "vrai"}, message="ok",
    )
    base.update(overrides)
    return Critere(**base)


# --- Cas nominal ---

def test_critere_valide_se_construit():
    c = _critere_valide()
    assert c.id == "x"
    assert c.quand.signal == "founder_is_repeat"


def test_mot_cle_tous_est_developpe():
    # 'tous' doit devenir la liste réelle des rounds, pas rester le mot-clé.
    c = _critere_valide(rounds=["tous"])
    assert "tous" not in c.rounds
    assert set(c.rounds) == {"pre-seed", "seed", "serie-a", "serie-b", "serie-c", "growth"}


# --- Rejets au niveau de la condition ---

def test_condition_double_forme_rejetee():
    # Mélanger 'est' et 'operateur' n'a pas de sens : on refuse.
    with pytest.raises(ValidationError):
        Condition(signal="s", est="vrai", operateur=">", valeur=3)


def test_condition_vide_rejetee():
    with pytest.raises(ValidationError):
        Condition(signal="s")


def test_condition_chiffree_incomplete_rejetee():
    # Un opérateur sans valeur (ou l'inverse) est incomplet.
    with pytest.raises(ValidationError):
        Condition(signal="s", operateur=">")


# --- Rejets au niveau du critère ---

def test_dimension_inconnue_rejetee():
    with pytest.raises(ValidationError):
        _critere_valide(dimension="equpe")  # faute de frappe


def test_round_inconnu_rejete():
    with pytest.raises(ValidationError):
        _critere_valide(rounds=["seed", "serie-z"])


def test_categorie_inconnue_rejetee():
    with pytest.raises(ValidationError):
        _critere_valide(categorie="genial")  # hors des 6 catégories


# --- Le chargeur de fichier ---

def test_charge_le_vrai_fichier():
    # Le fichier livré doit rester chargeable (garde-fou anti-régression).
    crits = charger_criteres()
    assert len(crits) >= 1
    assert all(isinstance(c, Critere) for c in crits)


def test_fichier_absent_leve_erreur(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_criteres(tmp_path / "inexistant.yaml")


def test_cle_criteres_pas_une_liste_rejetee(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("criteres: ceci n'est pas une liste\n", encoding="utf-8")
    with pytest.raises(ValueError):
        charger_criteres(p)


def test_critere_mal_forme_dans_fichier_rejete(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        "criteres:\n"
        "  - id: faux\n"
        "    dimension: inconnue\n"
        "    categorie: atout_equipe\n"
        "    rounds: [seed]\n"
        "    quand: {signal: x, est: vrai}\n"
        "    message: m\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        charger_criteres(p)


# --- L'évaluateur (signaux -> constats) ---

def _crit_chiffre(**overrides):
    base = dict(id="c", dimension="business_model", categorie="avantage_competitif",
                rounds=["serie-a"], quand={"signal": "ltv_cac_ratio", "operateur": ">=", "valeur": 3},
                message="LTV/CAC de {valeur}.")
    base.update(overrides)
    return Critere(**base)


def test_evaluer_declenche_et_substitue_la_valeur():
    crit = _crit_chiffre()
    findings = evaluer_criteres(DeckSignals(ltv_cac_ratio=4.0), "serie-a", [crit])
    assert len(findings) == 1
    assert findings[0].message == "LTV/CAC de 4."  # 4.0 -> "4", {valeur} substitué
    assert findings[0].source == "critere:c"


def test_evaluer_ignore_signal_absent_en_compare_chiffree():
    # Doctrine 1.1 : on ne compare pas l'inconnu, la condition chiffrée ne déclenche pas.
    findings = evaluer_criteres(DeckSignals(ltv_cac_ratio=None), "serie-a", [_crit_chiffre()])
    assert findings == []


def test_evaluer_absent_declenche_le_constat_de_manque():
    crit = Critere(id="m", dimension="equipe", categorie="faiblesse", rounds=["pre-seed"],
                   quand={"signal": "founder_unique_insight", "est": "absent"}, message="pas d'insight")
    findings = evaluer_criteres(DeckSignals(), "pre-seed", [crit])
    assert len(findings) == 1 and findings[0].categorie == "faiblesse"


def test_evaluer_filtre_par_round():
    # Un critère hors du round demandé ne doit pas être évalué.
    crit = _crit_chiffre(rounds=["serie-b"])
    assert evaluer_criteres(DeckSignals(ltv_cac_ratio=4.0), "serie-a", [crit]) == []
