"""Modèles Pydantic : structure des données extraites du deck.

Pydantic valide automatiquement que le JSON renvoyé par le LLM respecte
le schéma attendu. Si un champ manque ou a le mauvais type, on le sait
tout de suite au lieu de découvrir un bug plus loin dans le pipeline.
Analogie : c'est la checklist due diligence — on définit ce qu'on veut
avant d'ouvrir la data room.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.captable import LiquidationPref


class DeckAnalysis(BaseModel):
    """Analyse structurée d'un pitch deck selon les dimensions VC classiques."""

    company_name: str | None = Field(
        default=None, description="Nom de la société tel qu'écrit dans le deck. None si introuvable."
    )
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
    detected_round: str = Field(
        description="Round de financement détecté : pre-seed, seed, serie-a, serie-b, serie-c ou growth"
    )
    ask_amount: str = Field(
        description="Montant recherché extrait du deck, en chiffres avec devise (ex: '2M EUR', '500k USD'). 'non mentionné' si absent."
    )


class RawFigure(BaseModel):
    """Un chiffre du deck capté tel quel, sans le forcer dans le schéma de notation.

    Rôle distinct des champs typés de DeckSignals : ceux-ci sont le contrat de
    scoring (peu de champs, unités normalisées), ceux-là sont l'inventaire fidèle
    de ce que le deck affiche. Un CAGR, un NPS, un panier moyen n'ont pas de champ
    de notation mais méritent d'être vus. On préserve l'échelle et l'unité brutes :
    'valeur 1, unite "M USD"' reste rattrapable, là où un revenue_amount à 1 est
    déjà détruit. Point de départ aussi pour la traçabilité slide (docs §7).
    """
    libelle: str = Field(description="Nom de la métrique tel qu'écrit (ex: 'ARR', 'CAGR', 'CAC').")
    valeur: float = Field(description="Valeur numérique telle qu'écrite, sans développer l'échelle.")
    unite: str | None = Field(default=None, description="Unité brute : '%', 'M USD', 'k EUR', 'x'... None si aucune.")
    periode: str | None = Field(default=None, description="Période ou millésime associé (ex: '2024', 'MoM', '2021-2024'). None si aucun.")
    slide: int | None = Field(default=None, description="Numéro de slide source (1 = première). None si incertain.")


class DeckSignals(BaseModel):
    """Signaux factuels typés extraits du deck : la matière du scoring déterministe.

    Tous les champs sont optionnels. None signifie 'absent du deck', ce qui est
    un signal en soi (principe 1.1 du référentiel), jamais une valeur neutre.
    Le LLM ne remplit que ce qu'il trouve, il n'invente pas.
    """

    # Équipe
    has_technical_founder: bool | None = Field(
        default=None, description="Au moins un fondateur a un profil technique (ingénieur, dev, PhD tech). None si indéterminable."
    )
    product_is_tech: bool | None = Field(
        default=None, description="Le coeur du produit est technique (le différenciant repose sur de la tech). None si indéterminable."
    )
    # Qualité de l'équipe : décisif en pre-seed/seed, où l'on parie sur les personnes
    # faute de traction. None = le deck ne permet pas de trancher (pas 'false par défaut').
    founder_domain_years: float | None = Field(
        default=None, description="Années d'expérience cumulées des fondateurs dans le secteur du projet (ex: 8.0). None si non déductible."
    )
    founder_is_repeat: bool | None = Field(
        default=None, description="Au moins un fondateur a déjà créé une startup (repeat founder). None si indéterminable."
    )
    founder_prior_exit: bool | None = Field(
        default=None, description="Au moins un fondateur a déjà réalisé une sortie (rachat, IPO). None si indéterminable."
    )
    founder_unique_insight: bool | None = Field(
        default=None, description="Le deck articule un insight propre et non évident sur le marché (angle contrariant, expérience vécue du problème). None si absent ou générique."
    )
    team_complete: bool | None = Field(
        default=None, description="L'équipe couvre les fonctions clés du projet (tech ET business/go-to-market). None si indéterminable."
    )
    founder_ownership_pct: float | None = Field(
        default=None, description="Part du capital détenue par les fondateurs, en pourcentage (ex: 55.0). None si absent."
    )
    pre_money_valuation: float | None = Field(
        default=None, description="Valorisation pre-money annoncée pour ce tour, montant brut. None si absente."
    )
    pre_money_currency: Literal["EUR", "USD", "GBP"] | None = Field(
        default=None, description="Devise de la valorisation pre-money : EUR, USD ou GBP. None si absente."
    )
    new_option_pool_pct: float | None = Field(
        default=None, description="Option pool créé au tour, en pourcentage du post-money. None si absent."
    )
    liquidation_prefs: list[LiquidationPref] = Field(
        default_factory=list,
        description="Tranches de liquidation preferences connues. Souvent absentes d'un pitch deck (term sheet)."
    )
    slide_sources: dict[str, int] = Field(
        default_factory=dict,
        description="Traçabilité : pour chaque signal renseigné, le numéro de slide d'où il vient (au mieux)."
    )
    chiffres_bruts: list[RawFigure] = Field(
        default_factory=list,
        description="Inventaire de tous les chiffres du deck, captés tels quels (voir RawFigure). Complète les champs typés sans les remplacer."
    )

    # Marché
    tam_methodology: Literal["top-down", "bottom-up", "both"] | None = Field(
        default=None, description="Méthode de calcul du TAM : top-down (part d'un grand marché), bottom-up (clients x prix), both, ou None si absent."
    )
    has_why_now: bool | None = Field(
        default=None, description="Le deck justifie explicitement le 'why now' (pourquoi ce marché maintenant). None si indéterminable."
    )

    # Traction et unit economics
    revenue_amount: float | None = Field(
        default=None, description="Revenu ou ARR annuel, montant brut tel qu'écrit dans le deck (ex: 150000.0). None si absent."
    )
    revenue_currency: Literal["EUR", "USD", "GBP"] | None = Field(
        default=None, description="Devise du revenu : EUR, USD ou GBP. None si absent ou autre devise."
    )
    growth_rate_pct: float | None = Field(
        default=None, description="Taux de croissance en pourcentage (ex: 15.0). None si absent."
    )
    growth_period: Literal["MoM", "YoY"] | None = Field(
        default=None, description="Période du taux de croissance : MoM (mensuel) ou YoY (annuel). None si absent."
    )
    churn_rate_pct: float | None = Field(
        default=None, description="Taux de churn en pourcentage (ex: 5.0). None si absent."
    )
    churn_period: Literal["monthly", "annual"] | None = Field(
        default=None, description="Période du churn : monthly ou annual. None si absent."
    )
    nrr_pct: float | None = Field(
        default=None, description="Net Revenue Retention en pourcentage (ex: 110.0). None si absent."
    )
    burn_multiple: float | None = Field(
        default=None, description="Burn multiple (cash brûlé / net new ARR, ex: 1.5). None si absent."
    )
    runway_months: float | None = Field(
        default=None, description="Runway restant en mois (ex: 12.0). None si absent."
    )
    customer_concentration_top1_pct: float | None = Field(
        default=None, description="Part du revenu venant du plus gros client, en pourcentage (ex: 30.0). None si absent."
    )
    # Unit economics : décisif en série A+, où l'on note l'efficacité du modèle, pas
    # la promesse. Sans unité problématique (ratio, mois, %), donc pas de couplage.
    ltv_cac_ratio: float | None = Field(
        default=None, description="Rapport LTV / CAC (ex: 3.0 pour 3:1). None si absent ou non calculable depuis le deck."
    )
    cac_payback_months: float | None = Field(
        default=None, description="Délai de récupération du CAC, en mois (ex: 14.0). None si absent."
    )
    gross_margin_pct: float | None = Field(
        default=None, description="Marge brute en pourcentage (ex: 78.0). None si absente."
    )

    @field_validator("slide_sources", mode="before")
    @classmethod
    def _clean_slide_sources(cls, value: object) -> dict[str, int]:
        """Le LLM met parfois des null ou des valeurs non entières : on ne garde que les
        slides exploitables (un entier), on jette le reste sans faire échouer l'extraction."""
        if not isinstance(value, dict):
            return {}
        cleaned: dict[str, int] = {}
        for key, raw in value.items():
            try:
                if raw is not None:
                    cleaned[str(key)] = int(raw)
            except (TypeError, ValueError):
                continue
        return cleaned

    @field_validator("liquidation_prefs", mode="before")
    @classmethod
    def _default_prefs_if_null(cls, value: object) -> object:
        """Le LLM peut renvoyer null au lieu d'une liste vide : on retombe sur []."""
        return value if isinstance(value, list) else []

    @field_validator("chiffres_bruts", mode="before")
    @classmethod
    def _drop_unusable_figures(cls, value: object) -> object:
        """Jette les entrées sans libellé ou sans valeur numérique, sans faire échouer
        l'extraction. Un chiffre brut sert de preuve visible : sans nom ni nombre, il
        n'apporte rien. On tolère une liste imparfaite plutôt que de perdre tout l'inventaire."""
        if not isinstance(value, list):
            return []
        usable = []
        for item in value:
            if not isinstance(item, dict) or item.get("libelle") in (None, ""):
                continue
            try:
                float(item["valeur"])
            except (KeyError, TypeError, ValueError):
                continue
            usable.append(item)
        return usable

    @model_validator(mode="after")
    def _enforce_couples(self) -> "DeckSignals":
        """Garantit qu'un taux/montant ne survit jamais sans son unité.

        Un churn sans période, une croissance sans période, un revenu sans devise
        sont inexploitables et souvent le signe d'un chiffre inventé. Si une seule
        moitié d'une paire est présente, on remet LES DEUX à None. On jette la donnée
        incomplète plutôt que de deviner l'unité (deviner fausserait le jugement).
        """
        # pre_money_valuation n'est PAS couplé à sa devise : la dilution ne dépend que
        # du ratio montant/valo, la devise s'annule. On garde donc la valo même sans devise.
        couples = [
            ("churn_rate_pct", "churn_period"),
            ("growth_rate_pct", "growth_period"),
            ("revenue_amount", "revenue_currency"),
        ]
        for value_field, unit_field in couples:
            has_value = getattr(self, value_field) is not None
            has_unit = getattr(self, unit_field) is not None
            if has_value != has_unit:  # exactement une des deux moitiés
                setattr(self, value_field, None)
                setattr(self, unit_field, None)
        return self


# Fourchettes de tickets par round (en EUR) — tirées du référentiel critères
ROUND_TICKET_RANGES: dict[str, tuple[float, float]] = {
    "pre-seed": (100_000, 750_000),
    "seed": (500_000, 3_000_000),
    "serie-a": (5_000_000, 15_000_000),
    "serie-b": (15_000_000, 50_000_000),
    "serie-c": (30_000_000, 100_000_000),
    "growth": (50_000_000, 200_000_000),
}

ROUND_OPTIONS: list[str] = ["pre-seed", "seed", "serie-a", "serie-b", "serie-c", "growth"]


# Taux de change approximatifs vers l'euro. Volontairement fixes et lisibles :
# ils servent à comparer des ordres de grandeur entre eux (revenu vs fourchette de
# round), pas à faire de la compta. Un appel externe au taux réel serait plus juste
# mais introduirait une dépendance réseau pour un gain négligeable ici.
FX_TO_EUR: dict[str, float] = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17}


def revenue_in_eur(amount: float | None, currency: str | None) -> float | None:
    """Convertit un revenu (montant + devise) en euros pour permettre les comparaisons.

    Retourne None si le montant est absent ou la devise inconnue : on ne compare
    que ce qu'on peut convertir de façon fiable.
    """
    if amount is None or currency is None:
        return None
    rate = FX_TO_EUR.get(currency)
    if rate is None:
        return None
    return amount * rate


# --- Résultats du scoring déterministe (étape 2) ---

# Niveaux de sévérité tels qu'ils apparaissent dans le référentiel critères.
Severity = Literal["CRITIQUE", "MAJEUR", "MINEUR"]


class RedFlag(BaseModel):
    """Un signal d'alerte détecté par du code, pas par le LLM.

    dimension : la clé de dimension concernée (ex: 'equipe').
    severity : CRITIQUE, MAJEUR ou MINEUR.
    message : explication lisible, auditable (on sait pourquoi il s'est déclenché).
    """

    dimension: str
    severity: Severity
    message: str


# --- Analyse qualitative (constats tagués, remplace le score chiffré) ---

# Catégories d'un constat. Trois polarités : ce qui plaide contre, ce qui plaide
# pour, ce qui reste à éclaircir. Ces noms servent aussi de vocabulaire dans le
# fichier de critères éditable (config/criteres.yaml) : l'utilisateur range chaque
# critère dans l'une de ces catégories.
FindingCategory = Literal[
    "redhibitoire",         # bloquant à ce stade, tue le deal en l'état
    "vigilance",            # à surveiller / creuser en due diligence, pas bloquant
    "faiblesse",            # un attendu du round n'est pas rempli
    "avantage_competitif",  # moat, différenciant défendable
    "atout_equipe",         # founder-market fit, insight propre, expertise rare
    "a_creuser",            # donnée manquante : ni bon ni mauvais, question à poser
]


class Finding(BaseModel):
    """Un constat qualitatif tagué : l'atome de l'analyse qui remplace la note.

    dimension : la clé de dimension concernée (ex: 'equipe').
    categorie : une des FindingCategory (porte à la fois le sens et la polarité).
    message : le constat, lisible et auto-porteur.
    source : d'où il vient (ex: 'critere:equipe_insight', 'detecteur:red_flags'),
             pour rester auditable comme les 'rationale' du scoring d'avant.
    """

    dimension: str
    categorie: FindingCategory
    message: str
    source: str | None = None


# Métadonnées d'affichage par catégorie : polarité (pour trier pros/cons), libellé
# lisible, ordre d'apparition dans le mémo. Une seule source de vérité, les renderers
# la lisent au lieu de recoder la logique de tri à chaque endroit.
FINDING_CATEGORIES: dict[str, dict[str, object]] = {
    "redhibitoire":        {"polarite": "negatif", "label": "Rédhibitoire", "ordre": 0},
    "faiblesse":           {"polarite": "negatif", "label": "Faiblesse / attendu manquant", "ordre": 1},
    "vigilance":           {"polarite": "negatif", "label": "Point de vigilance", "ordre": 2},
    "avantage_competitif": {"polarite": "positif", "label": "Avantage compétitif", "ordre": 3},
    "atout_equipe":        {"polarite": "positif", "label": "Atout d'équipe / expertise", "ordre": 4},
    "a_creuser":           {"polarite": "neutre",  "label": "À creuser / donnée manquante", "ordre": 5},
}


class AnalysisResult(BaseModel):
    """Résultat du volet déterministe : le round et les red flags détectés.

    Depuis le pivot, plus de score : la couche qualitative (Finding) reprend ces
    red flags et les range en constats tagués.
    """

    round: str
    red_flags: list[RedFlag]


def parse_amount(amount_str: str) -> float | None:
    """Convertit un montant texte ('2M EUR', '500k USD') en nombre.

    Retourne None si le montant n'est pas parsable.
    """
    if not amount_str or "non mentionné" in amount_str.lower():
        return None

    import re
    # Cherche un nombre suivi optionnellement de k/M/B
    match = re.search(r"([\d.,]+)\s*(k|m|b|M|K|B)?", amount_str, re.IGNORECASE)
    if not match:
        return None

    number = float(match.group(1).replace(",", "."))
    multiplier = match.group(2)
    if multiplier:
        multiplier = multiplier.upper()
        if multiplier == "K":
            number *= 1_000
        elif multiplier == "M":
            number *= 1_000_000
        elif multiplier == "B":
            number *= 1_000_000_000

    return number


def check_round_coherence(detected_round: str, ask_amount: str) -> str | None:
    """Vérifie la cohérence entre le round détecté et le montant demandé.

    Retourne un message d'alerte si incohérent, None si OK.
    """
    amount = parse_amount(ask_amount)
    if amount is None:
        return None  # Pas de montant, pas de vérification possible

    if detected_round not in ROUND_TICKET_RANGES:
        return None

    min_ticket, max_ticket = ROUND_TICKET_RANGES[detected_round]
    if amount < min_ticket:
        return f"Le montant ({ask_amount}) est inférieur à la fourchette habituelle pour un {detected_round} ({min_ticket/1e6:.1f}M - {max_ticket/1e6:.1f}M EUR)."
    if amount > max_ticket:
        return f"Le montant ({ask_amount}) est supérieur à la fourchette habituelle pour un {detected_round} ({min_ticket/1e6:.1f}M - {max_ticket/1e6:.1f}M EUR)."

    return None


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
