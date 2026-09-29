"""Rendu Streamlit du mémo qualitatif : mise en forme pure, aucun calcul.

Troisième renderer du même agrégat `MemoData`, aux côtés de render_markdown et
render_docx. Il ne trie pas, ne compare pas, ne décide rien : tout est arbitré en
amont. Sa valeur ajoutée sur le markdown est l'interactivité (bandeaux colorés,
expanders), qu'un fichier texte ne peut pas porter.
"""

import streamlit as st

from src.models import FINDING_CATEGORIES, Finding
from src.output.memo_data import MemoData
# Marqueur de cellule vide et format montant repris du rendu Markdown : pures
# traductions d'affichage, à ne pas redéfinir ici pour éviter deux vocabulaires.
from src.output.render_markdown import STATUT_GRILLE_LABELS, VIDE, fmt_m

# Traduction de la recommandation en bandeau coloré. Pas une décision : elle est déjà
# prise par build_synthese. On ne fait que donner une couleur à un mot existant.
RECO_BANNER = {"APPROFONDIR": st.warning, "POURSUIVRE": st.success}

# Pastille de couleur d'un constat selon sa catégorie, pour balayer des yeux.
CATEGORIE_PASTILLE = {
    "redhibitoire": "⛔", "faiblesse": "🟠", "vigilance": "🔵",
    "avantage_competitif": "🟢", "atout_equipe": "🟢", "a_creuser": "⚪",
}

# Pastille de statut de la grille d'attendus.
STATUT_PASTILLE_GRILLE = {"PRESENT": "🟢", "ABSENT": "🔴", "INCONNU": "⚪"}


def _finding_md(finding: Finding) -> str:
    """Un constat en une ligne markdown : pastille, catégorie lisible, message."""
    pastille = CATEGORIE_PASTILLE.get(finding.categorie, "•")
    label = FINDING_CATEGORIES[finding.categorie]["label"]
    return f"{pastille} **{label}** — {finding.message}"


def render_header(memo: MemoData) -> None:
    """En-tête : société, round, montant, date, puis le disclaimer."""
    st.header(f"Mémo d'investissement : {memo.societe}")
    col_round, col_ask, col_date = st.columns(3)
    col_round.metric("Round", memo.round)
    col_ask.metric("Montant recherché", memo.ask_amount)
    col_date.metric("Date", memo.date.isoformat())
    st.caption(memo.disclaimer)


def render_recommandation(memo: MemoData) -> None:
    """Section 1 : la recommandation qualitative en bandeau, sa justification, les compteurs."""
    reco = memo.synthese.recommandation
    st.subheader(f"Recommandation : {reco.decision}")
    banner = RECO_BANNER.get(reco.decision, st.info)
    banner(reco.justification)
    col_red, col_faibles, col_atouts = st.columns(3)
    col_red.metric("Rédhibitoires", reco.nb_redhibitoires)
    col_faibles.metric("Faiblesses", reco.nb_faiblesses)
    col_atouts.metric("Atouts", reco.nb_atouts)


def render_synthese(memo: MemoData) -> None:
    """Section 2 : synthèse pros/cons, atouts et points négatifs côte à côte."""
    syn = memo.synthese
    st.subheader("Synthèse")
    col_pour, col_contre = st.columns(2)
    col_pour.markdown("**Atouts**")
    if not syn.atouts:
        col_pour.caption("Aucun atout relevé.")
    for f in syn.atouts:
        col_pour.markdown(_finding_md(f))
    col_contre.markdown("**Points négatifs**")
    if not syn.points_negatifs:
        col_contre.caption("Aucun point négatif relevé.")
    for f in syn.points_negatifs:
        col_contre.markdown(_finding_md(f))
    if syn.a_creuser:
        st.markdown("**À creuser**")
        for f in syn.a_creuser:
            st.markdown(_finding_md(f))


def render_grille(memo: MemoData) -> None:
    """Section 3 : grille d'attendus du round (présent / absent / inconnu)."""
    st.subheader("Grille d'attendus")
    if not memo.grille:
        st.caption("Aucun attendu défini pour ce round.")
        return
    st.dataframe(
        [
            {
                "Attendu": row.label,
                "Statut": f"{STATUT_PASTILLE_GRILLE[row.statut]} {STATUT_GRILLE_LABELS[row.statut]}",
                "Valeur": row.valeur if row.valeur is not None else VIDE,
                "Criticité": row.criticite,
            }
            for row in memo.grille
        ],
        hide_index=True,
        width="stretch",
    )


def render_deck_figures(memo: MemoData) -> None:
    """Section 'ce que le deck affirme' : tous les chiffres du deck, captés tels quels."""
    if not memo.chiffres_deck:
        return
    st.subheader("Ce que le deck affirme")
    st.caption("Inventaire brut, non jugé. Restitue les chiffres sans champ de notation.")
    st.dataframe(
        [
            {
                "Métrique": row.libelle,
                "Valeur": row.valeur,
                "Période": row.periode if row.periode else VIDE,
                "Source": f"slide {row.slide}" if row.slide is not None else VIDE,
            }
            for row in memo.chiffres_deck
        ],
        hide_index=True,
        width="stretch",
    )


def render_dimensions(memo: MemoData) -> None:
    """Section 4 : une dimension par bloc (récit du deck + constats), sans score.

    Les constats restent visibles hors du volet : une alerte qu'il faut déplier pour
    voir n'alerte personne. Le récit et la doctrine, plus longs, sont repliés.
    """
    st.subheader("Analyse par dimension")
    for dim in memo.dimensions:
        st.markdown(f"**{dim.label}**")
        for f in dim.findings:
            st.markdown(_finding_md(f))
        with st.expander("Voir le détail"):
            if dim.narratif:
                st.markdown("**Ce que dit le deck**")
                st.write(dim.narratif)
            if dim.doctrine:
                st.markdown("**Doctrine VC (tes cours)**")
                for citation in dim.doctrine:
                    st.caption(f"({citation.source}, §{citation.section}) {citation.extrait}")


def render_incoherences(memo: MemoData) -> None:
    """Section 5 : incohérences internes (chiffres qui se contredisent). Absente si aucune."""
    if not memo.incoherences:
        return
    st.subheader("Incohérences internes")
    for f in memo.incoherences:
        st.warning(f.message)


def render_review(memo: MemoData) -> None:
    """Section 6 : la lecture LLM au regard de la thèse, précédée de son bandeau."""
    review = memo.contre_analyse
    st.subheader("Analyse au regard de ta thèse")
    st.info(review.bandeau)
    if review.disponible and review.contenu:
        st.write(review.contenu)


def render_captable(memo: MemoData) -> None:
    """Section 7 : dilution du tour, et sortie au post-money quand les termes sont connus."""
    cap = memo.cap_table
    st.subheader("Cap table et dilution")
    if not cap.calculable:
        st.warning("Non calculable. Termes manquants ou incohérents : "
                   + ", ".join(cap.donnees_absentes))
        return
    dilution = cap.dilution
    col_pre, col_amount, col_post = st.columns(3)
    col_pre.metric("Pre-money", fmt_m(cap.pre_money))
    col_amount.metric("Montant levé", fmt_m(cap.amount))
    col_post.metric("Post-money", fmt_m(dilution.post_money))
    col_investor, col_founders = st.columns(2)
    col_investor.metric("Nouvel investisseur", f"{dilution.new_investor_pct:.0f}%")
    col_founders.metric(
        "Fondateurs après le tour", f"{dilution.founder_pct_post:.0f}%",
        delta=f"{-dilution.founder_dilution_points:.0f} pts",
    )
    if dilution.option_pool_pct > 0:
        st.caption(f"Option pool créé au tour : {dilution.option_pool_pct:.0f}%")
    if cap.waterfall is not None:
        water = cap.waterfall
        st.markdown("**Waterfall (sortie au post-money)**")
        st.write(
            f"À une sortie à {fmt_m(water.exit_value)}, les fondateurs touchent "
            f"**{water.founders_pct_of_exit:.0f}%** (~{fmt_m(water.founders_payout)})."
        )


def render_annexes(memo: MemoData) -> None:
    """Section 8 : méthodologie, limites, extraction brute. Repliée : c'est de l'audit."""
    annexes = memo.annexes
    with st.expander("Annexes (méthodologie, limites, extraction brute)"):
        st.markdown("**Méthodologie**")
        st.write(annexes.methodologie)
        st.markdown("**Limites**")
        st.write(annexes.limites)
        st.markdown("**Extraction brute**")
        st.json(annexes.extraction_brute)


def render_memo(memo: MemoData) -> None:
    """Assemble le mémo complet à l'écran, dans l'ordre du document.

    Point d'entrée unique du module : l'app appelle cette fonction et rien d'autre.
    """
    render_header(memo)
    st.divider()
    render_recommandation(memo)
    render_synthese(memo)
    render_grille(memo)
    render_deck_figures(memo)
    render_dimensions(memo)
    render_incoherences(memo)
    render_review(memo)
    render_captable(memo)
    render_annexes(memo)
