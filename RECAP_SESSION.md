# Récap de session — reprise dans une nouvelle fenêtre

À lire en premier. Le détail long vit dans `historique.docx` (journal de bord).

Dernière session : **23 juillet 2026**. Tests au vert : **111 passed**. Pivot **terminé**.

---

## 1. Le pivot (fait)

Le score chiffré a été **abandonné** puis **retiré du code**. Un nombre sur 100 ne tient
ni le flair VC ni la combinaison au cas par cas. À la place : une **analyse qualitative**
faite de **constats tagués** (pros/cons), une **grille d'attendus par round**, et des
**critères éditables à la main**. Voir mémoire `pivot-analyse-qualitative`.

**Règle de recommandation** (sans score) : un rédhibitoire → **APPROFONDIR** (à instruire
et justifier, jamais un rejet auto) ; sinon une faiblesse → APPROFONDIR ; sinon POURSUIVRE.
L'outil ne prononce pas de « non » définitif.

---

## 2. Architecture actuelle (carte du code)

| Brique | Fichier | Rôle |
|---|---|---|
| `Finding`, `FINDING_CATEGORIES` | `src/models.py` | Constat tagué + table des 6 catégories (polarité/label/ordre) |
| `criteres.yaml` | `config/criteres.yaml` | **Doctrine éditable** : un signal, une condition → un constat. 14 critères de départ |
| `Critere`, `charger_criteres`, `evaluer_criteres` | `src/criteres.py` | Schéma, chargeur validant, évaluateur |
| `collecter_red_flags`, `redflag_to_finding`, `collecter_findings` | `src/analysis.py` | Détecteurs code (red flags, incohérences, cap table) → constats, fusionnés avec le YAML |
| `Synthese`, `build_synthese`, `recommander` | `src/output/synthese.py` | Pros/cons + recommandation |
| `build_grille`, `build_dimensions_qualitatives`, `build_memo_data`, `MemoData` | `src/output/memo_data.py` | Grille, dimensions sans score, agrégat |
| `render_markdown/docx/pdf/streamlit` | `src/output/` | 4 rendus (docx et pdf dérivent du markdown) |
| `charger_these`, `rassembler_contexte_cours`, `generate_review` | `src/review.py` | **Couche de jugement LLM** : thèse + cours (RAG) → lecture au regard de la thèse + contre-analyse |
| `these_investissement.md` | `config/` | **Thèse éditable** en prose libre (vide par défaut) |

**Couche de jugement LLM (consultative, option A).** Un appel LLM reçoit les faits
déterministes + la thèse + les extraits de cours pertinents (RAG, sous budget de tokens)
et rend deux volets rédigés (lecture au regard de la thèse, contre-analyse). Consultatif :
n'entre PAS dans le verdict déterministe (qui reste l'ancre auditable). S'active avec
`MISTRAL_API_KEY` + index RAG ; sinon mode dégradé. **Aussi bon que la thèse** : tant que
`these_investissement.md` est vide, le LLM raisonne sur les cours seuls.

`run_analysis` ne calcule plus de score : il livre round + red flags. `ROUND_WEIGHTS`
existe encore mais ne sert plus qu'à **ordonner** l'affichage des dimensions.

Les 6 catégories : `redhibitoire`, `vigilance`, `faiblesse` (négatif) ;
`avantage_competitif`, `atout_equipe` (positif) ; `a_creuser` (neutre).
Mapping sévérité→catégorie : CRITIQUE→redhibitoire, MAJEUR→faiblesse, MINEUR→vigilance.

Deux canaux éditables : **criteres.yaml** (structuré, lié aux signaux) et
**these_investissement.md** (prose libre pour le LLM). Le mémo affiche un disclaimer :
analyse fondée sur les critères subjectifs du créateur + principes VC du référentiel.

---

## 3. Dette assumée (à traiter si tu veux)

- **Revenu établi comme atout** : l'ancien bonus de traction (avec garde-fou « 1 USD »)
  a disparu au nettoyage. À re-brancher comme critère ou détecteur si le revenu doit
  compter positivement.
- **Garnir `criteres.yaml`** au-delà des 14 critères, et **écrire la thèse**.
- **Traçabilité slide** des constats : non reliée.
- **Doctrine ciblée par dimension** (`doctrine_dimensions` restreint) : plus de test
  unitaire dédié après le nettoyage (le passthrough retriever reste testé).

---

## 4. État Git et méthode

- Poussé sur GitHub à la clôture de cette session (voir journal pour le détail).
- Journal `historique.docx` à jour (entrée de clôture en tête, sans accents).
- Méthode : petites tranches, validation, expliquer avant de coder, récap de fin d'étape.
  Réponses en français, pas de tirets cadratins. Voir mémoire `explication-fin-etape`.
- Tests : `./venv/bin/python -m pytest -q`. App : `streamlit run app.py`.
- Note : un test RAG (`test_rag_index`) peut clignoter selon l'ordre (état ChromaDB
  partagé) ; il passe en isolation. Pré-existant, sans rapport avec le pivot.
