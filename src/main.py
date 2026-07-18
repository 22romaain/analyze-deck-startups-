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
from src.review import make_review_generator


def _load_doctrine_retriever() -> tuple[object | None, str]:
    """Prépare la source de doctrine RAG pour le mémo, de façon tolérante.

    Renvoie (retriever, message). retriever vaut None si l'index est absent ou vide :
    le mémo se génère alors sans citation. L'appel externe (RAG) est protégé, une
    erreur désactive la doctrine au lieu de faire échouer le pipeline.
    """
    try:
        from src.rag.index import search
        probe = search("marché", k=1)  # sonde : l'index répond-il et contient-il des passages ?
    except Exception as exc:  # index illisible, dépendance manquante, etc.
        return None, f"Doctrine RAG desactivee (index indisponible : {exc})."
    if not probe:
        return None, "Doctrine RAG desactivee (index vide : lancer build_index sur courses/)."

    def retrieve(query: str, k: int):
        try:
            return search(query, k)
        except Exception:
            return []  # une requête ratée ne prive pas le mémo des autres citations

    return retrieve, "Doctrine RAG activee (citations des cours en appui des dimensions)."


def build_and_write_memo(
    deck: DeckAnalysis,
    signals: DeckSignals,
    config: MemoConfig,
    output_dir: Path | None = None,
    retriever: object | None = None,
    review_generator=None,
) -> tuple[MemoData, Path, Path]:
    """Assemble le mémo à partir des signaux et l'écrit (Markdown + Word).

    Le scoring et le mémo sont déterministes. `retriever` (optionnel) = doctrine RAG.
    `review_generator` (optionnel) = fonction (deck, analysis) -> contre-analyse LLM ;
    None ou échec -> section 6 en mode dégradé. Injectables : sans eux, tout se
    construit hors ligne (testable). Round inconnu -> dégrade proprement (poids vides).
    """
    analysis = run_analysis(signals, deck.detected_round, deck.ask_amount)
    review = review_generator(deck, analysis) if review_generator is not None else None
    memo = build_memo_data(deck, analysis, signals, config, review=review, retriever=retriever)
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

    retriever, doctrine_msg = _load_doctrine_retriever()
    print(doctrine_msg)
    review_generator = make_review_generator()
    print("Contre-analyse LLM activee." if review_generator else "Contre-analyse LLM desactivee (pas de cle).")

    try:
        memo, md_path, docx_path = build_and_write_memo(
            deck, signals, config, retriever=retriever, review_generator=review_generator)
    except RuntimeError as exc:
        print(f"Écriture du mémo impossible : {exc}")
        sys.exit(1)

    print(f"\nVerdict : {memo.verdict.decision} (score {memo.verdict.score_global:.0f}/100)")
    print(f"Mémo Markdown : {md_path}")
    print(f"Mémo Word : {docx_path}")


if __name__ == "__main__":
    main()
