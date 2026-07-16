"""Moteur de dilution (phase 4, cap table). Code pur et déterministe : aucune IA.

Donne, pour un tour de financement, comment évoluent les parts au capital.
Mécanique de base : post-money = pre-money + montant levé ; le nouvel investisseur
prend montant / post-money ; les détenteurs existants sont dilués au prorata
(facteur pre-money / post-money). L'option pool viendra dans un second temps.
"""

from pydantic import BaseModel, Field


class RoundInput(BaseModel):
    """Termes d'un tour. pre_money et amount dans la même devise (valeurs absolues)."""
    pre_money: float = Field(gt=0, description="Valorisation pre-money, avant l'argent levé.")
    amount: float = Field(gt=0, description="Montant levé au tour.")
    founder_pct_pre: float = Field(ge=0, le=100, description="Part fondateurs avant le tour, en %.")
    new_option_pool_pct: float = Field(
        default=0.0, ge=0, le=100,
        description="Option pool créé au tour, en % du post-money, prélevé pre-money (0 si aucun).",
    )


class DilutionResult(BaseModel):
    """Photo du capital après le tour, en pourcentages."""
    post_money: float
    new_investor_pct: float
    option_pool_pct: float
    founder_pct_post: float
    founder_dilution_points: float  # points de % perdus par les fondateurs


def compute_dilution(round_input: RoundInput) -> DilutionResult:
    """Évolution des parts après un tour, option pool créé pre-money incluse.

    Les anciens actionnaires retiennent (1 − part_investisseur − part_pool) : le pool
    créé pre-money est prélevé sur eux seuls, l'investisseur n'en porte rien. Sans pool,
    la rétention retombe sur pre_money / post_money.
    """
    post_money = round_input.pre_money + round_input.amount
    new_investor_pct = round_input.amount / post_money * 100
    pool_pct = round_input.new_option_pool_pct
    existing_retention = 1 - new_investor_pct / 100 - pool_pct / 100
    if existing_retention <= 0:
        raise ValueError("Investisseur + option pool dépassent 100% : termes du tour incohérents.")
    founder_post = round_input.founder_pct_pre * existing_retention
    return DilutionResult(
        post_money=post_money,
        new_investor_pct=new_investor_pct,
        option_pool_pct=pool_pct,
        founder_pct_post=founder_post,
        founder_dilution_points=round_input.founder_pct_pre - founder_post,
    )
