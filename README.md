# Analyseur de deck startup (logique fonds VC)

Analyse un pitch deck comme un analyste VC et produit un mémo d'investissement
structuré. Le flux : PDF → extraction par LLM vision → signaux structurés →
scoring et red flags déterministes → mémo (Markdown + Word), avec citations via un RAG local.

## Ce que fait l'outil

- **Extraction** : lit le deck (mode texte ou vision) via l'API Mistral et en
  tire les dimensions VC (équipe, marché, traction, business model, etc.) plus
  des signaux chiffrés typés.
- **Scoring déterministe** (aucun LLM) : note chaque dimension, applique les red
  flags du référentiel (dans le code), calcule un score global pondéré par
  le round.
- **Cap table** : dilution (pre-money), simulation de waterfall
  (liquidation preferences), alertes sur la détention fondateurs.
- **RAG** : cite la doctrine VC (cours perso indexés localement) en face de
  chaque dimension.
- **Sortie** : un mémo `.md` et `.docx` (verdict, dimensions, red flags,
  contre-analyse).


## Utilisation

**Analyser un deck (pipeline complet)** — écrit le mémo dans `output/` :

```bash
./venv/bin/python -m src.main chemin/vers/deck.pdf
```

## Corpus RAG (doctrine)

Les cours personnels vivent dans `courses/` (contenu ignoré par git, en local). Après avoir
ajouté ou modifié des documents (`.md`, `.txt`, `.pdf`, `.docx`), reconstruire
l'index :

```python
from src.rag.index import build_index
build_index("courses")
```

## Architecture

Modules séparés, chacun testable seul :

- `src/ingestion.py` : PDF → texte / images de slides.
- `src/extraction.py` : appel LLM → `DeckAnalysis` + `DeckSignals`.
- `src/analysis.py` : scoring, red flags, cap table (code déterministe).
- `src/captable.py` : moteurs de dilution et de waterfall.
- `src/rag/` : indexation et recherche de la doctrine (ChromaDB, embeddings ONNX).
- `src/output/` : assemblage du mémo et rendus Markdown / Word.
- `app.py` : interface Streamlit.

## Notes

- Tier gratuit Mistral : ~2 requêtes/minute. Les appels sont groupés et
  réessayés automatiquement en cas de rate limit.
- Le scoring, la cap table et les red flags sont du code déterministe : mêmes
  entrées, même résultat. Le LLM ne sert qu'à lire les slides.
