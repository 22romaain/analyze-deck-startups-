"""Agrégat du mémo et logique de préparation (couche déterministe).

Toute la logique de calcul du mémo vit ici : verdict, tri, sélection. Les
renderers (markdown, docx) ne font que mettre en forme ce que ce module produit.
Analogie : ce fichier est l'onglet de calcul du modèle, les renderers sont les
mises en page d'impression.

Tranche 1 : chargement/validation de la config + calcul du verdict.
"""

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from src.analysis import (
    BASELINE_SCORE,
    GLOBAL_CRITICAL_CAP,
    MAJOR_DIMENSION_CAP,
    MAJORS_FOR_CRITICAL,
    MINOR_PENALTY,
    ROUND_WEIGHTS,
)
from src.models import (
    DIMENSION_LABELS,
    AnalysisResult,
    DeckAnalysis,
    DeckSignals,
    DimensionScore,
    RedFlag,
    Severity,
)


# --- Config du mémo (typée et validée au chargement) ---

class GradeBand(BaseModel):
    """Une tranche de grade : score >= min -> grade (ex: >=80 -> 'A')."""
    min: float
    grade: str


class VerdictConfig(BaseModel):
    """Seuils du verdict, jamais codés en dur : ils vivent dans le JSON."""
    seuil_bas: float
    seuil_haut: float
    majeurs_pour_approfondir: int


class AttenduSignal(BaseModel):
    """Un signal typé attendu à un stade donné (§5.4). Son absence est un signal."""
    signal: str  # nom du champ dans DeckSignals
    label: str
    criticite: Severity


class BenchmarkBand(BaseModel):
    """Bornes de comparaison d'une métrique. Le sens (plus bas ou plus haut = mieux)
    se déduit de l'ordre : si top <= norme, plus bas est meilleur (ex: churn) ;
    sinon plus haut est meilleur (ex: runway). On n'invente jamais une borne absente."""
    top: float     # seuil du top quartile
    norme: float   # seuil de la norme acceptable
    unite: str = ""


class MemoConfig(BaseModel):
    """Config complète du mémo. Les invariants métier sont vérifiés ci-dessous."""
    verdict: VerdictConfig
    grades: list[GradeBand]
    societe_fallback: str
    attendus_par_round: dict[str, list[AttenduSignal]]
    benchmarks_par_round: dict[str, dict[str, BenchmarkBand]] = Field(default_factory=dict)
    version_referentiel: str

    @model_validator(mode="after")
    def _check_coherence(self) -> "MemoConfig":
        v = self.verdict
        if not v.seuil_bas < v.seuil_haut:
            raise ValueError(
                f"seuil_bas ({v.seuil_bas}) doit être strictement < seuil_haut ({v.seuil_haut})."
            )
        if v.majeurs_pour_approfondir < 1:
            raise ValueError("majeurs_pour_approfondir doit être >= 1.")
        mins = [g.min for g in self.grades]
        if mins != sorted(mins, reverse=True) or len(set(mins)) != len(mins):
            raise ValueError("Les grades doivent être triés strictement décroissants sur 'min'.")
        if not self.grades or self.grades[-1].min != 0:
            raise ValueError("Le dernier grade doit avoir min == 0 (borne plancher).")
        return self


# Racine du projet : memo_data.py est dans src/output/, donc deux niveaux au-dessus.
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "memo_config.json"


def load_memo_config(path: Path | None = None) -> MemoConfig:
    """Charge et valide la config. Lève ValueError explicite si illisible ou incohérente."""
    config_path = path or DEFAULT_CONFIG_PATH
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Config mémo illisible ({config_path}) : {exc}") from exc
    try:
        return MemoConfig.model_validate_json(raw)
    except ValidationError as exc:
        raise ValueError(f"Config mémo invalide ({config_path}) :\n{exc}") from exc


# --- Verdict (section 0 du mémo) ---

Decision = Literal["PASSER", "APPROFONDIR", "POURSUIVRE"]


class Verdict(BaseModel):
    """Décision d'investissement déterministe, avec sa justification auditable."""
    decision: Decision
    justification: str
    score_global: float
    nb_critiques: int
    nb_majeurs: int


def compute_verdict(
    global_score: float, red_flags: list[RedFlag], config: MemoConfig
) -> Verdict:
    """Calcule le verdict. Précédence : PASSER domine, puis POURSUIVRE, sinon APPROFONDIR.

    Convention de borne : larges vers APPROFONDIR. Un score pile à seuil_bas ou
    seuil_haut tombe dans APPROFONDIR (ni strictement <, ni strictement >).
    """
    v = config.verdict
    nb_critiques = sum(1 for f in red_flags if f.severity == "CRITIQUE")
    nb_majeurs = sum(1 for f in red_flags if f.severity == "MAJEUR")

    if nb_critiques >= 1 or global_score < v.seuil_bas:
        raisons: list[str] = []
        if nb_critiques >= 1:
            raisons.append(f"{nb_critiques} red flag(s) critique(s)")
        if global_score < v.seuil_bas:
            raisons.append(f"score {global_score:.0f} < {v.seuil_bas:.0f}")
        decision: Decision = "PASSER"
        justification = "PASSER : " + " et ".join(raisons) + "."
    elif global_score > v.seuil_haut and nb_majeurs < v.majeurs_pour_approfondir:
        decision = "POURSUIVRE"
        justification = f"POURSUIVRE : score {global_score:.0f} > {v.seuil_haut:.0f} sans red flag critique."
    else:
        decision = "APPROFONDIR"
        raisons = []
        if v.seuil_bas <= global_score <= v.seuil_haut:
            raisons.append(f"score {global_score:.0f} dans [{v.seuil_bas:.0f}, {v.seuil_haut:.0f}]")
        if nb_majeurs >= v.majeurs_pour_approfondir:
            raisons.append(f"{nb_majeurs} red flags majeurs")
        justification = "APPROFONDIR : " + " ; ".join(raisons) + "."

    return Verdict(
        decision=decision,
        justification=justification,
        score_global=global_score,
        nb_critiques=nb_critiques,
        nb_majeurs=nb_majeurs,
    )


# --- Sous-modèles du mémo (structure, aucune logique) ---

# Statuts possibles d'une ligne du tableau de bord (comparaison au benchmark).
DashboardStatut = Literal[
    "TOP_QUARTILE", "DANS_LA_NORME", "SOUS_LA_BARRE", "ABSENT", "NON_EVALUABLE"
]


class Reason(BaseModel):
    """Une force ou une faiblesse : la dimension, son score, et la preuve qui l'appuie.

    slide reste None tant que l'extraction ne capture pas la slide source (§7).
    """
    dimension: str
    label: str
    score: float
    preuve: str
    slide: int | None = None


class DashboardRow(BaseModel):
    """Une ligne du tableau de bord : une métrique attendue confrontée au benchmark."""
    metrique: str
    valeur: str | None
    statut: DashboardStatut
    benchmark: str | None
    slide: int | None = None


class RedFlagRow(BaseModel):
    """Un red flag mis en forme pour le mémo, avec son libellé de dimension lisible."""
    severity: Severity
    dimension: str
    label_dimension: str
    message: str
    est_incoherence: bool


class DoctrineCitation(BaseModel):
    """Un extrait de doctrine VC (tes cours perso) cité en appui d'une dimension.

    On ne garde qu'un extrait court : le mémo pointe vers la source, il ne recopie
    pas le cours entier. distance = proximité à la requête (plus petit = plus proche)."""
    source: str
    section: str
    extrait: str
    distance: float


class DimensionSection(BaseModel):
    """Le bloc d'analyse d'une dimension : score, poids, grade, règles, red flags liés.

    doctrine reste vide par défaut : la citation RAG est optionnelle, la couche mémo
    se construit sans réseau tant qu'on ne l'alimente pas."""
    dimension: str
    label: str
    score: float
    weight: float
    grade: str
    regle_appliquee: list[str]  # = DimensionScore.rationale
    red_flags_inline: list[RedFlagRow]
    doctrine: list[DoctrineCitation] = Field(default_factory=list)


class MissingData(BaseModel):
    """Une donnée attendue au stade mais absente du deck (signal à None)."""
    label: str
    criticite: Severity
    justification: str  # texte du référentiel, jamais généré


class ReviewBlock(BaseModel):
    """La contre-analyse LLM. Porte le mode dégradé tant que la brique n'existe pas."""
    disponible: bool
    bandeau: str
    contenu: str | None


class Annexes(BaseModel):
    """Méthodologie, limites, et extraction brute pour audit."""
    methodologie: str
    limites: str
    extraction_brute: dict


class MemoData(BaseModel):
    """Agrégat complet du mémo. Tous les champs sont requis : un mémo partiel échoue
    à la construction en nommant le champ manquant, plutôt que de sortir faux."""
    societe: str
    round: str
    ask_amount: str
    date: date
    verdict: Verdict
    forces: list[Reason]
    faiblesses: list[Reason]
    dashboard: list[DashboardRow]
    dimensions: list[DimensionSection]
    red_flags: list[RedFlagRow]
    incoherences: list[RedFlagRow]
    donnees_manquantes: list[MissingData]
    contre_analyse: ReviewBlock
    annexes: Annexes


# --- Recommandation (section 1 du mémo) : sélection déterministe ---

def _positive_evidence(rationale: list[str]) -> str:
    """Meilleure preuve positive d'une dimension : la première ligne de bonus.

    Le rationale liste les ajustements (ex: '+15 : Profil technique...'). À défaut
    de bonus, on renvoie la dernière ligne (souvent la base neutre).
    """
    for line in rationale:
        if line.startswith("+"):
            return line
    return rationale[-1] if rationale else ""


def _negative_evidence(rationale: list[str]) -> str:
    """Preuve négative d'une dimension : la première ligne de pénalité ('-...')."""
    for line in rationale:
        if line.startswith("-"):
            return line
    return rationale[-1] if rationale else ""


def select_forces(
    dimension_scores: list["DimensionScore"], count: int = 3
) -> list[Reason]:
    """Les meilleures dimensions du round (poids > 0), triées de façon stable.

    Départage documenté (§6.1) : score décroissant, puis poids du round décroissant,
    puis ordre alphabétique de la dimension. Renvoie au plus `count` forces ; moins
    si peu de dimensions dépassent la base. Une dimension à la base neutre (score
    == BASELINE) n'est pas une force : seules celles avec une vraie preuve positive
    (score > BASELINE) comptent.
    """
    eligibles = [d for d in dimension_scores if d.weight > 0 and d.score > BASELINE_SCORE]
    ranked = sorted(eligibles, key=lambda d: (-d.score, -d.weight, d.dimension))
    return [
        Reason(dimension=d.dimension, label=d.label, score=d.score,
               preuve=_positive_evidence(d.rationale))
        for d in ranked[:count]
    ]


def select_faiblesses(
    dimension_scores: list["DimensionScore"],
    red_flags: list[RedFlag],
    count: int = 3,
) -> list[Reason]:
    """Faiblesses par priorité : red flags CRITIQUE, puis MAJEUR, puis dimensions
    aux plus faibles scores. Une dimension déjà remontée n'est pas répétée.
    """
    by_dim = {d.dimension: d for d in dimension_scores}
    reasons: list[Reason] = []
    seen: set[str] = set()

    # 1-2. Red flags, CRITIQUE avant MAJEUR (tri stable : ordre d'origine préservé).
    severity_rank = {"CRITIQUE": 0, "MAJEUR": 1}
    flags = sorted(
        (f for f in red_flags if f.severity in severity_rank),
        key=lambda f: severity_rank[f.severity],
    )
    for f in flags:
        if f.dimension in seen:
            continue
        d = by_dim.get(f.dimension)
        reasons.append(Reason(
            dimension=f.dimension,
            label=d.label if d else DIMENSION_LABELS.get(f.dimension, f.dimension),
            score=d.score if d else 0.0,
            preuve=f.message,
        ))
        seen.add(f.dimension)
        if len(reasons) >= count:
            return reasons

    # 3. Dimensions du round réellement faibles (score < base). Une dimension à la
    # base neutre (60) n'est pas une faiblesse : on ne remonte que les pénalisées.
    weak = sorted(
        (d for d in dimension_scores if d.weight > 0 and d.score < BASELINE_SCORE),
        key=lambda d: (d.score, -d.weight, d.dimension),
    )
    for d in weak:
        if d.dimension in seen:
            continue
        reasons.append(Reason(dimension=d.dimension, label=d.label, score=d.score,
                              preuve=_negative_evidence(d.rationale)))
        seen.add(d.dimension)
        if len(reasons) >= count:
            break
    return reasons


# --- Tableau de bord (section 2) ---

def _grade_for(score: float, config: MemoConfig) -> str:
    """Traduit un score en grade via les bornes de la config (triées décroissantes)."""
    for band in config.grades:
        if score >= band.min:
            return band.grade
    return config.grades[-1].grade  # filet : le dernier a min == 0


def _format_signal_value(signal: str, signals: DeckSignals) -> str | None:
    """Met en forme un signal pour l'affichage, avec son unité. None si absent."""
    value = getattr(signals, signal)
    if value is None:
        return None
    if signal in ("has_why_now", "has_technical_founder", "product_is_tech"):
        return "Oui" if value else "Non"
    if signal == "revenue_amount":
        currency = signals.revenue_currency or ""
        return f"{value:,.0f} {currency}".strip().replace(",", " ")
    if signal == "churn_rate_pct":
        suffixe = "/mois" if signals.churn_period == "monthly" else "/an"
        return f"{value:.1f}%{suffixe}"
    if signal == "growth_rate_pct":
        return f"{value:.0f}% {signals.growth_period or ''}".strip()
    if signal == "runway_months":
        return f"{value:.0f} mois"
    if signal == "burn_multiple":
        return f"{value:.1f}x"
    if signal.endswith("_pct"):
        return f"{value:.0f}%"
    return str(value)


def _dashboard_status(
    signal: str, signals: DeckSignals, config: MemoConfig, round_name: str
) -> DashboardStatut:
    """Statut d'une métrique : absente, non évaluable (pas de benchmark), ou comparée."""
    value = getattr(signals, signal)
    if value is None:
        return "ABSENT"
    bench = config.benchmarks_par_round.get(round_name, {}).get(signal)
    if bench is None:
        return "NON_EVALUABLE"
    # Le benchmark churn est mensuel : un churn annuel n'est pas comparable ici.
    if signal == "churn_rate_pct" and signals.churn_period != "monthly":
        return "NON_EVALUABLE"
    lower_is_better = bench.top <= bench.norme
    if lower_is_better:
        if value <= bench.top:
            return "TOP_QUARTILE"
        return "DANS_LA_NORME" if value <= bench.norme else "SOUS_LA_BARRE"
    if value >= bench.top:
        return "TOP_QUARTILE"
    return "DANS_LA_NORME" if value >= bench.norme else "SOUS_LA_BARRE"


def build_dashboard(
    signals: DeckSignals, round_name: str, config: MemoConfig
) -> list[DashboardRow]:
    """Une ligne par signal attendu au stade : valeur formatée, statut, benchmark."""
    benchmarks = config.benchmarks_par_round.get(round_name, {})
    rows: list[DashboardRow] = []
    for attendu in config.attendus_par_round.get(round_name, []):
        bench = benchmarks.get(attendu.signal)
        benchmark_str = (
            f"top {bench.top:g} / norme {bench.norme:g}{bench.unite}" if bench else None
        )
        rows.append(DashboardRow(
            metrique=attendu.label,
            valeur=_format_signal_value(attendu.signal, signals),
            statut=_dashboard_status(attendu.signal, signals, config, round_name),
            benchmark=benchmark_str,
            slide=signals.slide_sources.get(attendu.signal),
        ))
    return rows


# --- Pont vers la doctrine RAG (citation des cours en appui d'une dimension) ---

# Longueur max d'un extrait cité : le mémo cite une source, il ne recopie pas un cours.
DOCTRINE_EXTRACT_CHARS = 300

# Requête de doctrine par dimension : plus ciblée que le libellé seul, pour retrouver
# le bon passage de cours. À défaut d'entrée, on retombe sur le libellé de la dimension.
DIMENSION_DOCTRINE_QUERY: dict[str, str] = {
    "equipe": "équipe fondatrice, founder-market fit, profil technique, complémentarité des fondateurs",
    "probleme": "problème douloureux, pain point client, urgence et fréquence du besoin",
    "solution": "solution produit, différenciation, avantage produit défendable",
    "marche": "taille de marché TAM SAM SOM, bottom-up contre top-down, why now",
    "business_model": "business model, unit economics, marge, burn multiple, rétention nette",
    "traction": "traction, croissance, rétention, churn, métriques d'usage",
    "concurrence": "concurrence, moat, barrière à l'entrée, défendabilité durable",
    "go_to_market": "go-to-market, acquisition clients, canaux de distribution, cycle de vente",
    "financials": "financials, runway, burn, projections, hypothèses de croissance",
    "ask": "montant levé, valorisation, dilution, use of funds",
}

# Au-delà de cette distance, un passage est jugé trop peu pertinent pour être cité.
# Durci à 1.0 : les bons matchs du corpus sont à 0.7-0.95 ; au-delà, les citations
# deviennent génériques/hors-sujet. Mieux vaut pas de citation qu'une mauvaise.
# À remonter si tu enrichis le corpus avec des docs plus ciblés par dimension.
DOCTRINE_MAX_DISTANCE = 1.0


def cite_doctrine(
    query: str, k: int = 2, retriever=None, max_distance: float | None = None
) -> list[DoctrineCitation]:
    """Récupère jusqu'à k extraits de doctrine pour une requête, filtrés par pertinence.

    Seuls les passages dont la distance est <= max_distance (défaut DOCTRINE_MAX_DISTANCE)
    sont cités ; les autres sont trop hors-sujet. retriever injectable (défaut = search RAG
    réel) : la couche mémo reste testable hors ligne, sans charger ChromaDB. L'import est
    différé dans la branche par défaut pour ne pas coupler ce module à chromadb.
    """
    ceiling = DOCTRINE_MAX_DISTANCE if max_distance is None else max_distance
    if retriever is None:
        from src.rag.index import search as retriever
    hits = retriever(query, k)
    return [
        DoctrineCitation(
            source=hit.source,
            section=hit.section,
            extrait=hit.text[:DOCTRINE_EXTRACT_CHARS].rstrip(),
            distance=hit.distance,
        )
        for hit in hits
        if hit.distance <= ceiling
    ]


# --- Analyse par dimension, red flags, données manquantes (sections 3-4-5) ---

def _to_red_flag_row(flag: RedFlag) -> RedFlagRow:
    """Convertit un RedFlag brut en ligne de mémo, avec libellé lisible et marquage
    des incohérences internes (convention : message préfixé 'Incohérence interne')."""
    return RedFlagRow(
        severity=flag.severity,
        dimension=flag.dimension,
        label_dimension=DIMENSION_LABELS.get(flag.dimension, flag.dimension),
        message=flag.message,
        est_incoherence=flag.message.startswith("Incohérence interne"),
    )


def build_dimensions(
    analysis: AnalysisResult,
    config: MemoConfig,
    retriever=None,
    doctrine_dimensions: set[str] | None = None,
) -> list[DimensionSection]:
    """Sections par dimension du round, triées par poids décroissant (départage alpha).

    retriever optionnel (défaut None = aucun appel RAG, section construite hors ligne).
    Quand un retriever est fourni : doctrine_dimensions None -> on cite toutes les
    dimensions du round ; un ensemble -> on restreint à ces dimensions. Requête = label."""
    weights = ROUND_WEIGHTS.get(analysis.round, {})
    by_dim = {d.dimension: d for d in analysis.dimension_scores}
    flags_by_dim: dict[str, list[RedFlag]] = {}
    for f in analysis.red_flags:
        flags_by_dim.setdefault(f.dimension, []).append(f)

    ordered = sorted(weights.keys(), key=lambda dim: (-weights[dim], dim))
    sections: list[DimensionSection] = []
    for dim in ordered:
        d = by_dim.get(dim)
        if d is None:
            continue
        want_doctrine = retriever is not None and (
            doctrine_dimensions is None or dim in doctrine_dimensions
        )
        # Requête ciblée par dimension (repli sur le libellé si non mappée).
        query = DIMENSION_DOCTRINE_QUERY.get(dim, d.label)
        cite = cite_doctrine(query, retriever=retriever) if want_doctrine else []
        sections.append(DimensionSection(
            dimension=dim, label=d.label, score=d.score, weight=d.weight,
            grade=_grade_for(d.score, config), regle_appliquee=d.rationale,
            red_flags_inline=[_to_red_flag_row(f) for f in flags_by_dim.get(dim, [])],
            doctrine=cite,
        ))
    return sections


# Ordre d'affichage des red flags : le plus grave en premier.
_SEVERITY_ORDER = {"CRITIQUE": 0, "MAJEUR": 1, "MINEUR": 2}


def build_red_flag_rows(red_flags: list[RedFlag]) -> list[RedFlagRow]:
    """Toutes les alertes en lignes de mémo, triées par sévérité décroissante (tri stable)."""
    rows = [_to_red_flag_row(f) for f in red_flags]
    return sorted(rows, key=lambda r: _SEVERITY_ORDER[r.severity])


def filter_incoherences(rows: list[RedFlagRow]) -> list[RedFlagRow]:
    """Sous-ensemble des lignes qui sont des incohérences internes."""
    return [r for r in rows if r.est_incoherence]


def _missing_justification(criticite: Severity, round_name: str) -> str:
    """Justification d'une donnée manquante, ancrée sur la doctrine (jamais un jugement inventé)."""
    poids = "critique" if criticite == "MAJEUR" else "secondaire"
    return (
        f"Donnée {poids} attendue au stade {round_name} et absente du deck. "
        "L'absence d'une donnée est un signal, pas un neutre (référentiel §1.1)."
    )


def build_missing_data(
    signals: DeckSignals, round_name: str, config: MemoConfig
) -> list[MissingData]:
    """Signaux attendus au stade dont la valeur est absente (None)."""
    missing: list[MissingData] = []
    for attendu in config.attendus_par_round.get(round_name, []):
        if getattr(signals, attendu.signal) is None:
            missing.append(MissingData(
                label=attendu.label,
                criticite=attendu.criticite,
                justification=_missing_justification(attendu.criticite, round_name),
            ))
    return missing


# --- Contre-analyse (section 6) ---

# Bandeaux fixes : le mode dégradé et le mode disponible portent un message exact.
REVIEW_BANDEAU_INDISPONIBLE = "Contre-analyse indisponible (erreur API)."
REVIEW_BANDEAU_DISPONIBLE = "Critique générée par LLM. Non intégrée au score. Non reproductible."


def build_review_block(review_content: str | None = None) -> ReviewBlock:
    """Section 6 : contre-analyse. None -> encart dégradé, le mémo se génère quand même.

    Tant que la brique DevilsAdvocateReview n'existe pas, review_content reste None.
    Le jour où elle produit un texte, on le passe ici et le bandeau bascule.
    """
    if review_content is None:
        return ReviewBlock(disponible=False, bandeau=REVIEW_BANDEAU_INDISPONIBLE, contenu=None)
    return ReviewBlock(disponible=True, bandeau=REVIEW_BANDEAU_DISPONIBLE, contenu=review_content)


# --- Annexes (section 8) ---

def build_annexes(deck: DeckAnalysis, config: MemoConfig, review_disponible: bool) -> Annexes:
    """Méthodologie (3 couches + mécanique de scoring réelle), limites, extraction brute."""
    methodologie = (
        "Trois couches : (1) extraction des slides par LLM vision, "
        "(2) scoring déterministe sans LLM, (3) mise en forme du mémo. "
        f"Score par dimension : base {BASELINE_SCORE:.0f}, plus bonus de preuve. "
        f"Mécanique red flags (§5.2) : MINEUR -{MINOR_PENALTY:.0f} sur la dimension ; "
        f"MAJEUR plafonne la dimension à {MAJOR_DIMENSION_CAP:.0f} ; CRITIQUE (ou "
        f"{MAJORS_FOR_CRITICAL} MAJEURS accumulés) plafonne le score global à "
        f"{GLOBAL_CRITICAL_CAP:.0f}. Score global = moyenne des dimensions pondérée par "
        f"les poids du round. Référentiel : {config.version_referentiel}."
    )
    limites = [
        "Traçabilité slide partielle : le tableau de bord affiche la slide source (au mieux) ; les dimensions narratives ne sont pas encore tracées.",
        "Benchmarks partiels : une métrique sans repère encodé est non évaluable.",
    ]
    if not review_disponible:
        limites.append("Contre-analyse LLM absente (brique non encore construite).")
    return Annexes(
        methodologie=methodologie,
        limites=" ".join(limites),
        extraction_brute=deck.model_dump(),
    )


def build_memo_data(
    deck: DeckAnalysis,
    analysis: AnalysisResult,
    signals: DeckSignals,
    config: MemoConfig,
    review: str | None = None,
    today: date | None = None,
    societe: str | None = None,
    retriever=None,
    doctrine_dimensions: set[str] | None = None,
) -> MemoData:
    """Assemble l'agrégat complet du mémo à partir des trois couches amont.

    Ne calcule rien de nouveau : orchestre les sous-fonctions déjà testées et
    laisse Pydantic vérifier que toutes les sections requises sont présentes.
    `review` = contenu texte de la contre-analyse (None tant que la brique n'existe
    pas). `societe` : nom extrait plus tard ; à défaut, fallback config.
    `retriever` : source de doctrine RAG passée à build_dimensions (None = pas de
    citation, mémo construit hors ligne).
    """
    day = today or date.today()
    red_flag_rows = build_red_flag_rows(analysis.red_flags)
    review_block = build_review_block(review)
    return MemoData(
        societe=societe or deck.company_name or config.societe_fallback,
        round=analysis.round,
        ask_amount=deck.ask_amount,
        date=day,
        verdict=compute_verdict(analysis.global_score, analysis.red_flags, config),
        forces=select_forces(analysis.dimension_scores),
        faiblesses=select_faiblesses(analysis.dimension_scores, analysis.red_flags),
        dashboard=build_dashboard(signals, analysis.round, config),
        dimensions=build_dimensions(analysis, config, retriever, doctrine_dimensions),
        red_flags=red_flag_rows,
        incoherences=filter_incoherences(red_flag_rows),
        donnees_manquantes=build_missing_data(signals, analysis.round, config),
        contre_analyse=review_block,
        annexes=build_annexes(deck, config, review_block.disponible),
    )
