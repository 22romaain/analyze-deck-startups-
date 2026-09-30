import os

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.utils import BackoffStrategy, RetryConfig

from extraction.lecture import lire_deck
from extraction.remplissage import remplir_fiche

RELANCE = RetryConfig("backoff", BackoffStrategy(1000, 60000, 1.5, 300000), False)


def extraire(chemin):
    load_dotenv()
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"), retry_config=RELANCE)
    slides = lire_deck(client, chemin)
    return remplir_fiche(client, slides)


if __name__ == "__main__":
    fiche = extraire("decks/test_image_random.pdf")
    print(fiche.model_dump_json(indent=2))
