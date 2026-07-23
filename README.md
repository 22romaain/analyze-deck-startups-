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

## Système de notation

Chaque dimension est notée sur 100. Tout part d'une **base neutre de 60/100**
(`BASELINE_SCORE` dans `src/analysis.py`). Ce 60 n'est pas arbitraire : c'est le
point de départ « ni preuve forte, ni alerte ». Un deck qui ne dit rien de
remarquable sur une dimension la laisse à 60. Les bonus et les pénalités font
ensuite bouger la note à partir de là.

**Pourquoi 60 et pas 50 ?** La grille du référentiel
(`criteria/criteres_analyse_vc.md`) définit quatre paliers par dimension :
Excellent (80-100), **Bon (60-79)**, Moyen (40-59), Faible (0-39). 60 n'est donc
pas le milieu de l'échelle : c'est le **plancher du palier « Bon »**. Le choix
encode un léger bénéfice du doute : un deck qui arrive jusqu'au pitch est présumé
« correct » par défaut, à charge pour les red flags et les données manquantes de
le faire descendre vers « Moyen » ou « Faible ». Partir de 50 reviendrait à le
présumer médiocre. Ce 60 est aussi cohérent avec le verdict : une dimension
neutre laisse le deck en zone `APPROFONDIR` (creuser), pas près du rejet.

- **Bonus** : une preuve positive dans le deck (ex : profil technique dans
  l'équipe, revenu établi) ajoute des points au-dessus de 60.
- **Red flags, par plafonnement et non par soustraction** (référentiel §5.2) :
  - `MINEUR` : -10 sur la dimension.
  - `MAJEUR` : plafonne la dimension à 40.
  - `CRITIQUE` (ou 3 `MAJEURS` cumulés) : plafonne le **score global** à 35.

Le **score global** est la moyenne des dimensions pondérée par les poids du round
(les poids changent selon le stade : la traction pèse lourd en série A, l'équipe
au pre-seed). Il est ensuite traduit en grade lisible :

| Score | Grade |
| --- | --- |
| ≥ 80 | A |
| ≥ 65 | B |
| ≥ 50 | C |
| ≥ 40 | D |
| < 40 | E |

Enfin le **verdict** : `PASSER` sous 40 (ou dès un red flag critique),
`POURSUIVRE` au-dessus de 65 sans critique, `APPROFONDIR` entre les deux. Tous ces
seuils vivent dans `config/memo_config.json`, jamais codés en dur.

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
