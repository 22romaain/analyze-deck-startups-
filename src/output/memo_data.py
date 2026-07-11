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

from pydantic import BaseModel, ValidationError, model_validator

from src.analysis import ROUND_WEIGHTS
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


class QuestionRef(BaseModel):
    """Une question d'analyste copiée du référentiel. Les réponses type sont à
    rédiger par un expert : le code ne les génère jamais (vides par défaut)."""
    question: str
    bonne_reponse: str = ""
    mauvaise_reponse: str = ""


class MemoConfig(BaseModel):
    """Config complète du mémo. Les invariants métier sont vérifiés ci-dessous."""
    verdict: VerdictConfig
    grades: list[GradeBand]
    societe_fallback: str
    attendus_par_round: dict[str, list[AttenduSignal]]
    questions_referentiel: dict[str, dict[str, QuestionRef]]
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

# D'où vient une question posée au comité (traçabilité de la sélection).
QuestionOrigine = Literal["red_flag", "donnee_manquante", "dimension_faible", "referentiel"]


class Reason(BaseModel):
    """Une force ou une faiblesse : la dimension, son score, et la preuve qui l'appuie.

    slide reste None tant que l'extraction ne capture pas la slide source (§7).
    """
    dimension: str
    label: str
    score: float
    preuve: str
    slide: int | None = None


class KeyQuestion(BaseModel):
    """Une question à poser aux fondateurs, avec ce qu'une bonne/mauvaise réponse révèle.

    bonne_reponse / mauvaise_reponse peuvent être vides tant qu'un expert ne les a
    pas rédigées : le code ne les invente jamais (elles viennent de la config).
    """
    question: str
    bonne_reponse: str
    mauvaise_reponse: str
    origine: QuestionOrigine


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


class DimensionSection(BaseModel):
    """Le bloc d'analyse d'une dimension : score, poids, grade, règles, red flags liés."""
    dimension: str
    label: str
    score: float
    weight: float
    grade: str
    regle_appliquee: list[str]  # = DimensionScore.rationale
    red_flags_inline: list[RedFlagRow]


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
    question_decisive: KeyQuestion
    dashboard: list[DashboardRow]
    dimensions: list[DimensionSection]
    red_flags: list[RedFlagRow]
    incoherences: list[RedFlagRow]
    donnees_manquantes: list[MissingData]
    contre_analyse: ReviewBlock
    questions_fondateurs: list[KeyQuestion]
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
    si le round pèse moins de `count` dimensions.
    """
    eligibles = [d for d in dimension_scores if d.weight > 0]
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

    # 3. Dimensions du round aux plus faibles scores (départage stable inverse).
    weak = sorted(
        (d for d in dimension_scores if d.weight > 0),
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


def _round_weight(round_name: str, dimension: str) -> float:
    """Poids d'une dimension dans le round (0 si non pondérée). Sert au départage."""
    return ROUND_WEIGHTS.get(round_name, {}).get(dimension, 0.0)


def select_question_decisive(
    analysis: AnalysisResult, signals: DeckSignals, config: MemoConfig
) -> KeyQuestion:
    """La seule question à trancher, sélectionnée par règles (jamais par le LLM).

    Priorité : red flag critique -> donnée manquante la plus critique -> dimension
    la plus faible. Reproductible : même entrée, même question.
    """
    round_name = analysis.round
    questions = config.questions_referentiel.get(round_name, {})

    # Règle 1 : un red flag CRITIQUE dont la dimension porte une question en config.
    critiques = sorted(
        (f for f in analysis.red_flags if f.severity == "CRITIQUE"),
        key=lambda f: (-_round_weight(round_name, f.dimension), f.dimension),
    )
    for f in critiques:
        q = questions.get(f.dimension)
        if q is not None:
            return KeyQuestion(question=q.question, bonne_reponse=q.bonne_reponse,
                               mauvaise_reponse=q.mauvaise_reponse, origine="red_flag")

    # Règle 2 : la donnée attendue absente de plus haute criticité.
    rank = {"MAJEUR": 2, "MINEUR": 1}
    attendus = config.attendus_par_round.get(round_name, [])
    missing = [a for a in attendus if getattr(signals, a.signal) is None]
    if missing:
        missing.sort(key=lambda a: -rank.get(a.criticite, 0))  # stable : ordre config à égalité
        a = missing[0]
        return KeyQuestion(
            question=f"Donnée attendue absente du deck : {a.label}. Pourquoi, et quelle est la valeur réelle ?",
            bonne_reponse="", mauvaise_reponse="", origine="donnee_manquante",
        )

    # Règle 3 : question d'analyste pour la dimension du round la plus faible.
    weighted = [d for d in analysis.dimension_scores if d.weight > 0]
    if weighted:
        weakest = sorted(weighted, key=lambda d: (d.score, -d.weight, d.dimension))[0]
        q = questions.get(weakest.dimension)
        if q is not None:
            return KeyQuestion(question=q.question, bonne_reponse=q.bonne_reponse,
                               mauvaise_reponse=q.mauvaise_reponse, origine="dimension_faible")

    # Repli : une question du round si disponible, sinon question générique.
    if questions:
        first = sorted(questions.items())[0][1]
        return KeyQuestion(question=first.question, bonne_reponse=first.bonne_reponse,
                           mauvaise_reponse=first.mauvaise_reponse, origine="referentiel")
    return KeyQuestion(
        question="Quelle est la principale incertitude non levée par ce deck ?",
        bonne_reponse="", mauvaise_reponse="", origine="referentiel",
    )


def build_memo_data(
    deck: DeckAnalysis,
    analysis: AnalysisResult,
    signals: DeckSignals,
    config: MemoConfig,
    review: object | None = None,
    today: date | None = None,
) -> MemoData:
    """Assemblera l'agrégat complet du mémo (en construction).

    Tranche 2 : les sous-fonctions (verdict, forces, faiblesses, question décisive)
    existent et sont testées isolément. L'assemblage complet attend que les sections
    tableau de bord, dimensions, red flags, données manquantes et annexes soient
    implémentées (tranches 4 à 6). On refuse de produire un MemoData partiel plutôt
    que de sortir un mémo silencieusement faux.
    """
    raise NotImplementedError(
        "build_memo_data : agrégat complet non encore assemblé (voir tranches 4 à 6)."
    )
