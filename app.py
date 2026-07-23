"""Interface Streamlit pour l'analyseur de deck startup."""

import tempfile
import os

import streamlit as st

from src.ingestion import load_deck
from src.extraction import analyze_deck
from src.analysis import run_analysis
from src.main import _load_doctrine_retriever
from src.models import ROUND_OPTIONS, check_round_coherence
from src.output.memo_data import build_memo_data, load_memo_config
from src.output.render_docx import render_docx_bytes
from src.output.render_markdown import render_markdown
from src.output.render_pdf import render_pdf_bytes
from src.output.render_streamlit import render_memo
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

        # Un nouveau deck périme les mémos du précédent : sans ce nettoyage, on
        # afficherait le mémo de l'ancienne société sous le nom de la nouvelle.
        for key in [k for k in st.session_state if k.startswith(("memo_", "doctrine_"))]:
            del st.session_state[key]

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

    # --- Mémo : construit une fois par round, puis mémorisé dans la session ---
    # Streamlit relance TOUT le script à chaque interaction avec un widget. Sans cette
    # mémoire, le simple fait de dérouler le menu des rounds relancerait la contre-analyse
    # LLM et les requêtes RAG, alors que le tier gratuit Mistral plafonne à 2 requêtes
    # par minute. La clé porte le round : corriger le round reconstruit, revenir dessus
    # ressort la version déjà calculée.
    memo_key = f"memo_{confirmed_round}"
    if memo_key not in st.session_state:
        retriever, doctrine_msg = _load_doctrine_retriever()
        review_generator = make_review_generator()
        with st.spinner("Construction du mémo (doctrine et contre-analyse)..."):
            review = review_generator(analysis, result) if review_generator else None
            st.session_state[memo_key] = build_memo_data(
                analysis, result, signals, load_memo_config(),
                review=review, retriever=retriever,
            )
        st.session_state[f"doctrine_{confirmed_round}"] = doctrine_msg

    memo = st.session_state[memo_key]

    # --- Le mémo complet : la vue principale, pas un sous-produit ---
    st.divider()
    render_memo(memo)

    # --- Exports, en bas de page une fois le mémo lu ---
    st.divider()
    st.subheader("Exporter le mémo")
    societe = memo.societe.replace(" ", "_")
    col_pdf, col_docx, col_md = st.columns(3)
    col_pdf.download_button(
        "PDF (.pdf)", render_pdf_bytes(memo),
        file_name=f"memo_{societe}.pdf", mime="application/pdf", width="stretch",
    )
    col_docx.download_button(
        "Word (.docx)", render_docx_bytes(memo),
        file_name=f"memo_{societe}.docx", width="stretch",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    col_md.download_button(
        "Markdown (.md)", render_markdown(memo),
        file_name=f"memo_{societe}.md", mime="text/markdown", width="stretch",
    )
    st.caption(st.session_state.get(f"doctrine_{confirmed_round}", ""))

    # --- Note de bas de page : la méthode qualitative et le cadre assumé ---
    st.divider()
    st.caption(
        "**Méthode : une analyse, pas une note.** L'outil ne met plus de score sur 100. "
        "Il produit des constats tagués (rédhibitoire, faiblesse, point de vigilance, "
        "atout d'équipe, avantage compétitif, à creuser) et une recommandation qui en "
        "découle. Un rédhibitoire renvoie à approfondir et à justifier, jamais à un rejet "
        "automatique : c'est l'analyste qui tranche, pas la machine."
    )
    # On assume le cadre subjectif plutôt que de le maquiller en objectivité de marché.
    st.caption(
        "**Critères éditables et cadre assumé.** Les critères d'analyse vivent dans "
        "config/criteres.yaml et se modifient à la main, sans toucher au code. L'analyse "
        "reflète les critères et la thèse d'investissement subjectifs du créateur de "
        "l'app, en complément des grands principes VC du référentiel (dossier courses/). "
        "Ce n'est pas une vérité de marché."
    )
