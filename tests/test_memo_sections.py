"""Tests de la tranche 4 : builders des sections 2 à 5 (dashboard, dimensions,
red flags, données manquantes)."""

from src.analysis import run_analysis
from src.models import DeckSignals, RedFlag
from src.output.memo_data import (
    REVIEW_BANDEAU_DISPONIBLE,
    REVIEW_BANDEAU_INDISPONIBLE,
    _grade_for,
    build_dashboard,
    build_dimensions,
    build_founder_questions,
    build_missing_data,
    build_red_flag_rows,
    build_review_block,
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
    # Détention fondateurs fournie (70% > seuil série A) pour isoler ce seul flag :
    # sans elle, la règle cap table §4.3 ajouterait un flag d'absence sur equipe.
    signals = DeckSignals(product_is_tech=True, has_technical_founder=False,
                          founder_ownership_pct=70.0)
    analysis = run_analysis(signals, "serie-a")
    dims = {d.dimension: d for d in build_dimensions(analysis, CONFIG)}
    inline = dims["equipe"].red_flags_inline
    assert len(inline) == 1 and inline[0].severity == "CRITIQUE"


def test_cite_doctrine_filtre_les_matchs_trop_lointains():
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [
            SearchHit(text="Pertinent.", source="c.md", section="A", distance=0.9),   # gardé
            SearchHit(text="Hors sujet.", source="c.md", section="B", distance=1.5),  # filtré
        ]

    cites = cite_doctrine("marché", retriever=fake_retriever)
    assert len(cites) == 1 and cites[0].section == "A"


def test_cite_doctrine_seuil_ajustable():
    from src.output.memo_data import cite_doctrine
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="Loin.", source="c.md", section="B", distance=1.5)]

    # Seuil large : le passage lointain passe. Seuil par défaut : il est filtré.
    assert len(cite_doctrine("m", retriever=fake_retriever, max_distance=2.0)) == 1
    assert cite_doctrine("m", retriever=fake_retriever) == []


def test_dimensions_doctrine_citee_pour_une_seule_dimension():
    # Faux retriever déterministe : la couche mémo se teste sans ChromaDB ni réseau.
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="Exiger un TAM bottom-up. " * 40,  # long -> sera tronqué
                          source="cours_marche.md", section="TAM", distance=0.12)]

    analysis = run_analysis(DeckSignals(), "serie-a")
    dims = {d.dimension: d for d in build_dimensions(
        analysis, CONFIG, retriever=fake_retriever, doctrine_dimensions={"marche"})}
    # Seule 'marche' est enrichie ; les autres dimensions restent sans doctrine.
    assert len(dims["marche"].doctrine) == 1
    assert dims["marche"].doctrine[0].source == "cours_marche.md"
    assert len(dims["marche"].doctrine[0].extrait) <= 300  # extrait borné
    assert dims["traction"].doctrine == []


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


# --- Contre-analyse (section 6) ---

def test_review_block_indisponible():
    r = build_review_block(None)
    assert r.disponible is False
    assert r.bandeau == REVIEW_BANDEAU_INDISPONIBLE
    assert r.contenu is None


def test_review_block_disponible():
    r = build_review_block("Le moat repose sur un accord exclusif non contractualise.")
    assert r.disponible is True
    assert r.bandeau == REVIEW_BANDEAU_DISPONIBLE
    assert "moat" in r.contenu


# --- Questions fondateurs (section 7) ---

def test_founder_questions_priorite_et_limite():
    # NRR à 80% -> red flag CRITIQUE sur business_model ; signaux surtout absents.
    signals = DeckSignals(nrr_pct=80.0)
    analysis = run_analysis(signals, "serie-a")
    questions = build_founder_questions(analysis, signals, CONFIG)
    assert len(questions) == 5  # plafonné à 5
    assert questions[0].origine == "red_flag"
    assert questions[0].question == CONFIG.questions_referentiel["serie-a"]["business_model"].question
    # Textes uniques (déduplication).
    assert len({q.question for q in questions}) == 5
    # Le reste vient des données manquantes.
    assert any(q.origine == "donnee_manquante" for q in questions)
