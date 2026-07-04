"""Modèles Pydantic : structure des données extraites du deck.

Pydantic valide automatiquement que le JSON renvoyé par le LLM respecte
le schéma attendu. Si un champ manque ou a le mauvais type, on le sait
tout de suite au lieu de découvrir un bug plus loin dans le pipeline.
Analogie : c'est la checklist due diligence — on définit ce qu'on veut
avant d'ouvrir la data room.
"""

from pydantic import BaseModel, Field


class DeckAnalysis(BaseModel):
    """Analyse structurée d'un pitch deck selon les dimensions VC classiques."""

    equipe: str = Field(
        description="Équipe fondatrice et founder-market fit : qui sont-ils, parcours, complémentarité"
    )
    probleme: str = Field(
        description="Problème adressé : pour qui, quelle douleur, quelle intensité"
    )
    solution: str = Field(
        description="Solution proposée : quoi, comment ça marche, quel différenciant"
    )
    marche: str = Field(
        description="Taille de marché : TAM SAM SOM, dynamique, why now"
    )
    business_model: str = Field(
        description="Modèle économique et unit economics : comment l'entreprise gagne de l'argent"
    )
    traction: str = Field(
        description="Traction et métriques clés : revenus, utilisateurs, croissance, preuves de validation"
    )
    concurrence: str = Field(
        description="Paysage concurrentiel et moat : qui sont les concurrents, quel avantage défendable"
    )
    go_to_market: str = Field(
        description="Stratégie d'acquisition : canaux, coût d'acquisition, stratégie de distribution"
    )
    financials: str = Field(
        description="Projections financières : hypothèses, runway, chemin vers la rentabilité"
    )
    ask: str = Field(
        description="La demande : montant levé, valorisation, use of funds, prochaines étapes"
    )


# Labels lisibles pour l'interface — évite de coder en dur les noms dans Streamlit
DIMENSION_LABELS: dict[str, str] = {
    "equipe": "Équipe",
    "probleme": "Problème",
    "solution": "Solution",
    "marche": "Marché",
    "business_model": "Business Model",
    "traction": "Traction",
    "concurrence": "Concurrence",
    "go_to_market": "Go-to-Market",
    "financials": "Financials",
    "ask": "Ask",
}
