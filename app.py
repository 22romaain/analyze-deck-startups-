"""Interface Streamlit pour l'analyseur de deck startup."""

import streamlit as st

from src.ingestion import load_deck
from src.extraction import analyze_deck
from src.models import DIMENSION_LABELS


# --- Configuration de la page ---
st.set_page_config(page_title="Analyseur de Deck", layout="centered")

st.title("Analyseur de Deck Startup")
st.caption("Analyse un pitch deck selon les grandes dimensions VC.")

# --- Upload du PDF ---
uploaded_file = st.file_uploader("Charge un pitch deck (PDF)", type=["pdf"])

if uploaded_file is not None:
    # Sauvegarde temporaire du fichier uploadé pour que PyMuPDF puisse le lire
    import tempfile, os

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(uploaded_file.read())
    tmp.close()

    # Charger les slides
    slides = load_deck(tmp.name)
    pdf_path = tmp.name  # Gardé pour markitdown

    # --- Aperçu : première slide uniquement ---
    st.subheader(f"{len(slides)} slides détectées")
    st.image(slides[0], caption="Slide 1 (couverture)", width=350)

    # --- Lancement de l'analyse ---
    if st.button("Lancer l'analyse"):
        with st.spinner("Analyse en cours via Mistral..."):
            analysis, mode = analyze_deck(slides, pdf_path=pdf_path)

        # Nettoyage du fichier temporaire
        os.unlink(pdf_path)

        st.divider()
        st.caption(f"Mode utilisé : {mode}")
        st.subheader("Résultats de l'analyse")

        # Affiche chaque dimension dans un accordéon
        data = analysis.model_dump()
        for key, label in DIMENSION_LABELS.items():
            with st.expander(label):
                st.write(data[key])
