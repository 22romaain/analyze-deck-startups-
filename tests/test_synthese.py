"""Tests de la synthèse qualitative (pros/cons + recommandation par catégories)."""

from src.models import Finding
from src.output.synthese import build_synthese, recommander


def _f(categorie, dimension="business_model"):
    return Finding(dimension=dimension, categorie=categorie, message="m")


def test_recommander_redhibitoire_donne_approfondir_a_justifier():
    # Choix assumé : un rédhibitoire ne conclut pas à un rejet automatique, il
    # renvoie à APPROFONDIR (à instruire), l'analyste tranche.
    reco = recommander([_f("redhibitoire"), _f("avantage_competitif")])
    assert reco.decision == "APPROFONDIR"
    assert reco.nb_redhibitoires == 1
    assert "justifier" in reco.justification


def test_recommander_faiblesse_sans_redhibitoire_donne_approfondir():
    reco = recommander([_f("faiblesse"), _f("atout_equipe")])
    assert reco.decision == "APPROFONDIR"


def test_recommander_sans_negatif_donne_poursuivre():
    reco = recommander([_f("avantage_competitif"), _f("atout_equipe")])
    assert reco.decision == "POURSUIVRE"
    assert reco.nb_atouts == 2


def test_recommander_vigilance_seule_reste_poursuivre():
    # Une vigilance n'est ni rédhibitoire ni faiblesse : elle ne bloque pas la reco.
    assert recommander([_f("vigilance")]).decision == "POURSUIVRE"


def test_build_synthese_groupe_par_polarite():
    findings = [_f("redhibitoire"), _f("atout_equipe"), _f("a_creuser"), _f("vigilance")]
    syn = build_synthese(findings)
    assert [f.categorie for f in syn.atouts] == ["atout_equipe"]
    assert {f.categorie for f in syn.points_negatifs} == {"redhibitoire", "vigilance"}
    assert [f.categorie for f in syn.a_creuser] == ["a_creuser"]


def test_points_negatifs_tries_par_gravite():
    # rédhibitoire (ordre 0) doit précéder vigilance (ordre 2).
    syn = build_synthese([_f("vigilance"), _f("redhibitoire"), _f("faiblesse")])
    assert [f.categorie for f in syn.points_negatifs] == ["redhibitoire", "faiblesse", "vigilance"]
