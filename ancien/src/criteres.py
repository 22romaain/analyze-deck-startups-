"""Chargement et validation des critères éditables (config/criteres.yaml).

Ce module lit le fichier de critères que l'utilisateur édite à la main et le
transforme en objets Pydantic validés. Rôle : attraper une faute de frappe
(dimension inconnue, opérateur invalide, condition mal formée) AU CHARGEMENT,
avec un message clair, plutôt que de la découvrir en plein milieu de l'analyse.
Le YAML est la doctrine éditable ; ce module en est le portier.
"""

import operator as _operator
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, model_validator

from src.models import DIMENSION_LABELS, DeckSignals, Finding, FindingCategory

# Traduction des opérateurs texte du YAML en vraies fonctions de comparaison.
_OPERATEURS = {
    ">": _operator.gt, ">=": _operator.ge, "<": _operator.lt,
    "<=": _operator.le, "==": _operator.eq, "!=": _operator.ne,
}

# Emplacement par défaut du fichier de critères, calculé depuis ce module pour
# marcher quel que soit le dossier d'où on lance l'app.
CRITERES_PATH = Path(__file__).resolve().parent.parent / "config" / "criteres.yaml"

# Rounds valides (mêmes clés que ROUND_OPTIONS dans models.py). Un round hors de
# cette liste dans le YAML est une faute de frappe, pas un round exotique.
ROUNDS_VALIDES: set[str] = {"pre-seed", "seed", "serie-a", "serie-b", "serie-c", "growth"}

Operateur = Literal[">", ">=", "<", "<=", "==", "!="]
EtatPresence = Literal["vrai", "faux", "present", "absent"]


class Condition(BaseModel):
    """Le bloc 'quand' d'un critère : soit une présence/booléen (est), soit une
    comparaison chiffrée (operateur + valeur). Exactement une des deux formes."""

    signal: str
    est: EtatPresence | None = None
    operateur: Operateur | None = None
    valeur: float | None = None

    @model_validator(mode="after")
    def _exactement_une_forme(self) -> "Condition":
        forme_presence = self.est is not None
        forme_chiffre = self.operateur is not None or self.valeur is not None
        if forme_presence and forme_chiffre:
            raise ValueError(f"signal '{self.signal}' : mélange 'est' et 'operateur/valeur', choisis une seule forme.")
        if not forme_presence and not forme_chiffre:
            raise ValueError(f"signal '{self.signal}' : condition vide, précise 'est' OU 'operateur'+'valeur'.")
        if forme_chiffre and (self.operateur is None or self.valeur is None):
            raise ValueError(f"signal '{self.signal}' : comparaison chiffrée incomplète, il faut 'operateur' ET 'valeur'.")
        return self


class Critere(BaseModel):
    """Un critère éditable : une condition qui, si vraie, produit un constat tagué."""

    id: str
    dimension: str
    categorie: FindingCategory
    rounds: list[str]
    quand: Condition
    message: str

    @model_validator(mode="after")
    def _valider_dimension_et_rounds(self) -> "Critere":
        if self.dimension not in DIMENSION_LABELS:
            raise ValueError(f"critère '{self.id}' : dimension inconnue '{self.dimension}'.")
        # 'tous' est un raccourci : on le remplace par la liste réelle des rounds,
        # pour que le reste du code ne manipule que des rounds concrets.
        if "tous" in self.rounds:
            self.rounds = sorted(ROUNDS_VALIDES)
        for r in self.rounds:
            if r not in ROUNDS_VALIDES:
                raise ValueError(f"critère '{self.id}' : round inconnu '{r}'.")
        return self


def charger_criteres(path: Path = CRITERES_PATH) -> list["Critere"]:
    """Lit le YAML des critères et retourne la liste validée.

    Lève une erreur claire si le fichier est absent, illisible, ou si sa forme
    d'ensemble est mauvaise (clé 'criteres' manquante ou pas une liste). Chaque
    critère est ensuite validé par le modèle Critere, qui râle sur ses propres
    fautes. On préfère échouer ici, au chargement, qu'en pleine analyse.
    """
    if not path.exists():
        raise FileNotFoundError(f"Fichier de critères introuvable : {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    criteres_bruts = data.get("criteres", [])
    if not isinstance(criteres_bruts, list):
        raise ValueError("Le fichier de critères doit contenir une liste sous la clé 'criteres'.")
    return [Critere.model_validate(c) for c in criteres_bruts]


def _condition_remplie(cond: Condition, signals: DeckSignals) -> bool:
    """Évalue une condition contre les signaux.

    Doctrine 1.1 : une donnée absente (None) ne remplit jamais une comparaison
    chiffrée, on ne compare pas l'inconnu. 'faux' (nié) et 'absent' (inconnu)
    restent bien distincts.
    """
    valeur = getattr(signals, cond.signal, None)
    if cond.est is not None:
        if cond.est == "vrai":
            return valeur is True
        if cond.est == "faux":
            return valeur is False
        if cond.est == "present":
            return valeur is not None
        return valeur is None  # "absent"
    if valeur is None:  # forme chiffrée sur une donnée absente
        return False
    return _OPERATEURS[cond.operateur](valeur, cond.valeur)


def _formater_valeur(valeur: object) -> str:
    """Rend une valeur lisible dans un message : 3.0 -> '3', 12.5 -> '12.5'."""
    if isinstance(valeur, float) and valeur.is_integer():
        return str(int(valeur))
    return str(valeur)


def evaluer_criteres(
    signals: DeckSignals, round_name: str, criteres: list[Critere] | None = None
) -> list[Finding]:
    """Confronte les critères du round aux signaux et retourne les constats déclenchés."""
    if criteres is None:
        criteres = charger_criteres()
    findings: list[Finding] = []
    for critere in criteres:
        if round_name not in critere.rounds:
            continue
        if not _condition_remplie(critere.quand, signals):
            continue
        valeur = getattr(signals, critere.quand.signal, None)
        message = critere.message.replace("{valeur}", _formater_valeur(valeur))
        findings.append(Finding(
            dimension=critere.dimension, categorie=critere.categorie,
            message=message, source=f"critere:{critere.id}",
        ))
    return findings
