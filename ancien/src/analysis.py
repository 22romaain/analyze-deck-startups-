"""Module d'analyse : le jugement déterministe (scoring + red flags).

Contrairement à l'extraction, ici AUCUN appel LLM. On lit les signaux factuels
(DeckSignals) et on applique des règles fixes, tirées du référentiel critères.
Avantage : c'est reproductible et auditable. Deux fois le même deck, deux fois
le même score. Analogie : c'est la grille de notation d'un comité d'investissement,
appliquée à la main de la même façon pour chaque dossier.
"""

from src.captable import LiquidationPref, RoundInput, compute_dilution, compute_waterfall
from src.criteres import evaluer_criteres
from src.models import (
    AnalysisResult,
    DeckSignals,
    Finding,
    RedFlag,
    parse_amount,
    revenue_in_eur,
)

# Importance de chaque dimension selon le round, tirée du référentiel (Partie 2).
# Ne sert plus à noter (le score a été retiré) : sert à ORDONNER l'affichage des
# dimensions dans le mémo, les plus décisives du stade en tête. Une dimension absente
# d'un round a une importance 0 (elle s'affiche après celles qui comptent au stade).
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

# Rounds où une cap table est exigible : son absence devient un signal (§4.3).
SERIES_A_PLUS_ROUNDS = {"serie-a", "serie-b", "serie-c", "growth"}

# Détention fondateurs minimale attendue par round (référentiel §4.3, ordre de grandeur).
# Le seuil se resserre à mesure que le tour avance. Pas de seuil en pre-seed.
FOUNDER_OWNERSHIP_MIN_BY_ROUND = {
    "seed": 75.0, "serie-a": 50.0, "serie-b": 40.0, "serie-c": 40.0, "growth": 40.0,
}


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

    # Détention fondateurs et cap table (référentiel §4.3).
    if signals.founder_ownership_pct is not None:
        threshold = FOUNDER_OWNERSHIP_MIN_BY_ROUND.get(round_name)
        if threshold is not None and signals.founder_ownership_pct < threshold:
            flags.append(RedFlag(
                dimension="equipe", severity="MAJEUR",
                message=f"Fondateurs à {signals.founder_ownership_pct:.0f}% du capital, sous le seuil attendu ({threshold:.0f}%) pour un {round_name}.",
            ))
    elif round_name in SERIES_A_PLUS_ROUNDS:
        # Cap table exigible mais absente : c'est un signal, pas un neutre (§1.1 et §4.3).
        flags.append(RedFlag(
            dimension="equipe", severity="MAJEUR",
            message=f"Cap table non fournie ou incomplète pour un {round_name} (détention fondateurs absente du deck).",
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


# Plafonds de revenu au-delà desquels un revenu devient suspect pour le round.
# On lève rarement un pre-seed/seed avec déjà beaucoup de revenu : ça interroge.
# Rien pour les rounds tardifs (un revenu élevé y est normal).
REVENUE_CEILING_BY_ROUND_EUR: dict[str, float] = {
    "pre-seed": 2_000_000,
    "seed": 10_000_000,
}


def _to_monthly_pct(rate_pct: float, period: str, kind: str) -> float:
    """Ramène un taux (churn ou croissance) à sa version mensuelle, en composé.

    kind='churn' : un churn annuel c se traduit par un churn mensuel équivalent
    tel que (1 - m)^12 = (1 - c). kind='growth' : (1 + m)^12 = (1 + a).
    Le composé, pas la division par 12 : 5% par mois ne fait pas 60% par an.
    """
    r = rate_pct / 100
    if period in ("annual", "YoY"):
        if kind == "churn":
            r = 1 - (1 - r) ** (1 / 12)
        else:  # growth
            r = (1 + r) ** (1 / 12) - 1
    return r * 100


def _annualize_churn_pct(churn_pct: float, period: str) -> float:
    """Churn annualisé en composé : 5% mensuel -> ~46% annuel, pas 60%."""
    if period == "annual":
        return churn_pct
    m = churn_pct / 100
    return (1 - (1 - m) ** 12) * 100


def detect_incoherences(signals: DeckSignals, round_name: str) -> list[RedFlag]:
    """Croise les chiffres entre eux pour repérer les contradictions internes.

    Différent des red flags classiques : ici un chiffre n'est pas jugé face à un
    seuil, mais face à un AUTRE chiffre du deck. C'est ce qui attrape le chiffre
    inventé mais crédible pris isolément. Message préfixé 'Incohérence interne'.
    """
    flags: list[RedFlag] = []

    # 1. churn ↔ NRR : perdre beaucoup au churn tout en gardant un NRR >= 100%
    #    suppose une expansion massive qui devrait être démontrée.
    if signals.churn_rate_pct is not None and signals.churn_period is not None and signals.nrr_pct is not None:
        annual_churn = _annualize_churn_pct(signals.churn_rate_pct, signals.churn_period)
        if annual_churn > 15 and signals.nrr_pct >= 100:
            flags.append(RedFlag(
                dimension="business_model", severity="MAJEUR",
                message=f"Incohérence interne : churn annualisé ~{annual_churn:.0f}% mais NRR de {signals.nrr_pct:.0f}%. Retenir >100% du revenu en perdant autant au churn suppose une expansion non démontrée.",
            ))

    # 2. churn ↔ croissance : ramenés au mois, si le churn dépasse la croissance,
    #    la base se contracte malgré la croissance affichée.
    if (signals.churn_rate_pct is not None and signals.churn_period is not None
            and signals.growth_rate_pct is not None and signals.growth_period is not None):
        monthly_churn = _to_monthly_pct(signals.churn_rate_pct, signals.churn_period, "churn")
        monthly_growth = _to_monthly_pct(signals.growth_rate_pct, signals.growth_period, "growth")
        if monthly_churn > monthly_growth:
            flags.append(RedFlag(
                dimension="traction", severity="MAJEUR",
                message=f"Incohérence interne : churn (~{monthly_churn:.1f}%/mois) supérieur à la croissance (~{monthly_growth:.1f}%/mois). La base se contracte malgré une croissance affichée.",
            ))

    # 3. revenu ↔ round : un revenu très élevé sur un round précoce interroge.
    rev_eur = revenue_in_eur(signals.revenue_amount, signals.revenue_currency)
    ceiling = REVENUE_CEILING_BY_ROUND_EUR.get(round_name)
    if rev_eur is not None and ceiling is not None and rev_eur > ceiling:
        flags.append(RedFlag(
            dimension="traction", severity="MINEUR",
            message=f"Incohérence interne : revenu de ~{rev_eur/1e6:.1f}M EUR anormalement élevé pour un {round_name} (plafond attendu ~{ceiling/1e6:.0f}M).",
        ))

    return flags


def detect_dilution_flag(
    signals: DeckSignals, round_name: str, ask_amount: str | None
) -> RedFlag | None:
    """Alerte si, après ce tour, la détention fondateurs passe sous le seuil du stade (§4.3).

    Exige valo pre-money, part fondateurs, et un montant levé parsable. Hypothèse : valo
    et montant dans la même devise (cas usuel d'un deck) ; seul leur ratio compte pour la
    dilution, la devise s'annule. Termes incohérents (>100% prélevé) : on renonce.
    """
    threshold = FOUNDER_OWNERSHIP_MIN_BY_ROUND.get(round_name)
    if threshold is None or signals.pre_money_valuation is None or signals.founder_ownership_pct is None:
        return None
    amount = parse_amount(ask_amount) if ask_amount else None
    if amount is None:
        return None
    try:
        result = compute_dilution(RoundInput(
            pre_money=signals.pre_money_valuation,
            amount=amount,
            founder_pct_pre=signals.founder_ownership_pct,
            new_option_pool_pct=signals.new_option_pool_pct or 0.0,
        ))
    except ValueError:
        return None
    if result.founder_pct_post >= threshold:
        return None
    return RedFlag(
        dimension="equipe", severity="MAJEUR",
        message=(f"Après ce tour, fondateurs à {result.founder_pct_post:.0f}% "
                 f"(dilution de {result.founder_dilution_points:.0f} pts), "
                 f"sous le seuil attendu ({threshold:.0f}%) pour un {round_name}."),
    )


# Sous ce plancher de part de sortie, les fondateurs "ne touchent presque rien" (§4.3).
WATERFALL_FOUNDERS_FLOOR_PCT = 10.0


def detect_waterfall_flag(
    prefs: list[LiquidationPref], founder_pct: float, post_money: float
) -> RedFlag | None:
    """Alerte CRITIQUE si, à la sortie de référence, le stack de préférences écrase les
    fondateurs (§4.3).

    Scénario médian retenu : vente au post-money (sortie honorable). Si même là les
    ordinaires passent sous le plancher, les liquidation preferences sont le problème.
    """
    if not prefs or post_money <= 0 or founder_pct <= 0:
        return None
    result = compute_waterfall(post_money, prefs, founder_pct)
    if result.founders_pct_of_exit >= WATERFALL_FOUNDERS_FLOOR_PCT:
        return None
    return RedFlag(
        dimension="equipe", severity="CRITIQUE",
        message=(f"Waterfall : à une sortie au post-money (~{post_money / 1e6:.0f}M), les "
                 f"fondateurs ne touchent que {result.founders_pct_of_exit:.0f}% "
                 f"(~{result.founders_payout / 1e6:.1f}M), écrasés par les liquidation preferences."),
    )


def collecter_red_flags(
    signals: DeckSignals, round_name: str, ask_amount: str | None = None
) -> list[RedFlag]:
    """Assemble tous les red flags déterministes : seuils, incohérences, dilution, waterfall.

    Factorisé pour être réutilisé par le score (run_analysis) ET par la couche
    qualitative (collecter_findings), sans dupliquer la logique cap table.
    """
    # Red flags classiques (chiffre vs seuil) + incohérences internes (chiffre vs chiffre).
    red_flags = detect_red_flags(signals, round_name)
    red_flags += detect_incoherences(signals, round_name)
    dilution_flag = detect_dilution_flag(signals, round_name, ask_amount)
    if dilution_flag is not None:
        red_flags.append(dilution_flag)

    # Waterfall : n'a de sens que si des préférences sont connues (rare hors term sheet).
    # Sortie de référence = post-money. La part fondateurs à l'exit = leur détention APRÈS
    # ce tour (post-dilution), pas leur détention actuelle : le waterfall porte sur un futur.
    amount = parse_amount(ask_amount) if ask_amount else None
    if signals.liquidation_prefs and signals.pre_money_valuation is not None \
            and signals.founder_ownership_pct is not None and amount is not None:
        try:
            diluted = compute_dilution(RoundInput(
                pre_money=signals.pre_money_valuation, amount=amount,
                founder_pct_pre=signals.founder_ownership_pct,
                new_option_pool_pct=signals.new_option_pool_pct or 0.0,
            ))
        except ValueError:
            diluted = None
        if diluted is not None:
            waterfall_flag = detect_waterfall_flag(
                signals.liquidation_prefs, diluted.founder_pct_post, diluted.post_money)
            if waterfall_flag is not None:
                red_flags.append(waterfall_flag)
    return red_flags


def run_analysis(
    signals: DeckSignals, round_name: str, ask_amount: str | None = None
) -> AnalysisResult:
    """Point d'entrée déterministe : signaux + round (+ montant) -> round et red flags.

    Depuis le pivot, ne calcule plus de score : rassemble les red flags déterministes
    (seuils, incohérences, dilution, waterfall) et les livre avec le round. La couche
    qualitative (collecter_findings) les reprend et les tague. ask_amount optionnel :
    sans lui, l'alerte de dilution est simplement absente.
    """
    return AnalysisResult(
        round=round_name,
        red_flags=collecter_red_flags(signals, round_name, ask_amount),
    )


# Traduction de la sévérité d'un red flag vers une catégorie de constat qualitatif.
# Choix assumé : CRITIQUE bloque (redhibitoire), MAJEUR est une faiblesse réelle,
# MINEUR un simple point de vigilance. Modifiable si la doctrine évolue.
_SEVERITE_VERS_CATEGORIE: dict[str, str] = {
    "CRITIQUE": "redhibitoire",
    "MAJEUR": "faiblesse",
    "MINEUR": "vigilance",
}


def redflag_to_finding(flag: RedFlag) -> Finding:
    """Convertit un red flag déterministe en constat tagué de la couche qualitative."""
    return Finding(
        dimension=flag.dimension,
        categorie=_SEVERITE_VERS_CATEGORIE[flag.severity],
        message=flag.message,
        source="detecteur",
    )


def collecter_findings(
    signals: DeckSignals, round_name: str, ask_amount: str | None = None
) -> list[Finding]:
    """Rassemble tous les constats du deck : détecteurs code + critères éditables (YAML).

    Point d'entrée de l'analyse qualitative qui remplace le score chiffré. Les
    constats des détecteurs (red flags, incohérences, cap table) et ceux des
    critères YAML sont fusionnés en une seule liste, prête à trier en pros/cons.
    """
    findings = [redflag_to_finding(f) for f in collecter_red_flags(signals, round_name, ask_amount)]
    findings += evaluer_criteres(signals, round_name)
    return findings
