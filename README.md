# Analyze deck startups

**Objectif** : à partir d'un pitch deck PDF, produire une grille d'analyse VC neutre (ce qu'il faut regarder, forces, faiblesses), sans note ni recommandation d'investir.

**Fonctionnement**, en 3 étapes :
1. `extraction/` : lit le deck slide par slide avec 3 sources indépendantes (OCR Mistral, texte PDF via PyMuPDF, vision LLM), les fusionne et remplit une fiche structurée (Pydantic).
2. `analyse/` : un appel LLM confronte la fiche au référentiel `referentiel.md` (benchmarks VC) et produit la grille d'analyse.
3. `restitution/` : met la grille en forme dans un mémo `.md` (option PDF), écrit dans `output/`.

**Outils** : Python 3.12, uv, Mistral (`mistral-ocr-latest`, `mistral-medium-latest`), PyMuPDF, Pydantic, Streamlit, markdown-pdf. 

**Lancer** : `uv run app.py decks/mon_deck.pdf [--pdf]`, ou l'interface avec `uv run streamlit run interface.py`.
