"""Point d'entrée CLI : orchestre le pipeline ingestion -> extraction -> affichage."""

import sys

from src.ingestion import load_deck
from src.extraction import analyze_deck


def main() -> None:
    """Fonction principale. Lit le chemin du PDF depuis les arguments CLI."""

    # sys.argv contient les arguments passés en ligne de commande
    # sys.argv[0] = le nom du script, sys.argv[1] = le premier argument (notre PDF)
    if len(sys.argv) != 2:
        print("Usage : python -m src.main chemin/vers/deck.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Étape 1 : charger le PDF et rendre chaque page en image
    print(f"Chargement du deck : {pdf_path}")
    slides = load_deck(pdf_path)
    print(f"{len(slides)} slides détectées.")

    # Étape 2 : envoyer les slides à Mistral et récupérer l'analyse
    print("Analyse en cours via Mistral...")
    analysis, mode = analyze_deck(slides, pdf_path=pdf_path)
    print(f"Mode utilisé : {mode}")

    # Étape 3 : afficher le résultat JSON formaté
    print("\n--- Analyse du deck ---")
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
