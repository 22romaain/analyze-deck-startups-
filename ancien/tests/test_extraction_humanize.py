"""Tests du rendu lisible des dimensions structurées par le LLM (_humanize)."""

import json

from src.extraction import _humanize, _parse_response


def test_humanize_dict_imbrique():
    value = {"unit_economics": {"LTV": "$240", "churn": "5%"}, "modele": "Freemium"}
    out = _humanize(value)
    assert "unit economics : LTV : $240 ; churn : 5%" in out
    assert "modele : Freemium" in out
    assert "{'" not in out  # plus aucun repr Python


def test_humanize_liste_d_objets_en_puces():
    value = [{"nom": "Joel", "role": "CEO"}, {"nom": "Leo", "role": "CMO"}]
    out = _humanize(value)
    assert out == "- nom : Joel ; role : CEO\n- nom : Leo ; role : CMO"


def test_humanize_liste_de_scalaires_en_virgules():
    assert _humanize(["Hootsuite", "TweetDeck"]) == "Hootsuite, TweetDeck"


def test_parse_response_rend_les_dimensions_lisibles():
    # Le LLM renvoie une dimension structuree : elle doit ressortir en texte propre.
    dims = {d: "x" for d in ["probleme", "solution", "marche", "business_model",
                             "traction", "concurrence", "go_to_market", "financials", "ask"]}
    dims["equipe"] = {"fondateurs": [{"nom": "Joel", "role": "CEO"}], "complementarite": "tech + growth"}
    dims["detected_round"] = "seed"
    dims["ask_amount"] = "non mentionné"
    analysis, _ = _parse_response(json.dumps(dims))
    assert "{'" not in analysis.equipe  # pas de repr Python
    assert "- nom : Joel ; role : CEO" in analysis.equipe
    assert "complementarite : tech + growth" in analysis.equipe
