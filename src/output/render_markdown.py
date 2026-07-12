"""Rendu Markdown du mémo : mise en forme pure, aucun calcul.

Toute donnée affichée vient de `MemoData` (produit par memo_data.build_memo_data).
Ce module ne trie, ne compare, ne décide rien : il met en page. Analogie : c'est
la mise en page d'impression d'un modèle déjà calculé, pas une formule de la feuille.

Tranche 3 : sections 0 (verdict), 1 (recommandation), 2 (tableau de bord).
Les sections 3 à 8 seront ajoutées aux tranches suivantes.
"""

from src.output.memo_data import MemoData, Reason

# Libellés lisibles des statuts du tableau de bord. Pur affichage (pas une décision :
# le statut est déjà calculé en amont), on ne fait que traduire l'énum en français.
STATUT_LABELS: dict[str, str] = {
    "TOP_QUARTILE": "Top quartile",
    "DANS_LA_NORME": "Dans la norme",
    "SOUS_LA_BARRE": "Sous la barre",
    "ABSENT": "Absent",
    "NON_EVALUABLE": "Non évaluable",
}

# Valeur affichée quand une cellule est vide (None), pour garder le tableau lisible.
VIDE = "—"


def _render_header(memo: MemoData) -> list[str]:
    """En-tête : société, round, montant, date."""
    return [
        f"# Mémo d'investissement — {memo.societe}",
        "",
        f"- **Round** : {memo.round}",
        f"- **Montant recherché** : {memo.ask_amount}",
        f"- **Date** : {memo.date.isoformat()}",
    ]


def _render_verdict(memo: MemoData) -> list[str]:
    """Section 0 : le verdict et sa justification auditable."""
    v = memo.verdict
    return [
        f"## Verdict : {v.decision}",
        "",
        v.justification,
        "",
        f"- Score global : **{v.score_global:.0f}/100**",
        f"- Red flags : {v.nb_critiques} critique(s), {v.nb_majeurs} majeur(s)",
    ]


def _render_reason(reason: Reason) -> str:
    """Une force ou une faiblesse en une ligne de liste."""
    return f"- **{reason.label}** — {reason.score:.0f}/100 : {reason.preuve}"


def _render_recommandation(memo: MemoData) -> list[str]:
    """Section 1 : 3 forces, 3 faiblesses, la question décisive."""
    lines = ["## Recommandation", "", "### Forces"]
    lines += [_render_reason(r) for r in memo.forces] or ["_Aucune force identifiée._"]
    lines += ["", "### Faiblesses"]
    lines += [_render_reason(r) for r in memo.faiblesses] or ["_Aucune faiblesse identifiée._"]
    lines += ["", "### Question décisive", memo.question_decisive.question]
    return lines


def _render_dashboard(memo: MemoData) -> list[str]:
    """Section 2 : tableau de bord (métrique, valeur, statut, benchmark)."""
    lines = [
        "## Tableau de bord",
        "",
        "| Métrique | Valeur | Statut | Benchmark |",
        "| --- | --- | --- | --- |",
    ]
    for row in memo.dashboard:
        valeur = row.valeur if row.valeur is not None else VIDE
        benchmark = row.benchmark if row.benchmark is not None else VIDE
        statut = STATUT_LABELS[row.statut]
        lines.append(f"| {row.metrique} | {valeur} | {statut} | {benchmark} |")
    return lines


def _render_dimensions(memo: MemoData) -> list[str]:
    """Section 3 : analyse par dimension (score, grade, poids, règles, red flags inline)."""
    lines = ["## Analyse par dimension"]
    if not memo.dimensions:
        lines.append("")
        lines.append("_Aucune dimension notée pour ce round._")
        return lines
    for d in memo.dimensions:
        lines += ["", f"### {d.label} — {d.score:.0f}/100 (grade {d.grade}, poids {d.weight:.0%})"]
        lines += ["", "Règles appliquées :"]
        lines += [f"- {regle}" for regle in d.regle_appliquee]
        if d.red_flags_inline:
            lines += ["", "Red flags :"]
            lines += [f"- [{r.severity}] {r.message}" for r in d.red_flags_inline]
    return lines


def _render_red_flags(memo: MemoData) -> list[str]:
    """Section 4 : tableau des red flags + sous-section incohérences internes."""
    lines = ["## Red flags", ""]
    if memo.red_flags:
        lines += ["| Sévérité | Dimension | Message |", "| --- | --- | --- |"]
        lines += [f"| {r.severity} | {r.label_dimension} | {r.message} |" for r in memo.red_flags]
    else:
        lines.append("_Aucun red flag détecté._")
    lines += ["", "### Incohérences internes"]
    if memo.incoherences:
        lines += [f"- [{r.severity}] {r.label_dimension} : {r.message}" for r in memo.incoherences]
    else:
        lines.append("_Aucune incohérence interne détectée._")
    return lines


def _render_missing_data(memo: MemoData) -> list[str]:
    """Section 5 : données attendues au stade et absentes du deck."""
    lines = ["## Données manquantes", ""]
    if memo.donnees_manquantes:
        lines += [f"- **{m.label}** ({m.criticite}) : {m.justification}" for m in memo.donnees_manquantes]
    else:
        lines.append("_Aucune donnée attendue manquante._")
    return lines


def render_markdown(memo: MemoData) -> str:
    """Assemble le mémo en Markdown (sections 0 à 5 pour l'instant).

    Les sections sont séparées par une ligne vide. Le document se termine par un
    retour à la ligne unique (convention fichier texte).
    """
    blocks = [
        _render_header(memo),
        _render_verdict(memo),
        _render_recommandation(memo),
        _render_dashboard(memo),
        _render_dimensions(memo),
        _render_red_flags(memo),
        _render_missing_data(memo),
    ]
    lines: list[str] = []
    for i, block in enumerate(blocks):
        lines += block
        if i < len(blocks) - 1:
            lines.append("")  # ligne vide entre sections
    return "\n".join(lines) + "\n"
