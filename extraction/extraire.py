from extraction.lecture import lire_deck
from extraction.remplissage import remplir_fiche


def extraire(client, chemin):
    slides = lire_deck(client, chemin)
    return remplir_fiche(client, slides)
