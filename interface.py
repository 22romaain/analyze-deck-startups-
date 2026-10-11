from pathlib import Path

import streamlit as st

from analyse.analyse import analyser
from client import client
from extraction.extraire import extraire
from restitution.restitution import en_pdf, restituer

st.title("Analyse de pitch deck")
fichier = st.file_uploader("Deck au format PDF", type="pdf")
if fichier and st.button("Analyser"):
    deck = Path("decks") / fichier.name
    deck.parent.mkdir(exist_ok=True)
    deck.write_bytes(fichier.getvalue())
    with st.spinner("Analyse en cours…"):
        fiche = extraire(client, deck)
        texte = restituer(fiche, analyser(client, fiche))
    Path("output").mkdir(exist_ok=True)
    en_pdf(texte, f"output/{deck.stem}.pdf")
    st.download_button("Télécharger le PDF", Path(f"output/{deck.stem}.pdf").read_bytes(), f"{deck.stem}.pdf", on_click="ignore")
    st.markdown(texte)
