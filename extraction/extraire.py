import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from extraction.lecture import lire_deck
from extraction.remplissage import remplir_fiche


def extraire(chemin):
    load_dotenv()
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    slides = lire_deck(client, chemin)
    return remplir_fiche(client, slides)


if __name__ == "__main__":
    for slide in extraire("decks/test_image_random.pdf"):
        print(slide)
