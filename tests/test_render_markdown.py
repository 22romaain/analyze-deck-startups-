"""Golden test du rendu Markdown (sections 0-1-2).

On fige une sortie de référence dans tests/golden/memo_min.md. Toute dérive future
casse le test : on doit alors regénérer sciemment le golden.
"""

from datetime import date
from pathlib import Path

from src.output.memo_data import (
    Annexes,
    DashboardRow,
    DimensionSection,
    KeyQuestion,
    MemoData,
    MissingData,
    Reason,
    RedFlagRow,
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
        dimensions=[
            DimensionSection(
                dimension="traction", label="Traction", score=82.0, weight=0.30, grade="A",
                regle_appliquee=["Base neutre : 60.", "+10 : Revenu établi (200,000 EUR)."],
                red_flags_inline=[RedFlagRow(
                    severity="MINEUR", dimension="traction", label_dimension="Traction",
                    message="Incohérence interne : revenu de ~2.0M EUR anormalement élevé pour un serie-a.",
                    est_incoherence=True,
                )],
            ),
            DimensionSection(
                dimension="business_model", label="Business Model", score=70.0, weight=0.20, grade="B",
                regle_appliquee=["Base neutre : 60.", "+10 : Burn multiple de 1.2, capital efficace."],
                red_flags_inline=[],
            ),
        ],
        red_flags=[
            RedFlagRow(severity="MAJEUR", dimension="marche", label_dimension="Marché",
                       message="TAM calculé uniquement en top-down, sans validation bottom-up.",
                       est_incoherence=False),
            RedFlagRow(severity="MINEUR", dimension="traction", label_dimension="Traction",
                       message="Incohérence interne : revenu de ~2.0M EUR anormalement élevé pour un serie-a.",
                       est_incoherence=True),
        ],
        incoherences=[
            RedFlagRow(severity="MINEUR", dimension="traction", label_dimension="Traction",
                       message="Incohérence interne : revenu de ~2.0M EUR anormalement élevé pour un serie-a.",
                       est_incoherence=True),
        ],
        donnees_manquantes=[
            MissingData(label="Cap table (part fondateurs)", criticite="MINEUR",
                        justification="Donnée secondaire attendue au stade serie-a et absente du deck. L'absence d'une donnée est un signal, pas un neutre (référentiel §1.1)."),
        ],
        contre_analyse=ReviewBlock(
            disponible=False,
            bandeau="Contre-analyse indisponible (erreur API).",
            contenu=None,
        ),
        questions_fondateurs=[
            KeyQuestion(
                question="Le burn multiple : combien coûte 1 EUR d'ARR net nouveau ?",
                bonne_reponse="", mauvaise_reponse="", origine="red_flag",
            ),
            KeyQuestion(
                question="Donnée attendue absente du deck : Cap table (part fondateurs). Pourquoi, et quelle est la valeur réelle ?",
                bonne_reponse="", mauvaise_reponse="", origine="donnee_manquante",
            ),
        ],
        annexes=Annexes(
            methodologie="Trois couches : extraction LLM vision, scoring déterministe, mise en forme.",
            limites="Traçabilité slide reportée. Contre-analyse absente.",
            extraction_brute={"detected_round": "serie-a", "ask": "Levée de 8M EUR pour l'expansion EU."},
        ),
    )


def test_render_markdown_golden():
    produced = render_markdown(make_memo())
    expected = GOLDEN.read_text(encoding="utf-8")
    assert produced == expected


def test_render_degradation_contre_analyse():
    # Sans contre-analyse : l'encart dégradé apparaît, aucune trace du bandeau "disponible".
    md = render_markdown(make_memo())
    assert "Contre-analyse indisponible (erreur API)." in md


def test_render_markdown_affiche_doctrine():
    # Une dimension portant une citation la voit rendue sous un bloc "Doctrine VC".
    from src.output.memo_data import DoctrineCitation

    memo = make_memo()
    memo.dimensions[0].doctrine = [DoctrineCitation(
        source="cours_marche.md", section="Dimensionner un TAM",
        extrait="Exiger un TAM bottom-up plutot qu'un pourcentage d'un marche geant.",
        distance=0.12,
    )]
    md = render_markdown(memo)
    assert "Doctrine VC :" in md
    assert "(cours_marche.md, §Dimensionner un TAM)" in md
    assert "bottom-up" in md


def test_render_markdown_sans_doctrine_inchange():
    # Sans citation, aucun bloc doctrine : garantit que le mémo par défaut ne régresse pas.
    md = render_markdown(make_memo())
    assert "Doctrine VC :" not in md
    assert "Critique générée par LLM" not in md
