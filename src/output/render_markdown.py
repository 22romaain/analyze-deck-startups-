"""Rendu Markdown du mémo : mise en forme pure, aucun calcul.

Toute donnée affichée vient de `MemoData` (produit par memo_data.build_memo_data).
Ce module ne trie, ne compare, ne décide rien : il met en page. Analogie : c'est
la mise en page d'impression d'un modèle déjà calculé, pas une formule de la feuille.

Tranche 3 : sections 0 (verdict), 1 (recommandation), 2 (tableau de bord).
Les sections 3 à 8 seront ajoutées aux tranches suivantes.
"""

import re
from pathlib import Path

from src.output.memo_data import MemoData, Reason

# Dossier de sortie par défaut : output/ à la racine (rendu ignoré par git).
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"

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
        # Doctrine issue des cours perso (RAG) : ne s'affiche que si une citation existe,
        # donc un mémo sans doctrine reste rendu à l'identique (golden inchangé).
        if d.doctrine:
            lines += ["", "Doctrine VC :"]
            lines += [f"- ({c.source}, §{c.section}) {c.extrait}" for c in d.doctrine]
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


def _render_review(memo: MemoData) -> list[str]:
    """Section 6 : contre-analyse. Encart distinct (blockquote), mode dégradé géré."""
    r = memo.contre_analyse
    lines = ["## Contre-analyse", "", f"> {r.bandeau}"]
    if r.disponible and r.contenu:
        lines += ["", r.contenu]
    return lines


def _render_founder_questions(memo: MemoData) -> list[str]:
    """Section 7 : questions aux fondateurs (liste numérotée)."""
    lines = ["## Questions aux fondateurs", ""]
    if not memo.questions_fondateurs:
        lines.append("_Aucune question générée._")
        return lines
    for i, q in enumerate(memo.questions_fondateurs, start=1):
        lines.append(f"{i}. {q.question}")
        if q.bonne_reponse:
            lines.append(f"   - Bonne réponse : {q.bonne_reponse}")
        if q.mauvaise_reponse:
            lines.append(f"   - Mauvaise réponse : {q.mauvaise_reponse}")
    return lines


def _render_annexes(memo: MemoData) -> list[str]:
    """Section 8 : méthodologie, limites, extraction brute."""
    a = memo.annexes
    lines = ["## Annexes", "", "### Méthodologie", a.methodologie,
             "", "### Limites", a.limites, "", "### Extraction brute"]
    for key, value in a.extraction_brute.items():
        lines.append(f"- **{key}** : {value}")
    return lines


def render_markdown(memo: MemoData) -> str:
    """Assemble le mémo complet en Markdown (sections 0 à 8).

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
        _render_review(memo),
        _render_founder_questions(memo),
        _render_annexes(memo),
    ]
    lines: list[str] = []
    for i, block in enumerate(blocks):
        lines += block
        if i < len(blocks) - 1:
            lines.append("")  # ligne vide entre sections
    return "\n".join(lines) + "\n"


def _slugify(name: str) -> str:
    """Nom de fichier sûr : lettres/chiffres, le reste devient '_'."""
    slug = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_")
    return slug or "societe"


def output_path(memo: MemoData, extension: str, output_dir: Path | None = None) -> Path:
    """Chemin de sortie partagé par les deux renderers : memo_{societe}_{date}.{ext}."""
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"memo_{_slugify(memo.societe)}_{memo.date.isoformat()}.{extension}"


def write_markdown(memo: MemoData, output_dir: Path | None = None) -> Path:
    """Écrit le mémo Markdown sur disque et retourne le chemin. Erreur claire si échec."""
    path = output_path(memo, "md", output_dir)
    try:
        path.write_text(render_markdown(memo), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Écriture du mémo Markdown impossible ({path}) : {exc}") from exc
    return path
