import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.utils import BackoffStrategy, RetryConfig

from analyse.analyse import analyser
from extraction.extraire import extraire
from restitution.restitution import en_pdf, restituer

RELANCE = RetryConfig("backoff", BackoffStrategy(1000, 60000, 1.5, 300000), False)

logging.basicConfig(level=logging.INFO)
load_dotenv()
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"), retry_config=RELANCE)
deck = Path(sys.argv[1])
fiche = extraire(client, deck)
texte = restituer(fiche, analyser(client, fiche))
Path("output").mkdir(exist_ok=True)
Path(f"output/{deck.stem}.md").write_text(texte, encoding="utf-8")
if "--pdf" in sys.argv:
    en_pdf(texte, f"output/{deck.stem}.pdf")
print(f"Mémo écrit dans output/{deck.stem}.md")
