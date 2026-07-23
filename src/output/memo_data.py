"""Agrégat du mémo et logique de préparation (couche déterministe).

Toute la logique de préparation du mémo vit ici : collecte des constats, synthèse,
grille, sections par dimension. Les renderers (markdown, docx, pdf, streamlit) ne font
que mettre en forme ce que ce module produit. Analogie : ce fichier est l'onglet de
calcul du modèle, les renderers sont les mises en page d'impression.

Depuis le pivot, aucun score : l'analyse est qualitative (constats tagués).
"""

import re
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from src.analysis import ROUND_WEIGHTS, collecter_findings
from src.captable import (
    DilutionResult,
    RoundInput,
    WaterfallResult,
    compute_dilution,
    compute_waterfall,
)
from src.models import (
    DIMENSION_LABELS,
    FINDING_CATEGORIES,
    AnalysisResult,
    DeckAnalysis,
    DeckSignals,
    Finding,
    Severity,
    parse_amount,
)
from src.output.synthese import Synthese, build_synthese


# --- Config du mémo (typée et validée au chargement) ---

class AttenduSignal(BaseModel):
    """Un signal typé attendu à un stade donné (§5.4). Son absence est un signal."""
    signal: str  # nom du champ dans DeckSignals
    label: str
    criticite: Severity


class MemoConfig(BaseModel):
    """Config du mémo. Depuis le pivot, seuls les attendus par round et le nom de repli
    servent (le verdict et les grades chiffrés ont disparu). Les clés en trop dans le
    JSON (verdict, grades, benchmarks) sont simplement ignorées."""
    societe_fallback: str
    attendus_par_round: dict[str, list[AttenduSignal]]
    version_referentiel: str


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


# --- Sous-modèles du mémo (structure, aucune logique) ---

class DeckFigureRow(BaseModel):
    """Un chiffre brut du deck, mis en forme pour l'affichage (inventaire 'ce que le
    deck affirme'). On ne juge pas, on restitue."""
    libelle: str
    valeur: str          # déjà formatée (valeur + unité), les renderers ne calculent pas
    periode: str | None
    slide: int | None = None


class DoctrineCitation(BaseModel):
    """Un extrait de doctrine VC (tes cours perso) cité en appui d'une dimension.

    On ne garde qu'un extrait court : le mémo pointe vers la source, il ne recopie
    pas le cours entier. distance = proximité à la requête (plus petit = plus proche)."""
    source: str
    section: str
    extrait: str
    distance: float


class ReviewBlock(BaseModel):
    """La contre-analyse LLM. Porte le mode dégradé tant que la brique n'existe pas."""
    disponible: bool
    bandeau: str
    contenu: str | None


class CapTableSection(BaseModel):
    """Section cap table du mémo : dilution du tour, et waterfall de sortie si connu.

    Réutilise les modèles du moteur (DilutionResult, WaterfallResult) comme sous-objets.
    calculable = False quand un terme indispensable manque (valo pre-money, part
    fondateurs, montant levé) : on liste alors ce qui manque plutôt que d'inventer
    des chiffres. waterfall reste None hors term sheet (liquidation prefs inconnues).
    """
    calculable: bool
    donnees_absentes: list[str]          # termes manquants qui bloquent le calcul
    pre_money: float | None
    amount: float | None
    founder_pct_pre: float | None
    dilution: DilutionResult | None
    waterfall: WaterfallResult | None


class Annexes(BaseModel):
    """Méthodologie, limites, et extraction brute pour audit."""
    methodologie: str
    limites: str
    extraction_brute: dict


# Disclaimer affiché en tête du mémo : l'analyse n'est pas une vérité de marché mais
# le cadre assumé du créateur, en plus des grands principes VC du référentiel.
DISCLAIMER = (
    "Analyse fondée sur les critères et la thèse d'investissement subjectifs du créateur "
    "de l'app, en complément des grands principes VC du référentiel (dossier courses/). "
    "Ce n'est pas une vérité de marché : les seuils et priorités reflètent un cadre assumé."
)


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


# --- Grille d'attendus par round (présent / absent / inconnu) ---

# Statut d'un attendu du stade. Dans l'esprit "l'absence est un signal" (§1.1),
# mais on distingue le nié (booléen False) du tu (None) : ce n'est pas pareil.
GrilleStatut = Literal["PRESENT", "ABSENT", "INCONNU"]


class GrilleRow(BaseModel):
    """Une ligne de la grille : ce que le stade exige, et si le deck le couvre.

    PRESENT = le deck le renseigne ; ABSENT = explicitement nié (booléen à False) ;
    INCONNU = le deck n'en dit rien (signal à None).
    """
    label: str
    criticite: Severity
    statut: GrilleStatut
    valeur: str | None


def build_grille(
    signals: DeckSignals, round_name: str, config: MemoConfig
) -> list[GrilleRow]:
    """Confronte chaque attendu du round au deck : présent, nié, ou inconnu."""
    rows: list[GrilleRow] = []
    for attendu in config.attendus_par_round.get(round_name, []):
        value = getattr(signals, attendu.signal)
        if value is None:
            statut: GrilleStatut = "INCONNU"
        elif value is False:
            statut = "ABSENT"
        else:
            statut = "PRESENT"
        rows.append(GrilleRow(
            label=attendu.label,
            criticite=attendu.criticite,
            statut=statut,
            valeur=_format_signal_value(attendu.signal, signals),
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


def _aplatir_extrait(text: str) -> str:
    """Réduit un passage de cours à une phrase citable, sans balisage.

    Les cours sont écrits en Markdown : un passage brut porte des '**', des puces
    et des retours à la ligne. Réinjecté tel quel dans le mémo (lui-même en
    Markdown) ou dans un libellé Streamlit, ce balisage est réinterprété et casse
    la mise en forme autour de la citation. On neutralise ici, une fois, plutôt que
    dans chacun des quatre renderers : la citation est une donnée, pas une mise en page.
    """
    plat = " ".join(text.split())        # retours à la ligne et indentation
    plat = plat.replace("*", "")         # gras et italique markdown
    return re.sub(r"^[-•]\s*", "", plat)  # puce de tête


def _couper_aux_mots(text: str, limite: int) -> str:
    """Tronque sans casser le dernier mot. Une citation coupée en plein mot fait
    douter de la source autant que du contenu."""
    if len(text) <= limite:
        return text
    # limite - 1 : l'ellipse occupe un caractère, la borne reste respectée.
    return text[:limite - 1].rsplit(" ", 1)[0] + "…"


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
            extrait=_couper_aux_mots(_aplatir_extrait(hit.text), DOCTRINE_EXTRACT_CHARS),
            distance=hit.distance,
        )
        for hit in hits
        if hit.distance <= ceiling
    ]


# --- Analyse par dimension (récit du deck + constats, sans score) ---

class DimensionQualitative(BaseModel):
    """Bloc d'analyse d'une dimension SANS score : le récit du deck et les constats.

    narratif = ce que le deck raconte (texte du LLM). findings = les constats tagués
    rattachés à cette dimension, triés par gravité. doctrine = citations RAG optionnelles.
    Aucun score, poids ni grade : on ne note plus, on donne à lire.
    """
    dimension: str
    label: str
    narratif: str | None
    findings: list[Finding]
    doctrine: list[DoctrineCitation] = Field(default_factory=list)


def build_dimensions_qualitatives(
    deck: DeckAnalysis,
    findings: list[Finding],
    round_name: str,
    retriever=None,
    doctrine_dimensions: set[str] | None = None,
) -> list[DimensionQualitative]:
    """Une section par dimension : narratif du deck + constats rattachés + doctrine.

    Ordre : dimensions du round d'abord (ROUND_WEIGHTS, décroissant), puis les autres
    par ordre alphabétique. ROUND_WEIGHTS ne sert plus qu'à ORDONNER l'affichage (les
    dimensions décisives du stade en haut), plus à noter. Toutes les dimensions sont
    affichées : chacune porte le récit du deck, même sans constat.
    """
    weights = ROUND_WEIGHTS.get(round_name, {})
    findings_by_dim: dict[str, list[Finding]] = {}
    for f in findings:
        findings_by_dim.setdefault(f.dimension, []).append(f)

    ordered = sorted(DIMENSION_LABELS, key=lambda d: (-weights.get(d, 0.0), d))
    sections: list[DimensionQualitative] = []
    for dim in ordered:
        want_doctrine = retriever is not None and (
            doctrine_dimensions is None or dim in doctrine_dimensions
        )
        query = DIMENSION_DOCTRINE_QUERY.get(dim, DIMENSION_LABELS[dim])
        cite = cite_doctrine(query, retriever=retriever) if want_doctrine else []
        dim_findings = sorted(
            findings_by_dim.get(dim, []),
            key=lambda f: FINDING_CATEGORIES[f.categorie]["ordre"],
        )
        sections.append(DimensionQualitative(
            dimension=dim, label=DIMENSION_LABELS[dim],
            narratif=getattr(deck, dim, None),
            findings=dim_findings, doctrine=cite,
        ))
    return sections


# --- Contre-analyse (section 6) ---

# Bandeaux fixes : le mode dégradé et le mode disponible portent un message exact.
REVIEW_BANDEAU_INDISPONIBLE = "Contre-analyse indisponible (erreur API)."
REVIEW_BANDEAU_DISPONIBLE = "Critique générée par LLM. Hors analyse déterministe. Non reproductible."


def build_review_block(review_content: str | None = None) -> ReviewBlock:
    """Section 6 : contre-analyse. None -> encart dégradé, le mémo se génère quand même."""
    if review_content is None:
        return ReviewBlock(disponible=False, bandeau=REVIEW_BANDEAU_INDISPONIBLE, contenu=None)
    return ReviewBlock(disponible=True, bandeau=REVIEW_BANDEAU_DISPONIBLE, contenu=review_content)


# --- Cap table et dilution (section 7) ---

# Termes indispensables au calcul de dilution, avec leur libellé lisible.
_CAPTABLE_REQUIRED = {
    "pre_money": "Valorisation pre-money",
    "founder_pct_pre": "Part des fondateurs au capital",
    "amount": "Montant levé (l'ask)",
}


def build_captable_section(signals: DeckSignals, ask_amount: str | None) -> CapTableSection:
    """Section cap table déterministe : dilution du tour, waterfall si prefs connues.

    Aucun chiffre inventé : si un terme indispensable manque, calculable=False et on
    liste les manques. Miroir de detect_dilution_flag/detect_waterfall_flag (même
    hypothèse de sortie au post-money) pour que mémo et red flags concordent.
    """
    pre_money = signals.pre_money_valuation
    founder_pct_pre = signals.founder_ownership_pct
    amount = parse_amount(ask_amount) if ask_amount else None

    present = {"pre_money": pre_money, "founder_pct_pre": founder_pct_pre, "amount": amount}
    manquants = [lib for cle, lib in _CAPTABLE_REQUIRED.items() if present[cle] is None]
    if manquants:
        return CapTableSection(
            calculable=False, donnees_absentes=manquants,
            pre_money=pre_money, amount=amount, founder_pct_pre=founder_pct_pre,
            dilution=None, waterfall=None,
        )

    try:
        dilution = compute_dilution(RoundInput(
            pre_money=pre_money, amount=amount, founder_pct_pre=founder_pct_pre,
            new_option_pool_pct=signals.new_option_pool_pct or 0.0,
        ))
    except ValueError:
        # Termes incohérents (>100% prélevé) : on renonce plutôt que sortir un faux chiffre.
        return CapTableSection(
            calculable=False,
            donnees_absentes=["Termes du tour incohérents (investisseur + option pool > 100%)"],
            pre_money=pre_money, amount=amount, founder_pct_pre=founder_pct_pre,
            dilution=None, waterfall=None,
        )

    # Waterfall : seulement si des liquidation prefs sont connues (rare hors term sheet).
    # Part fondateurs à l'exit = leur détention APRÈS ce tour (post-dilution), miroir exact
    # de detect_waterfall_flag pour que mémo et red flag concordent.
    waterfall = None
    if signals.liquidation_prefs:
        waterfall = compute_waterfall(
            dilution.post_money, signals.liquidation_prefs, dilution.founder_pct_post)

    return CapTableSection(
        calculable=True, donnees_absentes=[],
        pre_money=pre_money, amount=amount, founder_pct_pre=founder_pct_pre,
        dilution=dilution, waterfall=waterfall,
    )


# --- Annexes (section 8) ---

def build_annexes(deck: DeckAnalysis, config: MemoConfig, review_disponible: bool) -> Annexes:
    """Méthodologie (approche qualitative, sans score), limites, extraction brute."""
    methodologie = (
        "Trois couches : (1) extraction des slides par LLM vision, (2) analyse "
        "déterministe sans LLM produisant des constats tagués, à partir de critères "
        "éditables (config/criteres.yaml) et de détecteurs de red flags, d'incohérences "
        "et de cap table, (3) mise en forme du mémo. Pas de score chiffré : les constats "
        "sont rangés par catégorie et la recommandation en découle (un rédhibitoire "
        "renvoie à approfondir, jamais à un rejet automatique ; l'analyste tranche). "
        f"Référentiel : {config.version_referentiel}."
    )
    limites = [
        "Traçabilité slide partielle : les constats ne sont pas encore reliés à leur slide source.",
        "Analyse fondée sur les critères subjectifs du créateur : à confronter au jugement de l'analyste.",
    ]
    if not review_disponible:
        limites.append("Contre-analyse LLM absente (brique non encore construite).")
    return Annexes(
        methodologie=methodologie,
        limites=" ".join(limites),
        extraction_brute=deck.model_dump(),
    )


def build_deck_figures(signals: DeckSignals) -> list[DeckFigureRow]:
    """Met en forme l'inventaire brut du deck pour l'affichage (section 'ce que le deck
    affirme'). Ne juge ni ne normalise : la valeur et l'unité sont recomposées telles
    quelles ('140 %', '1,2 M USD'). Ordre d'extraction préservé (ordre du deck au mieux)."""
    rows: list[DeckFigureRow] = []
    for fig in signals.chiffres_bruts:
        # valeur sans décimale superflue : 140.0 -> '140', 1.2 -> '1,2'.
        nombre = f"{fig.valeur:g}".replace(".", ",")
        valeur = f"{nombre} {fig.unite}".strip() if fig.unite else nombre
        rows.append(DeckFigureRow(
            libelle=fig.libelle, valeur=valeur, periode=fig.periode, slide=fig.slide,
        ))
    return rows


# --- Agrégat complet et assemblage ---

class MemoData(BaseModel):
    """Agrégat complet du mémo pivoté (analyse qualitative, sans score).

    Tous les champs sont requis : un mémo partiel échoue à la construction en nommant
    le champ manquant, plutôt que de sortir faux. `synthese` remplace verdict + forces
    + faiblesses ; `grille` remplace tableau de bord + données manquantes ; `dimensions`
    ne portent plus de score.
    """
    societe: str
    round: str
    ask_amount: str
    date: date
    disclaimer: str
    synthese: Synthese
    grille: list[GrilleRow]
    chiffres_deck: list[DeckFigureRow]
    dimensions: list[DimensionQualitative]
    incoherences: list[Finding]
    contre_analyse: ReviewBlock
    cap_table: CapTableSection
    annexes: Annexes


# Préfixe conventionnel d'un constat d'incohérence interne (posé par detect_incoherences).
_INCOHERENCE_PREFIX = "Incohérence interne"


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
    """Assemble l'agrégat du mémo qualitatif à partir des couches amont.

    Ne calcule rien de nouveau : collecte les constats (collecter_findings), les met
    en synthèse, en grille et par dimension. `analysis` sert pour son round et alimente
    la collecte via les red flags qu'il porte. `review` = contenu de la contre-analyse
    (None tant que la brique n'existe pas). `retriever` = source de doctrine RAG (None =
    mémo construit hors ligne).
    """
    day = today or date.today()
    findings = collecter_findings(signals, analysis.round, deck.ask_amount)
    review_block = build_review_block(review)
    return MemoData(
        societe=societe or deck.company_name or config.societe_fallback,
        round=analysis.round,
        ask_amount=deck.ask_amount,
        date=day,
        disclaimer=DISCLAIMER,
        synthese=build_synthese(findings),
        grille=build_grille(signals, analysis.round, config),
        chiffres_deck=build_deck_figures(signals),
        dimensions=build_dimensions_qualitatives(deck, findings, analysis.round, retriever, doctrine_dimensions),
        incoherences=[f for f in findings if f.message.startswith(_INCOHERENCE_PREFIX)],
        contre_analyse=review_block,
        cap_table=build_captable_section(signals, deck.ask_amount),
        annexes=build_annexes(deck, config, review_block.disponible),
    )
