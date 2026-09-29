"""Golden test du rendu Markdown (sections 0-1-2).

On fige une sortie de référence dans tests/golden/memo_min.md. Toute dérive future
casse le test : on doit alors regénérer sciemment le golden.
"""

from datetime import date
from pathlib import Path

from src.captable import DilutionResult
from src.models import Finding
from src.output.memo_data import (
    DISCLAIMER,
    REVIEW_BANDEAU_INDISPONIBLE,
    Annexes,
    CapTableSection,
    DeckFigureRow,
    DimensionQualitative,
    GrilleRow,
    MemoData,
    ReviewBlock,
)
from src.output.synthese import Recommandation, Synthese
from src.output.render_markdown import render_markdown

GOLDEN = Path(__file__).parent / "golden" / "memo_min.md"


def make_memo() -> MemoData:
    """Un MemoData complet et stable (analyse qualitative), fixture du golden test.

    Les dimensions ont narratif=None par défaut (le test 'sans narratif' s'appuie
    dessus) ; un test dédié le renseigne pour vérifier son rendu.
    """
    ltv = Finding(dimension="business_model", categorie="redhibitoire",
                  message="LTV/CAC de 0.7 : destruction de valeur à chaque acquisition client.",
                  source="critere:unit_economics_ltv_cac_destruction")
    marge = Finding(dimension="business_model", categorie="avantage_competitif",
                    message="Marge brute de 82%, dans la norme d'un modèle logiciel.",
                    source="critere:marge_brute_saine")
    exit_founder = Finding(dimension="equipe", categorie="atout_equipe",
                           message="Track record : au moins un fondateur a déjà réalisé une sortie.",
                           source="critere:equipe_exit_precedente")
    tam = Finding(dimension="marche", categorie="vigilance",
                  message="Aucune méthode de dimensionnement du marché explicite.",
                  source="detecteur")
    incoherence = Finding(dimension="traction", categorie="vigilance",
                          message="Incohérence interne : revenu de ~2.0M EUR anormalement élevé pour un serie-a.",
                          source="detecteur")
    return MemoData(
        societe="Acme SaaS",
        round="serie-a",
        ask_amount="8M EUR",
        date=date(2026, 7, 12),
        disclaimer=DISCLAIMER,
        synthese=Synthese(
            atouts=[marge, exit_founder],
            points_negatifs=[ltv, tam],
            a_creuser=[],
            recommandation=Recommandation(
                decision="APPROFONDIR",
                justification="APPROFONDIR : 1 constat(s) rédhibitoire(s) à instruire et à justifier avant toute décision.",
                nb_redhibitoires=1, nb_faiblesses=0, nb_atouts=2,
            ),
        ),
        grille=[
            GrilleRow(label="ARR", criticite="MAJEUR", statut="PRESENT", valeur="200 000 EUR"),
            GrilleRow(label="Churn ou rétention", criticite="MAJEUR", statut="INCONNU", valeur=None),
            GrilleRow(label="Cap table (part fondateurs)", criticite="MINEUR", statut="INCONNU", valeur=None),
        ],
        chiffres_deck=[
            DeckFigureRow(libelle="CAGR", valeur="140 %", periode="2021-2024", slide=7),
            DeckFigureRow(libelle="NPS", valeur="62", periode=None, slide=None),
        ],
        dimensions=[
            DimensionQualitative(dimension="business_model", label="Business Model",
                                 narratif=None, findings=[ltv, marge]),
            DimensionQualitative(dimension="equipe", label="Équipe",
                                 narratif=None, findings=[exit_founder]),
        ],
        incoherences=[incoherence],
        contre_analyse=ReviewBlock(
            disponible=False,
            bandeau=REVIEW_BANDEAU_INDISPONIBLE,
            contenu=None,
        ),
        cap_table=CapTableSection(
            calculable=True, donnees_absentes=[],
            pre_money=24_000_000.0, amount=8_000_000.0, founder_pct_pre=60.0,
            dilution=DilutionResult(
                post_money=32_000_000.0, new_investor_pct=25.0, option_pool_pct=0.0,
                founder_pct_post=45.0, founder_dilution_points=15.0,
            ),
            waterfall=None,
        ),
        annexes=Annexes(
            methodologie="Trois couches : extraction LLM vision, analyse déterministe en constats, mise en forme.",
            limites="Traçabilité slide reportée. Contre-analyse absente.",
            extraction_brute={"detected_round": "serie-a", "ask": "Levée de 8M EUR pour l'expansion EU."},
        ),
    )


def test_render_markdown_golden():
    produced = render_markdown(make_memo())
    expected = GOLDEN.read_text(encoding="utf-8")
    assert produced == expected


def test_render_degradation_contre_analyse():
    # Sans analyse LLM : l'encart dégradé apparaît (bandeau "indisponible").
    md = render_markdown(make_memo())
    assert "indisponible" in md


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


def test_render_markdown_inventaire_absent_si_vide():
    # Sans chiffre brut, la section 'ce que le deck affirme' ne doit pas apparaître.
    memo = make_memo()
    memo.chiffres_deck = []
    md = render_markdown(memo)
    assert "## Ce que le deck affirme" not in md
    assert "\n\n\n" not in md  # pas de ligne blanche parasite laissée par le bloc vide
