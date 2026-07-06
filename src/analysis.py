"""Module d'analyse : le jugement déterministe (scoring + red flags).

Contrairement à l'extraction, ici AUCUN appel LLM. On lit les signaux factuels
(DeckSignals) et on applique des règles fixes, tirées du référentiel critères.
Avantage : c'est reproductible et auditable. Deux fois le même deck, deux fois
le même score. Analogie : c'est la grille de notation d'un comité d'investissement,
appliquée à la main de la même façon pour chaque dossier.
"""

from src.models import (
    DIMENSION_LABELS,
    AnalysisResult,
    DeckSignals,
    DimensionScore,
    RedFlag,
)

# Poids de chaque dimension selon le round, tirés du référentiel (Partie 2).
# La somme fait 1.0 par round. Les dimensions absentes d'un round ont un poids 0
# (elles comptent pour l'affichage mais pas pour le score global).
ROUND_WEIGHTS: dict[str, dict[str, float]] = {
    "pre-seed": {
        "equipe": 0.40, "probleme": 0.25, "marche": 0.20, "solution": 0.10, "ask": 0.05,
    },
    "seed": {
        "equipe": 0.25, "traction": 0.25, "marche": 0.15, "solution": 0.15,
        "business_model": 0.10, "concurrence": 0.05, "ask": 0.05,
    },
    "serie-a": {
        "traction": 0.30, "business_model": 0.20, "equipe": 0.15, "marche": 0.10,
        "concurrence": 0.10, "go_to_market": 0.10, "ask": 0.05,
    },
    "serie-b": {
        "business_model": 0.30, "traction": 0.20, "equipe": 0.15, "concurrence": 0.15,
        "marche": 0.10, "ask": 0.10,
    },
    "serie-c": {
        "marche": 0.35, "business_model": 0.30, "financials": 0.15, "equipe": 0.15,
        "ask": 0.05,
    },
    "growth": {
        "financials": 0.45, "business_model": 0.25, "concurrence": 0.15,
        "equipe": 0.10, "ask": 0.05,
    },
}

# Pénalité de score par sévérité de red flag (points retirés sur 100).
SEVERITY_PENALTY: dict[str, float] = {
    "CRITIQUE": 35.0,
    "MAJEUR": 18.0,
    "MINEUR": 8.0,
}

# Score de départ de chaque dimension avant ajustements.
# 60 = neutre : ni preuve forte, ni alerte. Les bonus et pénalités font bouger.
BASELINE_SCORE: float = 60.0


def detect_red_flags(signals: DeckSignals, round_name: str) -> list[RedFlag]:
    """Applique les règles du référentiel aux signaux et retourne les alertes.

    Chaque règle vérifie d'abord que la donnée existe (is not None) : une donnée
    absente ne déclenche pas ces règles-ci, elle est traitée à part (pénalité de
    score via l'absence de bonus).
    """
    flags: list[RedFlag] = []

    # --- Équipe ---
    if signals.product_is_tech and signals.has_technical_founder is False:
        flags.append(RedFlag(
            dimension="equipe", severity="CRITIQUE",
            message="Produit au coeur technique mais aucun fondateur au profil technique.",
        ))

    if signals.founder_ownership_pct is not None:
        # Le seuil de dilution acceptable se resserre à mesure que le round avance.
        dilution_thresholds = {"seed": 60.0, "serie-a": 50.0, "serie-b": 40.0, "serie-c": 40.0, "growth": 40.0}
        threshold = dilution_thresholds.get(round_name)
        if threshold is not None and signals.founder_ownership_pct < threshold:
            flags.append(RedFlag(
                dimension="equipe", severity="MAJEUR",
                message=f"Fondateurs à {signals.founder_ownership_pct:.0f}% du capital, sous le seuil attendu ({threshold:.0f}%) pour un {round_name}.",
            ))

    # --- Marché ---
    if signals.tam_methodology == "top-down":
        flags.append(RedFlag(
            dimension="marche", severity="MAJEUR",
            message="TAM calculé uniquement en top-down, sans validation bottom-up.",
        ))
    elif signals.tam_methodology is None and round_name != "pre-seed":
        flags.append(RedFlag(
            dimension="marche", severity="MINEUR",
            message="Aucune méthode de dimensionnement du marché explicite.",
        ))

    if signals.has_why_now is False:
        flags.append(RedFlag(
            dimension="marche", severity="MAJEUR",
            message="Pas de 'why now' articulé (test Sequoia non passé).",
        ))

    # --- Business model / unit economics ---
    if signals.churn_rate_pct is not None:
        if signals.churn_period == "monthly":
            if signals.churn_rate_pct > 5:
                flags.append(RedFlag(
                    dimension="business_model", severity="CRITIQUE",
                    message=f"Churn mensuel de {signals.churn_rate_pct:.1f}%, très élevé pour du B2B.",
                ))
            elif signals.churn_rate_pct > 3:
                flags.append(RedFlag(
                    dimension="business_model", severity="MAJEUR",
                    message=f"Churn mensuel de {signals.churn_rate_pct:.1f}%, au-dessus des standards.",
                ))
        elif signals.churn_period == "annual" and signals.churn_rate_pct > 20:
            flags.append(RedFlag(
                dimension="business_model", severity="MAJEUR",
                message=f"Churn annuel de {signals.churn_rate_pct:.1f}%, élevé.",
            ))

    if signals.nrr_pct is not None:
        if signals.nrr_pct < 90:
            flags.append(RedFlag(
                dimension="business_model", severity="CRITIQUE",
                message=f"NRR à {signals.nrr_pct:.0f}%, la base de revenus se contracte (le seau fuit).",
            ))
        elif signals.nrr_pct < 100:
            flags.append(RedFlag(
                dimension="business_model", severity="MAJEUR",
                message=f"NRR à {signals.nrr_pct:.0f}%, expansion insuffisante pour compenser le churn.",
            ))

    if signals.burn_multiple is not None and signals.burn_multiple > 2:
        flags.append(RedFlag(
            dimension="business_model", severity="MAJEUR",
            message=f"Burn multiple de {signals.burn_multiple:.1f}, capital peu efficace.",
        ))

    # --- Financials ---
    if signals.runway_months is not None:
        if signals.runway_months < 6:
            flags.append(RedFlag(
                dimension="financials", severity="CRITIQUE",
                message=f"Runway de {signals.runway_months:.0f} mois, sous le seuil critique.",
            ))
        elif signals.runway_months < 12:
            flags.append(RedFlag(
                dimension="financials", severity="MAJEUR",
                message=f"Runway de {signals.runway_months:.0f} mois, court pour boucler un tour.",
            ))

    # --- Traction ---
    if signals.customer_concentration_top1_pct is not None and signals.customer_concentration_top1_pct > 30:
        flags.append(RedFlag(
            dimension="traction", severity="MAJEUR",
            message=f"Le premier client pèse {signals.customer_concentration_top1_pct:.0f}% du revenu, forte dépendance.",
        ))

    return flags


def _positive_bonuses(signals: DeckSignals) -> dict[str, list[tuple[float, str]]]:
    """Bonus par dimension quand un signal positif est présent.

    Retourne un dict {dimension: [(points, explication), ...]}.
    Séparé des red flags : ici on récompense les preuves, là on pénalise les alertes.
    """
    bonuses: dict[str, list[tuple[float, str]]] = {}

    def add(dim: str, points: float, why: str) -> None:
        bonuses.setdefault(dim, []).append((points, why))

    if signals.has_technical_founder is True:
        add("equipe", 15, "Profil technique présent dans l'équipe fondatrice.")
    if signals.tam_methodology in ("bottom-up", "both"):
        add("marche", 15, "TAM validé en bottom-up.")
    if signals.has_why_now is True:
        add("marche", 10, "'Why now' explicite.")
    if signals.nrr_pct is not None and signals.nrr_pct >= 110:
        add("business_model", 15, f"NRR à {signals.nrr_pct:.0f}%, expansion nette.")
    if signals.burn_multiple is not None and signals.burn_multiple < 1.5:
        add("business_model", 10, f"Burn multiple de {signals.burn_multiple:.1f}, capital efficace.")
    if signals.churn_rate_pct is not None and (
        (signals.churn_period == "monthly" and signals.churn_rate_pct < 2)
        or (signals.churn_period == "annual" and signals.churn_rate_pct < 10)
    ):
        add("business_model", 10, f"Churn maîtrisé ({signals.churn_rate_pct:.1f}%).")
    if signals.revenue_eur is not None and signals.revenue_eur > 0:
        add("traction", 10, f"Revenu établi ({signals.revenue_eur:,.0f} EUR).")
    if signals.customer_concentration_top1_pct is not None and signals.customer_concentration_top1_pct <= 15:
        add("traction", 5, "Base clients diversifiée.")
    if signals.runway_months is not None and signals.runway_months >= 18:
        add("financials", 10, f"Runway confortable ({signals.runway_months:.0f} mois).")

    return bonuses


def score_dimensions(
    signals: DeckSignals, red_flags: list[RedFlag], round_name: str
) -> list[DimensionScore]:
    """Calcule un score 0-100 par dimension : baseline + bonus - pénalités."""
    weights = ROUND_WEIGHTS.get(round_name, {})
    bonuses = _positive_bonuses(signals)

    scores: list[DimensionScore] = []
    for dim, label in DIMENSION_LABELS.items():
        score = BASELINE_SCORE
        rationale: list[str] = [f"Base neutre : {BASELINE_SCORE:.0f}."]

        for points, why in bonuses.get(dim, []):
            score += points
            rationale.append(f"+{points:.0f} : {why}")

        for flag in red_flags:
            if flag.dimension == dim:
                penalty = SEVERITY_PENALTY[flag.severity]
                score -= penalty
                rationale.append(f"-{penalty:.0f} [{flag.severity}] : {flag.message}")

        # On borne le score dans [0, 100] pour éviter des valeurs absurdes.
        score = max(0.0, min(100.0, score))

        scores.append(DimensionScore(
            dimension=dim, label=label, score=score,
            weight=weights.get(dim, 0.0), rationale=rationale,
        ))

    return scores


def run_analysis(signals: DeckSignals, round_name: str) -> AnalysisResult:
    """Point d'entrée du module : signaux + round -> résultat complet.

    C'est la seule fonction que l'interface a besoin d'appeler.
    """
    red_flags = detect_red_flags(signals, round_name)
    dimension_scores = score_dimensions(signals, red_flags, round_name)

    # Score global = moyenne pondérée des dimensions par les poids du round.
    global_score = sum(ds.score * ds.weight for ds in dimension_scores)

    return AnalysisResult(
        round=round_name,
        global_score=global_score,
        dimension_scores=dimension_scores,
        red_flags=red_flags,
    )
