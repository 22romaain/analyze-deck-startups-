"""Rendu Word (.docx) du mémo : mise en forme pure, aucun calcul.

Le docx n'est PAS une conversion du Markdown : il lit le même MemoData via l'API
python-docx. Analogie : deux mises en page d'impression différentes du même modèle.

Choix python-docx (vs docxtpl) : contenu dynamique et déjà structuré, on pose la
mise en forme en code sans maintenir un template Word en parallèle.
"""

import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from src.output.memo_data import MemoData
from src.output.render_markdown import STATUT_LABELS, VIDE

# Dossier de sortie par défaut : output/ à la racine (rendu ignoré par git).
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def _add_table(document: Document, headers: list[str], rows: list[list[str]]) -> Table:
    """Ajoute un tableau Word natif (ligne d'en-tête + lignes de données)."""
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, headers):
        cell.text = text
    for row in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = str(text)
    return table


def _shade_paragraph(paragraph: Paragraph, fill: str) -> None:
    """Grise le fond d'un paragraphe (w:shd), pour l'encadré de la contre-analyse."""
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    paragraph._p.get_or_add_pPr().append(shd)


def _docx_header(doc: Document, memo: MemoData) -> None:
    doc.add_heading(f"Mémo d'investissement — {memo.societe}", level=0)
    doc.add_paragraph(f"Round : {memo.round}")
    doc.add_paragraph(f"Montant recherché : {memo.ask_amount}")
    doc.add_paragraph(f"Date : {memo.date.isoformat()}")


def _docx_verdict(doc: Document, memo: MemoData) -> None:
    v = memo.verdict
    doc.add_heading(f"Verdict : {v.decision}", level=1)
    doc.add_paragraph(v.justification)
    doc.add_paragraph(f"Score global : {v.score_global:.0f}/100")
    doc.add_paragraph(f"Red flags : {v.nb_critiques} critique(s), {v.nb_majeurs} majeur(s)")


def _docx_recommandation(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Recommandation", level=1)
    doc.add_heading("Forces", level=2)
    for r in memo.forces:
        doc.add_paragraph(f"{r.label} — {r.score:.0f}/100 : {r.preuve}", style="List Bullet")
    doc.add_heading("Faiblesses", level=2)
    for r in memo.faiblesses:
        doc.add_paragraph(f"{r.label} — {r.score:.0f}/100 : {r.preuve}", style="List Bullet")
    doc.add_heading("Question décisive", level=2)
    doc.add_paragraph(memo.question_decisive.question)


def _docx_dashboard(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Tableau de bord", level=1)
    rows = [
        [row.metrique, row.valeur or VIDE, STATUT_LABELS[row.statut], row.benchmark or VIDE]
        for row in memo.dashboard
    ]
    _add_table(doc, ["Métrique", "Valeur", "Statut", "Benchmark"], rows)


def _docx_dimensions(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Analyse par dimension", level=1)
    for d in memo.dimensions:
        doc.add_heading(f"{d.label} — {d.score:.0f}/100 (grade {d.grade}, poids {d.weight:.0%})", level=2)
        doc.add_paragraph("Règles appliquées :")
        for regle in d.regle_appliquee:
            doc.add_paragraph(regle, style="List Bullet")
        if d.red_flags_inline:
            doc.add_paragraph("Red flags :")
            for r in d.red_flags_inline:
                doc.add_paragraph(f"[{r.severity}] {r.message}", style="List Bullet")


def _docx_red_flags(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Red flags", level=1)
    if memo.red_flags:
        rows = [[r.severity, r.label_dimension, r.message] for r in memo.red_flags]
        _add_table(doc, ["Sévérité", "Dimension", "Message"], rows)
    else:
        doc.add_paragraph("Aucun red flag détecté.")
    doc.add_heading("Incohérences internes", level=2)
    if memo.incoherences:
        for r in memo.incoherences:
            doc.add_paragraph(f"[{r.severity}] {r.label_dimension} : {r.message}", style="List Bullet")
    else:
        doc.add_paragraph("Aucune incohérence interne détectée.")


def _docx_missing_data(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Données manquantes", level=1)
    if memo.donnees_manquantes:
        for m in memo.donnees_manquantes:
            doc.add_paragraph(f"{m.label} ({m.criticite}) : {m.justification}", style="List Bullet")
    else:
        doc.add_paragraph("Aucune donnée attendue manquante.")


def _docx_review(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Contre-analyse", level=1)
    encart = doc.add_paragraph(memo.contre_analyse.bandeau)
    _shade_paragraph(encart, "D9D9D9")  # gris clair, distinct du texte courant
    if memo.contre_analyse.disponible and memo.contre_analyse.contenu:
        doc.add_paragraph(memo.contre_analyse.contenu)


def _docx_founder_questions(doc: Document, memo: MemoData) -> None:
    doc.add_heading("Questions aux fondateurs", level=1)
    if not memo.questions_fondateurs:
        doc.add_paragraph("Aucune question générée.")
        return
    for i, q in enumerate(memo.questions_fondateurs, start=1):
        doc.add_paragraph(f"{i}. {q.question}")
        if q.bonne_reponse:
            doc.add_paragraph(f"Bonne réponse : {q.bonne_reponse}", style="List Bullet")
        if q.mauvaise_reponse:
            doc.add_paragraph(f"Mauvaise réponse : {q.mauvaise_reponse}", style="List Bullet")


def _docx_annexes(doc: Document, memo: MemoData) -> None:
    a = memo.annexes
    doc.add_heading("Annexes", level=1)
    doc.add_heading("Méthodologie", level=2)
    doc.add_paragraph(a.methodologie)
    doc.add_heading("Limites", level=2)
    doc.add_paragraph(a.limites)
    doc.add_heading("Extraction brute", level=2)
    for key, value in a.extraction_brute.items():
        doc.add_paragraph(f"{key} : {value}", style="List Bullet")


def _slugify(name: str) -> str:
    """Nom de fichier sûr : lettres/chiffres, le reste devient '_'."""
    slug = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_")
    return slug or "societe"


def _output_path(memo: MemoData, output_dir: Path | None) -> Path:
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"memo_{_slugify(memo.societe)}_{memo.date.isoformat()}.docx"


def render_docx(memo: MemoData, output_dir: Path | None = None) -> Path:
    """Écrit le mémo complet en .docx et retourne le chemin du fichier.

    Aucun calcul : chaque section lit MemoData. Lève une erreur claire si
    l'écriture échoue (droits, disque).
    """
    doc = Document()
    _docx_header(doc, memo)
    _docx_verdict(doc, memo)
    _docx_recommandation(doc, memo)
    _docx_dashboard(doc, memo)
    _docx_dimensions(doc, memo)
    _docx_red_flags(doc, memo)
    _docx_missing_data(doc, memo)
    _docx_review(doc, memo)
    _docx_founder_questions(doc, memo)
    _docx_annexes(doc, memo)

    path = _output_path(memo, output_dir)
    try:
        doc.save(str(path))
    except OSError as exc:
        raise RuntimeError(f"Écriture du mémo Word impossible ({path}) : {exc}") from exc
    return path
