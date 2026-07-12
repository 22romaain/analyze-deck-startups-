"""Point d'entrée CLI : pipeline complet PDF -> mémo (Markdown + Word).

Flux : ingestion (PDF -> images) -> extraction (LLM -> DeckAnalysis + DeckSignals)
-> scoring déterministe -> assemblage du mémo -> écriture des deux fichiers.
"""

import sys
from pathlib import Path

from src.analysis import run_analysis
from src.extraction import analyze_deck
from src.ingestion import load_deck
from src.models import DeckAnalysis, DeckSignals
from src.output.memo_data import MemoConfig, MemoData, build_memo_data, load_memo_config
from src.output.render_docx import render_docx
from src.output.render_markdown import write_markdown


def build_and_write_memo(
    deck: DeckAnalysis,
    signals: DeckSignals,
    config: MemoConfig,
    output_dir: Path | None = None,
) -> tuple[MemoData, Path, Path]:
    """Partie déterministe du pipeline : scoring -> mémo -> écriture des 2 fichiers.

    Aucun appel LLM ici, donc testable de bout en bout. Le round vient du deck
    (detected_round) ; un round inconnu dégrade proprement (poids vides) sans planter.
    """
    analysis = run_analysis(signals, deck.detected_round)
    memo = build_memo_data(deck, analysis, signals, config)
    md_path = write_markdown(memo, output_dir)
    docx_path = render_docx(memo, output_dir)
    return memo, md_path, docx_path


def main() -> None:
    """Enveloppe CLI : arguments, appels externes, messages et codes de sortie."""
    if len(sys.argv) != 2:
        print("Usage : python -m src.main chemin/vers/deck.pdf")
        sys.exit(1)
    pdf_path = sys.argv[1]

    try:
        config = load_memo_config()
    except ValueError as exc:
        print(f"Config mémo invalide : {exc}")
        sys.exit(1)

    try:
        print(f"Chargement du deck : {pdf_path}")
        slides = load_deck(pdf_path)
        print(f"{len(slides)} slides détectées.")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Ingestion impossible : {exc}")
        sys.exit(1)

    try:
        print("Analyse en cours via Mistral...")
        deck, signals, mode = analyze_deck(slides, pdf_path=pdf_path)
        print(f"Mode utilisé : {mode}")
    except Exception as exc:  # appel externe : message clair plutôt qu'une trace brute
        print(f"Extraction impossible : {exc}")
        sys.exit(1)

    try:
        memo, md_path, docx_path = build_and_write_memo(deck, signals, config)
    except RuntimeError as exc:
        print(f"Écriture du mémo impossible : {exc}")
        sys.exit(1)

    print(f"\nVerdict : {memo.verdict.decision} (score {memo.verdict.score_global:.0f}/100)")
    print(f"Mémo Markdown : {md_path}")
    print(f"Mémo Word : {docx_path}")


if __name__ == "__main__":
    main()
