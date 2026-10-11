import logging
import sys
from pathlib import Path

from analyse.analyse import analyser
from client import client
from extraction.extraire import extraire
from restitution.restitution import en_pdf, restituer

logging.basicConfig(level=logging.INFO)
deck = Path(sys.argv[1])
fiche = extraire(client, deck)
texte = restituer(analyser(client, fiche))
Path("output").mkdir(exist_ok=True)
Path(f"output/{deck.stem}.json").write_text(fiche.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
Path(f"output/{deck.stem}.md").write_text(texte, encoding="utf-8")
if "--pdf" in sys.argv:
    en_pdf(texte, f"output/{deck.stem}.pdf")
print(f"Mémo écrit dans output/{deck.stem}.md")
