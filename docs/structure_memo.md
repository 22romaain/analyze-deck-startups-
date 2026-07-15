# Spécification du module `sortie` (mémo d'investissement)

Version 1 (adaptée au code réel). Source de vérité pour l'étape 3. En cas de
doute pendant l'implémentation, ce document fait foi.

## 0. Objet et périmètre

Assembler l'extraction, le scoring et (quand elle existera) la contre-analyse
en un mémo d'investissement structuré, rendu en Markdown puis en Word (.docx).
Le PDF est hors périmètre.

Principe d'architecture : **un agrégat, des renderers**.
- `build_memo_data(...) -> MemoData` : toute la logique de préparation (tri,
  sélection, verdict, statuts). Analogie : l'onglet de calcul du modèle.
- `render_markdown(memo)` et `render_docx(memo, path)` : mise en forme pure,
  aucun calcul. Analogie : les mises en page d'impression. Le docx n'est PAS
  une conversion du markdown ; les deux lisent le même `MemoData`.

## 1. Décisions d'adaptation (le delta assumé)

La consigne initiale suppose des briques amont qui n'existent pas encore. On a
choisi **adapter + dégrader**. Voici le contrat réel, écart par écart. Ce sont
les seuls points où cette spec s'écarte de la consigne ; ils priment.

| Consigne initiale | Réalité étape 1-2 | Décision pour l'étape 3 |
|---|---|---|
| Extraction avec slide source, confiance, présence | `DeckAnalysis` (10 dimensions texte) + `DeckSignals` (signaux typés) sans slide ni confiance | Traçabilité slide **reportée** (voir §9). Les valeurs s'affichent sans slide, marquées `source: deck` sans numéro. |
| `ScoringResult` | `AnalysisResult(round, global_score, dimension_scores[], red_flags[])` | On lit `AnalysisResult`. |
| Red flags avec `id`, `preuve`, `slide` | `RedFlag(dimension, severity, message)` | On lit ces 3 champs. Pas d'`id` référentiel ; l'effet inline s'appuie sur `message` et `severity`. |
| `DevilsAdvocateReview` (appel LLM) | n'existe pas | Section 6 **toujours en mode dégradé** (encart indisponible) tant que la brique n'existe pas. `build_memo_data` accepte `review=None`. |
| Benchmarks structurés par round dans `criteria/` | doctrine en **texte** dans un seul `.md` | Les métriques attendues et bornes benchmarks sont **encodées dans la config** (sourcées du référentiel §5.2/5.4 et des seuils déjà présents dans `analysis.py`). Métrique sans benchmark = statut `NON_EVALUABLE`. |
| Effet red flag « plafonnée à 40 par RF-A12 » (mécanique §5.2) | `analysis.py` fait une soustraction (CRITIQUE -35, MAJEUR -18, MINEUR -8), pas de plafonnement | Le mémo **reflète la mécanique réellement appliquée** (soustraction). L'écart §5.2 vs code est un **point ouvert** (§14), non traité ici. |

## 2. Sources de données réelles (mapping objet -> section)

- En-tête : `DeckAnalysis.detected_round`, `ask_amount` ; nom société à extraire
  (voir §7 config, champ à ajouter côté extraction plus tard ; pour l'instant
  `config` fournit un fallback ou on lit un champ narratif).
- Verdict (§0 mémo) : `AnalysisResult.global_score` + sévérités des `red_flags`.
- Recommandation : `dimension_scores` (forces/faiblesses) + `red_flags`.
- Tableau de bord : `DeckSignals` (valeurs) vs config (attendus + benchmarks).
- Analyse par dimension : `dimension_scores` (score, weight, rationale) +
  `red_flags` groupés par `dimension`.
- Red flags : `red_flags`. Incohérences internes = red flags dont le `message`
  commence par « Incohérence interne » (convention actuelle de `analysis.py`).
- Données manquantes : `DeckSignals` à None croisés aux attendus du round (config).
- Contre-analyse : `review` (None pour l'instant).
- Questions fondateurs : questions du référentiel (encodées en config) priorisées.
- Annexes : `DeckAnalysis` (narratif) + métadonnées (version référentiel).

## 3. Fichiers livrés

- `src/output/__init__.py`
- `src/output/memo_data.py` : modèles Pydantic + `build_memo_data`.
- `src/output/render_markdown.py`
- `src/output/render_docx.py`
- `config/memo_config.json`
- `tests/test_memo_data.py`, `tests/test_render_markdown.py`,
  `tests/test_render_docx.py`
- `output/` ajouté à `.gitignore` (jamais commité).

## 4. `config/memo_config.json` (schéma + validation)

```jsonc
{
  "verdict": {
    "seuil_bas": 40,          // < seuil_bas -> PASSER
    "seuil_haut": 65,         // > seuil_haut -> POURSUIVRE
    "majeurs_pour_approfondir": 2
  },
  "grades": [                 // borne basse incluse, décroissant
    {"min": 80, "grade": "A"},
    {"min": 65, "grade": "B"},
    {"min": 50, "grade": "C"},
    {"min": 40, "grade": "D"},
    {"min": 0,  "grade": "E"}
  ],
  "societe_fallback": "Société",
  "attendus_par_round": {
    "seed": [
      {"signal": "revenue_amount", "label": "Revenus / premiers revenus", "criticite": "MAJEUR"},
      {"signal": "churn_rate_pct", "label": "Churn ou rétention", "criticite": "MINEUR"}
      // ... complété depuis référentiel §5.4
    ]
    // ... un tableau par round
  },
  "benchmarks_par_round": {
    "serie-a": {
      "churn_rate_pct": {"top": 2, "norme": 5, "unite": "%/mois"},
      "burn_multiple":  {"top": 1.2, "norme": 2.0}
      // valeur absente ici -> NON_EVALUABLE
    }
  },
  "questions_referentiel": {
    "seed": {
      "traction": "Les utilisateurs reviennent-ils ? Le montrent-ils (cohortes) ?",
      "business_model": "Le pricing a-t-il été confronté à de vrais clients ?"
      // ... texte copié du référentiel, jamais généré
    }
  },
  "version_referentiel": "criteres_analyse_vc.md @ 2026-07"
}
```

Validation au chargement (fonction `load_memo_config`) :
- `seuil_bas < seuil_haut` sinon `ValueError` explicite.
- `majeurs_pour_approfondir >= 1`.
- `grades` triés strictement décroissants sur `min`, dernier `min == 0`.
Analogie : on vérifie la cohérence des bornes comme une clause de covenant avant
de signer, pas après.

## 5. `MemoData` et sous-modèles (Pydantic)

Champs requis = validation Pydantic stricte : un champ requis absent lève une
erreur qui **nomme le champ** (jamais de mémo silencieusement faux).

```
MemoData
  societe: str
  round: str
  ask_amount: str
  date: date
  verdict: Verdict
  forces: list[Reason]          # exactement 3 si >=3 dimensions notées, sinon autant que possible
  faiblesses: list[Reason]      # même règle
  question_decisive: KeyQuestion
  dashboard: list[DashboardRow]
  dimensions: list[DimensionSection]   # ordre = poids décroissant du round
  red_flags: list[RedFlagRow]          # tri sévérité décroissante
  incoherences: list[RedFlagRow]       # sous-ensemble internes
  donnees_manquantes: list[MissingData]
  contre_analyse: ReviewBlock          # porte le mode dégradé
  questions_fondateurs: list[KeyQuestion]   # top 5
  annexes: Annexes

Verdict            -> decision: Literal["PASSER","APPROFONDIR","POURSUIVRE"]
                      justification: str
                      score_global: float
                      nb_critiques: int, nb_majeurs: int
Reason             -> dimension: str, label: str, score: float, preuve: str,
                      slide: int | None   # None tant que traçabilité reportée
DashboardRow       -> metrique: str, valeur: str | None, statut:
                      Literal["TOP_QUARTILE","DANS_LA_NORME","SOUS_LA_BARRE",
                              "ABSENT","NON_EVALUABLE"],
                      benchmark: str | None, slide: int | None
DimensionSection   -> dimension, label, score, weight, grade,
                      regle_appliquee: list[str]  # = rationale
                      red_flags_inline: list[RedFlagRow]
RedFlagRow         -> severity, dimension, label_dimension, message,
                      est_incoherence: bool
MissingData        -> label, criticite, justification: str  # texte référentiel
KeyQuestion        -> question: str, bonne_reponse: str, mauvaise_reponse: str,
                      origine: Literal["red_flag","donnee_manquante","dimension_faible","referentiel"]
ReviewBlock        -> disponible: bool, bandeau: str, contenu: str | None
Annexes            -> methodologie: str, limites: str, extraction_brute: dict
```

## 6. `build_memo_data` : logique par section

### Section 0 — Verdict (déterministe, seuils config)
Précédence d'évaluation :
1. `nb_critiques >= 1` OU `score < seuil_bas` -> **PASSER**.
2. sinon `score > seuil_haut` ET `nb_majeurs < majeurs_pour_approfondir` -> **POURSUIVRE**.
3. sinon -> **APPROFONDIR**.

Convention de borne (documentée et testée) : bornes **larges vers APPROFONDIR**.
`score == 40` et `score == 65` tombent dans APPROFONDIR (car ni `< 40` ni `> 65`).
`justification` cite la règle déclenchée (ex : « score 32 < 40 »).

### Section 1 — Recommandation
- **3 forces** = 3 `dimension_scores` aux meilleurs scores. Départage stable en
  cas d'égalité : score décroissant, puis poids du round décroissant, puis ordre
  alphabétique de `dimension`. `preuve` = meilleure preuve de la dimension
  (valeur de `DeckSignals` liée si dispo, sinon extrait narratif).
- **3 faiblesses** = par priorité : red flags CRITIQUE, puis MAJEUR, puis
  dimensions aux plus faibles scores, jusqu'à 3.
- **Question décisive** (`KeyQuestion`), priorité :
  1. s'il existe un red flag CRITIQUE : question du référentiel associée à sa
     **dimension** (mapping config `questions_referentiel[round][dimension]`) ;
  2. sinon : la donnée manquante de plus haute criticité ;
  3. sinon : question d'analyste du round pour la **dimension la plus faible**.
  Sélection dans `build_memo_data`, reproductible, jamais dans le LLM.

### Section 2 — Tableau de bord
Lignes = `attendus_par_round[round]` (config, sourcé §5.4). Pour chaque ligne :
- valeur = signal correspondant dans `DeckSignals` (formaté) ou None.
- statut :
  - signal None -> `ABSENT`.
  - pas de benchmark en config pour ce signal/round -> `NON_EVALUABLE`.
  - sinon comparaison à `benchmarks_par_round[round][signal]` :
    `TOP_QUARTILE` / `DANS_LA_NORME` / `SOUS_LA_BARRE`.
  On n'invente jamais de seuil absent.

### Section 3 — Analyse par dimension
Ordre = `ROUND_WEIGHTS[round]` décroissant (traction ouvre en série A, équipe en
pre-seed). Pour chaque dimension : score, poids, `grade` (via config), `regle_appliquee`
= `DimensionScore.rationale`, red flags inline (groupés par `dimension`) avec leur
effet lisible tiré du `message`/`severity`.

### Section 4 — Red flags
Tableau trié par sévérité décroissante (CRITIQUE, MAJEUR, MINEUR). Sous-section
« Incohérences internes » = `red_flags` avec `est_incoherence = True` (message
préfixé « Incohérence interne »).

### Section 5 — Données manquantes
`attendus_par_round[round]` dont le signal est None. Chaque entrée porte sa
`justification` = texte du référentiel (config), jamais généré. Criticité selon
§5.4 (donnée critique du stade = MAJEUR, secondaire = MINEUR).

### Section 6 — Contre-analyse (dégradation propre)
Si `review is None` : `ReviewBlock(disponible=False, bandeau=..., contenu=None)`
avec l'encart « Contre-analyse indisponible (erreur API) ». Le mémo se génère
quand même. Si présente plus tard : bandeau exact
« Critique générée par LLM. Non intégrée au score. Non reproductible. » puis contenu.

### Section 7 — Questions fondateurs (top 5)
Priorité : questions liées aux red flags, puis aux données manquantes (sourcées
config/référentiel), complétées par les questions d'analyste du round. Chaque
question : `bonne_reponse` (ce qu'une bonne réponse impliquerait) et
`mauvaise_reponse`.

### Section 8 — Annexes
`methodologie` (les 3 couches, la mécanique de scoring réellement appliquée,
`version_referentiel`), `limites` (dont traçabilité slide reportée, contre-analyse
absente), `extraction_brute` = `DeckAnalysis.model_dump()` mis en forme.

## 7. Traçabilité (politique, reportée)

Invariant cible : une valeur venant du deck porte sa slide source ; sans source,
elle n'apparaît pas. **L'extraction ne capture pas encore la slide.** Donc :
- `slide` est optionnel (`int | None`) sur `Reason` et `DashboardRow`.
- Convention : si un champ source est renseigné, `slide` DOIT l'être. Aujourd'hui
  vacuously vrai (aucune source numérotée). Le test §11 encode l'invariant pour
  qu'il morde automatiquement dès que l'extraction ajoutera les slides.

## 8. Renderers (règles)

- Aucun calcul, tri ou condition métier. Toute donnée dérivée vient de `MemoData`.
- `render_markdown` : titres `#`/`##`, tableaux markdown pour §2 et §4.
- `render_docx` (python-docx) : rendu **brut** (choix ultérieur). Le docx est un
  simple report du texte Markdown en paragraphes, sans styles de titre, sans
  tableaux Word ni encadré. Les lignes de séparation de tableau markdown sont
  sautées. Nom de sortie `memo_{societe}_{YYYY-MM-DD}.docx` dans `output/` (créé si absent).

### Choix librairie Word (à expliquer avant install)
- `python-docx` : construit le document par API (paragraphes, styles, tableaux).
  On garde une seule source de vérité (`MemoData`) et on pose la mise en forme en
  code. Adapté ici car le contenu est dynamique et déjà structuré.
- Alternative `docxtpl` : template Word + variables Jinja. Puissant quand un
  gabarit visuel fixe existe ; mais il faudrait maintenir un .docx template en
  parallèle et la logique de boucles dans le template. Trop rigide pour des
  sections à nombre variable (dimensions, red flags).
- **Choix : `python-docx`**, cohérent avec le journal déjà produit via cette lib.

## 9. Gestion d'erreurs

- `MemoData` incomplet (champ requis absent) : `ValidationError` Pydantic nommant
  le champ. Jamais de mémo silencieusement faux.
- `review=None` : dégradation propre (§6).
- Échec d'écriture (droits, disque) : message clair, code de sortie non nul en CLI.
- Config incohérente : `ValueError` au chargement (§4).

## 10. Tests exigés (pytest)

- Verdict : PASSER par score, PASSER par critique, APPROFONDIR par 2 majeurs,
  POURSUIVRE, plus le cas `score == seuil` (convention large documentée).
- Forces/faiblesses : nominal, < 3 dimensions notées, égalité de scores
  (départage stable).
- Question décisive : les 3 règles de priorité.
- `render_markdown` : golden test (fixture `MemoData` -> markdown attendu, comparé
  caractère par caractère). Le golden test fige une sortie de référence dans un
  fichier ; toute dérive future casse le test volontairement.
- `render_docx` : le fichier se crée, se relit avec python-docx, contient le
  bandeau §6 en texte, aucun tableau Word (rendu brut). Pas de comparaison binaire.
- Invariant traçabilité : aucun `DashboardRow`/`Reason` sans slide quand la valeur
  a une source (vacuement vrai aujourd'hui, actif dès les slides ajoutées).
- Dégradation : `MemoData` sans review -> markdown contient l'encart, aucune trace
  de contenu critique.

## 11. Ordre d'implémentation (tranches verticales)

1. `memo_config.json` + `load_memo_config` (validation) + modèle `Verdict` +
   fonction de verdict + tests verdict.
2. Modèles `MemoData` complets + `build_memo_data` sur en-tête + recommandation +
   tests forces/faiblesses/question.
3. `render_markdown` sections 0-1-2 + golden test.
4. `build_memo_data` + `render_markdown` sections 3-4-5.
5. Section 6 (dégradée) + section 7.
6. `render_docx` complet + tests.
7. Branchement CLI dans `main.py` : ingestion -> extraction -> scoring -> mémo,
   écriture des deux fichiers dans `output/`.

## 12. Points ouverts / dette (hors périmètre étape 3)

1. Mécanique red flags §5.2 (plafonnement) non implémentée en étape 2 (soustraction).
2. Slide source absente de l'extraction (bloque la traçabilité pleine).
3. `DevilsAdvocateReview` (appel Mistral texte) à construire pour la section 6.
4. Benchmarks du référentiel non structurés : dashboard partiel (`NON_EVALUABLE`).
5. Nom de société non extrait proprement (fallback config).
6. `questions_referentiel` (config) : le texte des questions est copié du référentiel
   mais `bonne_reponse`/`mauvaise_reponse` sont vides, à rédiger par un expert VC.
   Le code ne les génère jamais. `attendus_par_round` ne couvre que les signaux
   **typés** de `DeckSignals` ; les attendus narratifs (§5.4 : équipe détaillée,
   problème, use of funds) ne sont pas traçables tant que l'extraction ne les
   structure pas.
