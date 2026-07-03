"""Module d'extraction : envoie les images de slides à Mistral vision et récupère l'analyse structurée."""

import base64
import json
import os

from dotenv import load_dotenv
from mistralai import Mistral

from src.models import DeckAnalysis

# Charge les variables du fichier .env (notamment MISTRAL_API_KEY)
load_dotenv()

# Le prompt système définit le rôle et les instructions pour Mistral.
# C'est ici que tu peux ajuster le comportement de l'analyse.
SYSTEM_PROMPT = """Tu es un analyste VC senior. On te présente les slides d'un pitch deck de startup.

Analyse le deck selon ces 10 dimensions. Pour chaque dimension, sois factuel et précis :
cite les chiffres et éléments visibles dans les slides. Si une information est absente
du deck, dis-le explicitement.

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


def _encode_image(image_bytes: bytes) -> str:
    """Encode une image PNG en base64 pour l'API Mistral.

    L'API attend les images sous forme de texte base64 dans le JSON,
    pas des bytes bruts. C'est une conversion réversible, sans perte.
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_messages(slides: list[bytes]) -> list[dict]:
    """Construit la liste de messages pour l'API Mistral.

    On envoie toutes les slides dans un seul message utilisateur
    pour respecter le rate limit (2 req/min sur le tier gratuit).
    """
    # Chaque image devient un bloc "image_url" dans le contenu du message
    image_blocks = []
    for slide_bytes in slides:
        b64 = _encode_image(slide_bytes)
        image_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })

    # Le texte qui accompagne les images
    image_blocks.append({
        "type": "text",
        "text": "Voici les slides du pitch deck. Analyse-les selon les instructions.",
    })

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": image_blocks},
    ]


# Nom du modèle vision Mistral — vérifié dans la doc Mistral (juillet 2025)
MODEL_NAME = "pixtral-large-latest"


def analyze_deck(slides: list[bytes]) -> DeckAnalysis:
    """Envoie les slides à Mistral vision et retourne l'analyse structurée.

    C'est la fonction publique du module, la seule que main.py appellera.
    Le flux : slides (bytes) -> messages formatés -> appel API -> JSON -> DeckAnalysis.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MISTRAL_API_KEY absente. Vérifie ton fichier .env à la racine du projet."
        )

    client = Mistral(api_key=api_key)
    messages = _build_messages(slides)

    # Appel à l'API Mistral vision
    response = client.chat.complete(
        model=MODEL_NAME,
        messages=messages,
    )

    # Le contenu de la réponse est dans le premier choix
    raw_text = response.choices[0].message.content

    # Parse le JSON renvoyé par Mistral en objet DeckAnalysis
    # Si le JSON est invalide ou incomplet, Pydantic lève une erreur claire
    data = json.loads(raw_text)
    analysis = DeckAnalysis(**data)

    return analysis
