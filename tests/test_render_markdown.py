"""Golden test du rendu Markdown (sections 0-1-2).

On fige une sortie de référence dans tests/golden/memo_min.md. Toute dérive future
casse le test : on doit alors regénérer sciemment le golden.
"""

from datetime import date
from pathlib import Path

from src.output.memo_data import (
    Annexes,
    DashboardRow,
    KeyQuestion,
    MemoData,
    Reason,
    ReviewBlock,
    Verdict,
)
from src.output.render_markdown import render_markdown

GOLDEN = Path(__file__).parent / "golden" / "memo_min.md"


def make_memo() -> MemoData:
    """Un MemoData complet et stable, sert de fixture au golden test.

    Les sections non encore rendues (dimensions, red flags, etc.) sont fournies
    vides mais valides : MemoData exige tous ses champs.
    """
    return MemoData(
        societe="Acme SaaS",
        round="serie-a",
        ask_amount="8M EUR",
        date=date(2026, 7, 12),
        verdict=Verdict(
            decision="APPROFONDIR",
            justification="APPROFONDIR : score 58 dans [40, 65].",
            score_global=58.0, nb_critiques=0, nb_majeurs=1,
        ),
        forces=[
            Reason(dimension="traction", label="Traction", score=82.0,
                   preuve="+10 : Revenu établi (200,000 EUR)."),
            Reason(dimension="equipe", label="Équipe", score=75.0,
                   preuve="+15 : Profil technique présent dans l'équipe fondatrice."),
            Reason(dimension="business_model", label="Business Model", score=70.0,
                   preuve="+10 : Burn multiple de 1.2, capital efficace."),
        ],
        faiblesses=[
            Reason(dimension="marche", label="Marché", score=42.0,
                   preuve="TAM calculé uniquement en top-down, sans validation bottom-up."),
            Reason(dimension="concurrence", label="Concurrence", score=52.0,
                   preuve="Base neutre : 60."),
            Reason(dimension="go_to_market", label="Go-to-Market", score=55.0,
                   preuve="Base neutre : 60."),
        ],
        question_decisive=KeyQuestion(
            question="Le moteur de croissance est-il identifié et répétable, ou la traction est-elle un agrégat de coups uniques ?",
            bonne_reponse="", mauvaise_reponse="", origine="dimension_faible",
        ),
        dashboard=[
            DashboardRow(metrique="ARR", valeur="200 000 EUR", statut="DANS_LA_NORME", benchmark="2,5-3,5M USD"),
            DashboardRow(metrique="Churn", valeur="2%/mois", statut="TOP_QUARTILE", benchmark="< 2%/mois"),
            DashboardRow(metrique="Burn multiple", valeur=None, statut="ABSENT", benchmark="~1,2x"),
            DashboardRow(metrique="NRR", valeur="105%", statut="NON_EVALUABLE", benchmark=None),
        ],
        dimensions=[],
        red_flags=[],
        incoherences=[],
        donnees_manquantes=[],
        contre_analyse=ReviewBlock(
            disponible=False,
            bandeau="Contre-analyse indisponible (erreur API).",
            contenu=None,
        ),
        questions_fondateurs=[],
        annexes=Annexes(methodologie="", limites="", extraction_brute={}),
    )


def test_render_markdown_golden():
    produced = render_markdown(make_memo())
    expected = GOLDEN.read_text(encoding="utf-8")
    assert produced == expected
