"""Test d'intégration : assemblage complet du mémo (build_memo_data) de bout en bout."""

from datetime import date

from src.analysis import run_analysis
from src.main import build_and_write_memo
from src.models import DeckAnalysis, DeckSignals
from src.output.memo_data import build_memo_data, load_memo_config
from src.output.render_markdown import render_markdown

CONFIG = load_memo_config()


def make_deck() -> DeckAnalysis:
    """Un DeckAnalysis minimal mais complet (les 12 champs sont requis)."""
    return DeckAnalysis(
        equipe="Deux fondateurs, ex-Stripe.", probleme="Reconciliation comptable manuelle.",
        solution="Automatisation par IA.", marche="TAM 12Md EUR.",
        business_model="SaaS par siege.", traction="200k EUR ARR.",
        concurrence="Quelques acteurs legacy.", go_to_market="Outbound + product-led.",
        financials="Runway 14 mois.", ask="Levee pour l'expansion EU.",
        detected_round="serie-a", ask_amount="8M EUR",
    )


def test_build_memo_data_assemblage_complet():
    # NRR à 80% -> red flag CRITIQUE -> verdict PASSER.
    signals = DeckSignals(nrr_pct=80.0, churn_rate_pct=1.5, churn_period="monthly")
    analysis = run_analysis(signals, "serie-a")
    memo = build_memo_data(make_deck(), analysis, signals, CONFIG, today=date(2026, 7, 12))

    assert memo.round == "serie-a"
    assert memo.ask_amount == "8M EUR"
    assert memo.societe == CONFIG.societe_fallback
    assert memo.date == date(2026, 7, 12)
    assert memo.verdict.decision == "PASSER"  # dominé par le red flag critique
    assert memo.contre_analyse.disponible is False
    assert len(memo.forces) == 3
    assert memo.annexes.extraction_brute["detected_round"] == "serie-a"

    # Le mémo complet se rend sans exception et commence par le titre.
    md = render_markdown(memo)
    assert md.startswith("# Mémo d'investissement")
    assert "## Annexes" in md


def test_build_and_write_memo_transmet_le_retriever(tmp_path):
    # Câblage réel testé hors ligne : un faux retriever suffit à prouver le passthrough
    # CLI -> build_memo_data -> build_dimensions -> rendu, sans ChromaDB.
    from src.rag.index import SearchHit

    def fake_retriever(query, k):
        return [SearchHit(text="Doctrine de reference. " * 20, source="cours.md",
                          section="S1", distance=0.2)]

    memo, md_path, _ = build_and_write_memo(
        make_deck(), DeckSignals(), CONFIG, output_dir=tmp_path, retriever=fake_retriever)
    # Sans doctrine_dimensions, toutes les dimensions du round sont citées.
    assert all(d.doctrine for d in memo.dimensions)
    assert "Doctrine VC :" in md_path.read_text(encoding="utf-8")


def test_build_memo_data_avec_contre_analyse():
    signals = DeckSignals()
    analysis = run_analysis(signals, "serie-a")
    memo = build_memo_data(
        make_deck(), analysis, signals, CONFIG, review="Le moat n'est pas defendable.",
    )
    assert memo.contre_analyse.disponible is True
    assert "moat" in memo.contre_analyse.contenu


def test_build_and_write_memo_ecrit_les_deux_fichiers(tmp_path):
    # Pipeline déterministe (sans LLM) : scoring -> mémo -> écriture des 2 fichiers.
    signals = DeckSignals(nrr_pct=80.0)
    memo, md_path, docx_path = build_and_write_memo(
        make_deck(), signals, CONFIG, output_dir=tmp_path,
    )
    assert md_path.exists() and md_path.suffix == ".md"
    assert docx_path.exists() and docx_path.suffix == ".docx"
    assert md_path.stem == docx_path.stem  # même nom, extensions différentes
    assert md_path.read_text(encoding="utf-8").startswith("# Mémo d'investissement")
