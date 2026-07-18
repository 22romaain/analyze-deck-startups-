"""Module d'extraction : envoie le deck à Mistral et récupère l'analyse structurée.

Deux modes : texte (markdown via markitdown, économe en tokens) ou vision (images).
Le mode texte est tenté en premier, fallback sur vision si le PDF est mal parsé.
"""

import base64
import json
import os
import time

from dotenv import load_dotenv
from mistralai.client import Mistral

from src.ingestion import convert_to_markdown, group_slides
from src.models import DeckAnalysis, DeckSignals

# Charge les variables du fichier .env (notamment MISTRAL_API_KEY)
load_dotenv()

# Le prompt système définit le rôle et les instructions pour Mistral.
SYSTEM_PROMPT = """Tu es un analyste VC senior. On te présente un pitch deck de startup.

Analyse le deck selon ces 10 dimensions. Pour chaque dimension, sois factuel et précis :
cite les chiffres et éléments présents dans le deck. Si une information est absente,
dis-le explicitement.

Dimensions à analyser :
- equipe : fondateurs, parcours, complémentarité, founder-market fit
- probleme : pour qui, quelle douleur, quelle intensité, preuves du problème
- solution : quoi, comment ça marche, différenciant technique ou usage
- marche : TAM SAM SOM, dynamique du marché, why now
- business_model : comment l'entreprise gagne de l'argent, unit economics si présents
- traction : métriques clés, revenus, utilisateurs, croissance, preuves de validation
- concurrence : concurrents identifiés, positionnement, moat défendable ou non
- go_to_market : canaux d'acquisition, stratégie de distribution, CAC si mentionné
- financials : projections, hypothèses clés, runway, chemin vers rentabilité
- ask : montant recherché, valorisation, use of funds, prochaines étapes

En plus des 10 dimensions, ajoute ces 3 champs :
- company_name : le nom de la société tel qu'écrit dans le deck. null si introuvable.
- detected_round : le round de financement que ce deck cible, parmi : pre-seed, seed, serie-a, serie-b, serie-c, growth. Déduis-le du montant demandé, du stade de maturité et du vocabulaire utilisé.
- ask_amount : le montant recherché extrait du deck, en chiffres avec devise (ex: "2M EUR", "500k USD"). Si absent, écris "non mentionné".

Ajoute enfin un objet "signals" avec des faits chiffrés/booléens, pour un scoring automatique.
RÈGLE ABSOLUE : n'invente jamais. Si une donnée n'est PAS dans le deck, mets null.
Un null est une information (donnée absente), pas un défaut à combler.
Clés de "signals" :
- has_technical_founder : true/false/null. Au moins un fondateur au profil technique.
- product_is_tech : true/false/null. Le coeur du produit est technique.
- founder_ownership_pct : nombre ou null. % du capital détenu par les fondateurs.
- pre_money_valuation : nombre ou null. Valorisation pre-money annoncée pour ce tour, montant brut (ne convertis pas).
- pre_money_currency : "EUR" | "USD" | "GBP" | null. Devise de la valorisation ci-dessus.
- new_option_pool_pct : nombre ou null. Option pool créé au tour, en % du post-money.
- liquidation_prefs : liste d'objets ou []. Chaque préférence connue : {"name", "invested" (montant), "multiple" (ex: 1.0), "participating" (true/false), "as_converted_pct", "seniority" (entier)}. Presque toujours absent d'un pitch deck : mets [] si non mentionné.
- slide_sources : objet ou {}. Pour chaque signal chiffré que tu renseignes, indique le numéro de slide (1 = première slide) d'où vient l'information, ex: {"revenue_amount": 7, "runway_months": 12}. Omets les signaux non renseignés. Ne devine pas un numéro : si tu n'es pas sûr, ne mets pas la clé.
- tam_methodology : "top-down" | "bottom-up" | "both" | null. Méthode de calcul du TAM.
- has_why_now : true/false/null. Le deck justifie explicitement le 'why now'.
- revenue_amount : nombre ou null. Revenu ou ARR annuel, montant brut tel qu'écrit (ne convertis pas).
- revenue_currency : "EUR" | "USD" | "GBP" | null. Devise du revenu ci-dessus.
- growth_rate_pct : nombre ou null. Taux de croissance en %.
- growth_period : "MoM" | "YoY" | null. Période de la croissance.
- churn_rate_pct : nombre ou null. Taux de churn en %.
- churn_period : "monthly" | "annual" | null. Période du churn.
- nrr_pct : nombre ou null. Net Revenue Retention en %.
- burn_multiple : nombre ou null. Burn multiple.
- runway_months : nombre ou null. Runway restant en mois.
- customer_concentration_top1_pct : nombre ou null. % du revenu venant du plus gros client.

RÈGLE DE COUPLAGE (impérative). Un taux sans sa période, ou un montant sans sa devise,
est inutilisable. Ces champs vont par paires indissociables :
- churn_rate_pct <-> churn_period
- growth_rate_pct <-> growth_period
- revenue_amount <-> revenue_currency
- pre_money_valuation <-> pre_money_currency
Pour chaque paire : soit tu renseignes LES DEUX, soit tu mets LES DEUX à null. Ne donne
jamais le taux/montant seul. Si la période ou la devise n'est pas écrite noir sur blanc,
déduis-la du contexte du deck (unité, formulation). Si c'est vraiment indéterminable,
mets les deux à null.

Réponds UNIQUEMENT avec un objet JSON valide : les 13 clés de société/dimensions/round au
premier niveau, plus la clé "signals". Pas de markdown, pas de commentaires, juste le JSON."""

# Modèles Mistral
# Pixtral a été retiré du catalogue Mistral : la vision est désormais intégrée
# aux modèles généralistes. On prend medium (vision OK, plus économe que large).
VISION_MODEL = "mistral-medium-latest"
TEXT_MODEL = "mistral-large-latest"


def _encode_image(image_bytes: bytes) -> str:
    """Encode une image PNG en base64 pour l'API Mistral."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_vision_messages(slides: list[bytes]) -> list[dict]:
    """Construit les messages pour le mode vision (images)."""
    image_blocks = []
    for slide_bytes in slides:
        b64 = _encode_image(slide_bytes)
        image_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })

    image_blocks.append({
        "type": "text",
        "text": "Voici les slides du pitch deck. Analyse-les selon les instructions.",
    })

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": image_blocks},
    ]


def _build_text_messages(markdown: str) -> list[dict]:
    """Construit les messages pour le mode texte (markdown)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Voici le contenu du pitch deck :\n\n{markdown}"},
    ]


def _humanize(value, inline: bool = False) -> str:
    """Rend une valeur JSON (dict/list imbriqués du LLM) en texte lisible.

    Filet quand le LLM structure une dimension au lieu de rédiger : au lieu d'un
    repr Python (`{'nom': ...}`), on produit des lignes `clé : valeur` et des listes
    à puces. inline=True compacte un sous-objet sur une ligne (séparateur ' ; ').
    """
    if isinstance(value, dict):
        parts = [f"{str(k).replace('_', ' ')} : {_humanize(v, inline=True)}"
                 for k, v in value.items()]
        return " ; ".join(parts) if inline else "\n".join(parts)
    if isinstance(value, list):
        if all(not isinstance(x, (dict, list)) for x in value):
            return ", ".join(str(x) for x in value)
        return "\n".join(f"- {_humanize(x, inline=True)}" for x in value)
    return str(value)


def _parse_response(raw_text: str) -> tuple[DeckAnalysis, DeckSignals]:
    """Parse la réponse brute de Mistral en (DeckAnalysis, DeckSignals).

    On sort d'abord le sous-objet 'signals' pour qu'il ne soit pas aplati en
    texte par le filet de sécurité (qui n'est là que pour les dimensions).
    """
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]).strip()

    data = json.loads(raw_text)

    # Extraction des signaux (sous-objet). Absent -> DeckSignals vide (tout None).
    signals_data = data.pop("signals", {}) or {}

    # Filet de sécurité : le LLM structure parfois une dimension (dict/list) au lieu
    # de rédiger. On rend ça en texte lisible plutôt qu'en repr Python brut.
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            data[key] = _humanize(value)

    return DeckAnalysis(**data), DeckSignals(**signals_data)


# Attentes (en secondes) entre deux essais Mistral. Calées sur le tier gratuit
# (~2 requêtes/minute) : on patiente vraiment avant de réessayer.
RETRY_WAITS_SECONDS = (20, 40, 60)


def _is_retryable(exc: Exception) -> bool:
    """Vrai si l'erreur mérite un réessai : rate limit ou aléa transitoire du serveur."""
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    text = str(exc).lower()
    return any(s in text for s in ("rate limit", "429", "timeout", "temporarily", "overloaded"))


def _complete_with_retry(client, model, messages, sleep=time.sleep):
    """Appelle Mistral en réessayant sur les erreurs transitoires (rate limit surtout).

    Le tier gratuit plafonne à ~2 requêtes/minute : plutôt qu'échouer au premier 429,
    on patiente et on réessaie. Les autres erreurs (clé invalide, JSON) remontent direct.
    sleep injectable pour tester sans attendre réellement.
    """
    last_exc: Exception | None = None
    for wait in (0, *RETRY_WAITS_SECONDS):
        if wait:
            sleep(wait)
        try:
            return client.chat.complete(model=model, messages=messages)
        except Exception as exc:
            if not _is_retryable(exc):
                raise
            last_exc = exc
    raise RuntimeError(
        f"Mistral inaccessible après {len(RETRY_WAITS_SECONDS)} réessais (rate limit ?) : {last_exc}"
    )


def analyze_deck(slides: list[bytes], pdf_path: str | None = None) -> tuple[DeckAnalysis, DeckSignals, str]:
    """Analyse un deck en essayant d'abord le mode texte, puis vision en fallback.

    Args:
        slides: images PNG des slides (pour le mode vision)
        pdf_path: chemin du PDF (pour tenter markitdown)

    Returns:
        Tuple (analyse, signals, mode) — mode est "texte" ou "vision" pour informer l'utilisateur.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL_API_KEY absente. Vérifier le fichier .env à la racine du projet."
        )

    client = Mistral(api_key=api_key)

    #transforme le PDF en texte si le chemin est fourni
    markdown = None
    if pdf_path:
        markdown = convert_to_markdown(pdf_path)

    if markdown:
        #economise les tokens
        messages = _build_text_messages(markdown)
        response = _complete_with_retry(client, TEXT_MODEL, messages)
        mode = "texte"
    else:
        #fallback si markitdown échoue
        slides = group_slides(slides)
        messages = _build_vision_messages(slides)
        response = _complete_with_retry(client, VISION_MODEL, messages)
        mode = "vision"

    raw_text = response.choices[0].message.content
    analysis, signals = _parse_response(raw_text)

    return analysis, signals, mode
