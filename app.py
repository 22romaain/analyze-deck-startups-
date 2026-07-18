"""Interface Streamlit pour l'analyseur de deck startup."""

import tempfile
import os

import streamlit as st

from src.ingestion import load_deck
from src.extraction import analyze_deck
from src.analysis import run_analysis
from src.main import _load_doctrine_retriever
from src.models import DIMENSION_LABELS, ROUND_OPTIONS, check_round_coherence
from src.output.memo_data import build_memo_data, load_memo_config
from src.output.render_docx import render_docx_bytes
from src.output.render_markdown import render_markdown
from src.review import make_review_generator


# --- Configuration de la page ---
st.set_page_config(page_title="Analyseur de Deck", layout="centered")

st.title("Analyseur de Deck Startup")
st.caption("Analyse un pitch deck selon les grandes dimensions VC.")

# --- Upload du PDF ---
uploaded_file = st.file_uploader("Charge un pitch deck (PDF)", type=["pdf"])

if uploaded_file is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(uploaded_file.read())
    tmp.close()

    # Charger les slides
    slides = load_deck(tmp.name)
    pdf_path = tmp.name

    # --- Aperçu : première slide uniquement ---
    st.subheader(f"{len(slides)} slides détectées")
    st.image(slides[0], caption="Slide 1 (couverture)", width=350)

    # --- Lancement de l'analyse ---
    if st.button("Lancer l'analyse"):
        with st.spinner("Analyse en cours via Mistral..."):
            analysis, signals, mode = analyze_deck(slides, pdf_path=pdf_path)

        # Nettoyage du fichier temporaire
        os.unlink(pdf_path)

        # Stocke l'analyse dans la session pour ne pas la perdre au rechargement
        st.session_state["analysis"] = analysis
        st.session_state["signals"] = signals
        st.session_state["mode"] = mode

# --- Affichage des résultats (persiste après le clic) ---
if "analysis" in st.session_state:
    analysis = st.session_state["analysis"]
    signals = st.session_state["signals"]
    mode = st.session_state["mode"]

    st.divider()
    st.caption(f"Mode utilisé : {mode}")

    # --- Confirmation du round ---
    st.subheader("Round de financement")

    # Dropdown pré-rempli avec la suggestion du LLM
    detected = analysis.detected_round.lower().strip()
    default_index = ROUND_OPTIONS.index(detected) if detected in ROUND_OPTIONS else 0

    confirmed_round = st.selectbox(
        "Round détecté (confirme ou corrige) :",
        options=ROUND_OPTIONS,
        index=default_index,
    )

    # Contrôle croisé montant / round
    coherence_alert = check_round_coherence(confirmed_round, analysis.ask_amount)
    if coherence_alert:
        st.warning(f"Incohérence détectée : {coherence_alert}")
    else:
        if analysis.ask_amount and "non mentionné" not in analysis.ask_amount.lower():
            st.success(f"Montant ({analysis.ask_amount}) cohérent avec un {confirmed_round}.")

    # --- Scoring déterministe (étape 2), recalculé sur le round confirmé ---
    # On passe ask_amount : nécessaire à l'alerte de dilution (cap table).
    result = run_analysis(signals, confirmed_round, analysis.ask_amount)

    st.subheader("Score d'investissement")
    st.metric("Score global (pondéré par le round)", f"{result.global_score:.0f} / 100")
    st.caption("Score déterministe : calculé par du code à partir des signaux extraits, pas par le LLM.")

    # Red flags, triés du plus grave au moins grave.
    st.subheader("Red flags")
    if not result.red_flags:
        st.success("Aucun red flag déclenché par les signaux disponibles.")
    else:
        severity_order = {"CRITIQUE": 0, "MAJEUR": 1, "MINEUR": 2}
        for flag in sorted(result.red_flags, key=lambda f: severity_order[f.severity]):
            label = DIMENSION_LABELS.get(flag.dimension, flag.dimension)
            line = f"**[{flag.severity}]** ({label}) {flag.message}"
            if flag.severity == "CRITIQUE":
                st.error(line)
            elif flag.severity == "MAJEUR":
                st.warning(line)
            else:
                st.info(line)

    # Score par dimension : barre de progression + poids dans le round + trace du calcul.
    st.subheader("Détail par dimension")
    for ds in result.dimension_scores:
        weight_txt = f"poids {ds.weight * 100:.0f}%" if ds.weight > 0 else "hors pondération"
        st.markdown(f"**{ds.label}** — {ds.score:.0f}/100 ({weight_txt})")
        st.progress(ds.score / 100)
        with st.expander("Comment ce score est calculé"):
            for line in ds.rationale:
                st.write(line)

    # --- Analyse narrative (le mémo texte du LLM) ---
    st.subheader("Analyse détaillée (narratif)")

    data = analysis.model_dump()
    for key, label in DIMENSION_LABELS.items():
        with st.expander(label):
            st.write(data[key])

    # --- Mémo d'investissement : génération + téléchargements ---
    st.divider()
    st.subheader("Mémo d'investissement")
    st.caption("Assemble le mémo VC complet (verdict, dimensions, red flags, doctrine).")

    if st.button("Générer le mémo VC"):
        config = load_memo_config()
        retriever, doctrine_msg = _load_doctrine_retriever()
        review_gen = make_review_generator()
        with st.spinner("Construction du mémo (dont contre-analyse LLM)..."):
            review = review_gen(analysis, result) if review_gen else None
            memo = build_memo_data(analysis, result, signals, config, review=review, retriever=retriever)
            st.session_state["memo_md"] = render_markdown(memo)
            st.session_state["memo_docx"] = render_docx_bytes(memo)
            st.session_state["memo_societe"] = memo.societe
        st.caption(doctrine_msg)

    if "memo_md" in st.session_state:
        societe = st.session_state["memo_societe"].replace(" ", "_")
        col_md, col_docx = st.columns(2)
        col_md.download_button(
            "Télécharger le mémo (.md)", st.session_state["memo_md"],
            file_name=f"memo_{societe}.md", mime="text/markdown",
        )
        col_docx.download_button(
            "Télécharger le mémo (.docx)", st.session_state["memo_docx"],
            file_name=f"memo_{societe}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        with st.expander("Aperçu du mémo"):
            st.markdown(st.session_state["memo_md"])
