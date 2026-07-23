"""Synthèse qualitative du deck : les constats tagués groupés en pros / cons.

Remplace le score chiffré. À partir de la liste unique de constats (Finding)
produite par collecter_findings, ce module range chaque constat par polarité et
en tire une recommandation pilotée par les catégories, jamais par un nombre.
Un rédhibitoire suffit à recommander de passer ; l'expérience de l'analyste fait
le reste en lisant le détail. La logique reste déterministe et auditable.
"""

from typing import Literal

from pydantic import BaseModel

from src.models import FINDING_CATEGORIES, Finding

# Décision de haut niveau, dérivée des catégories de constats (pas d'un score).
# Choix assumé : l'outil ne prononce jamais un "non" définitif. Même un rédhibitoire
# renvoie à APPROFONDIR (à instruire et justifier), jamais à un rejet automatique.
# C'est l'analyste qui tranche après approfondissement, pas la machine.
RecommandationDecision = Literal["APPROFONDIR", "POURSUIVRE"]


class Recommandation(BaseModel):
    """La reco qualitative et sa justification auditable (quels constats la portent)."""
    decision: RecommandationDecision
    justification: str
    nb_redhibitoires: int
    nb_faiblesses: int
    nb_atouts: int


class Synthese(BaseModel):
    """Les constats groupés par polarité, prêts à afficher en pros / cons.

    atouts = polarité positive, points_negatifs = polarité négative (rédhibitoire,
    faiblesse, vigilance), a_creuser = polarité neutre. Chaque liste est triée par
    ordre de catégorie (le plus fort/grave d'abord) puis par dimension.
    """
    atouts: list[Finding]
    points_negatifs: list[Finding]
    a_creuser: list[Finding]
    recommandation: Recommandation


def _polarite(finding: Finding) -> str:
    """Polarité d'un constat (positif/negatif/neutre), lue dans la table des catégories."""
    return FINDING_CATEGORIES[finding.categorie]["polarite"]


def _trie_par_gravite(findings: list[Finding]) -> list[Finding]:
    """Trie par ordre de catégorie (rédhibitoire avant vigilance...) puis par dimension."""
    return sorted(findings, key=lambda f: (FINDING_CATEGORIES[f.categorie]["ordre"], f.dimension))


def recommander(findings: list[Finding]) -> Recommandation:
    """Dérive la reco des seules catégories : un rédhibitoire = PASSER ; sinon une
    faiblesse = APPROFONDIR ; sinon POURSUIVRE. Aucune moyenne, aucun score."""
    nb_red = sum(1 for f in findings if f.categorie == "redhibitoire")
    nb_faibles = sum(1 for f in findings if f.categorie == "faiblesse")
    nb_atouts = sum(1 for f in findings if _polarite(f) == "positif")
    if nb_red >= 1:
        decision: RecommandationDecision = "APPROFONDIR"
        justification = (f"APPROFONDIR : {nb_red} constat(s) rédhibitoire(s) à instruire "
                         "et à justifier avant toute décision.")
    elif nb_faibles >= 1:
        decision = "APPROFONDIR"
        justification = f"APPROFONDIR : {nb_faibles} faiblesse(s) à lever, aucun rédhibitoire."
    else:
        decision = "POURSUIVRE"
        justification = f"POURSUIVRE : aucun point bloquant, {nb_atouts} atout(s) relevé(s)."
    return Recommandation(
        decision=decision, justification=justification,
        nb_redhibitoires=nb_red, nb_faiblesses=nb_faibles, nb_atouts=nb_atouts,
    )


def build_synthese(findings: list[Finding]) -> Synthese:
    """Groupe les constats par polarité (triés par gravité) et calcule la recommandation."""
    return Synthese(
        atouts=_trie_par_gravite([f for f in findings if _polarite(f) == "positif"]),
        points_negatifs=_trie_par_gravite([f for f in findings if _polarite(f) == "negatif"]),
        a_creuser=_trie_par_gravite([f for f in findings if _polarite(f) == "neutre"]),
        recommandation=recommander(findings),
    )
