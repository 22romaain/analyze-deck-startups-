"""Agrégat du mémo et logique de préparation (couche déterministe).

Toute la logique de calcul du mémo vit ici : verdict, tri, sélection. Les
renderers (markdown, docx) ne font que mettre en forme ce que ce module produit.
Analogie : ce fichier est l'onglet de calcul du modèle, les renderers sont les
mises en page d'impression.

Tranche 1 : chargement/validation de la config + calcul du verdict.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError, model_validator

from src.models import RedFlag


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


class MemoConfig(BaseModel):
    """Config complète du mémo. Les invariants métier sont vérifiés ci-dessous."""
    verdict: VerdictConfig
    grades: list[GradeBand]
    societe_fallback: str
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
