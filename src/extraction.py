"""Module d'extraction : envoie le deck à Mistral et récupère l'analyse structurée.

Deux modes : texte (markdown via markitdown, économe en tokens) ou vision (images).
Le mode texte est tenté en premier, fallback sur vision si le PDF est mal parsé.
"""

import base64
import json
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from src.ingestion import convert_to_markdown, group_slides
from src.models import DeckAnalysis

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

Réponds UNIQUEMENT avec un objet JSON valide contenant ces 10 clés, sans texte autour.
Pas de markdown, pas de commentaires, juste le JSON."""

# Modèles Mistral
VISION_MODEL = "pixtral-large-latest"
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


def _parse_response(raw_text: str) -> DeckAnalysis:
    """Parse la réponse brute de Mistral en objet DeckAnalysis."""
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]).strip()

    data = json.loads(raw_text)

    # Filet de sécurité : sous-objets convertis en texte lisible
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = "\n".join(f"{k}: {v}" for k, v in value.items())

    return DeckAnalysis(**data)


def analyze_deck(slides: list[bytes], pdf_path: str | None = None) -> tuple[DeckAnalysis, str]:
    """Analyse un deck en essayant d'abord le mode texte, puis vision en fallback.

    Args:
        slides: images PNG des slides (pour le mode vision)
        pdf_path: chemin du PDF (pour tenter markitdown)

    Returns:
        Tuple (analyse, mode) — mode est "texte" ou "vision" pour informer l'utilisateur.
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
        response = client.chat.complete(model=TEXT_MODEL, messages=messages)
        mode = "texte"
    else:
        #fallback si markitdown échoue
        slides = group_slides(slides)
        messages = _build_vision_messages(slides)
        response = client.chat.complete(model=VISION_MODEL, messages=messages)
        mode = "vision"

    raw_text = response.choices[0].message.content
    analysis = _parse_response(raw_text)

    return analysis, mode
