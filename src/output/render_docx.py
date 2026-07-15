"""Rendu Word (.docx) du mémo, volontairement brut : aucune mise en page.

Choix assumé : le docx n'est qu'un report du mémo en paragraphes de texte simple
(une ligne = un paragraphe), sans styles de titre, sans tableaux Word, sans
encadré. Une seule source : le texte Markdown déjà construit. Si un rendu plus
mis en forme redevient utile, on réintroduira des helpers par section.
"""

from pathlib import Path

from docx import Document

from src.output.memo_data import MemoData
from src.output.render_markdown import output_path, render_markdown


def _is_table_separator(line: str) -> bool:
    """Vrai pour une ligne de séparation de tableau markdown (ex: '| --- | --- |').

    Ces lignes n'ont pas de sens hors markdown : on les saute pour rester lisible.
    """
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= {"|", "-", " ", ":"} and "-" in stripped


def render_docx(memo: MemoData, output_dir: Path | None = None) -> Path:
    """Écrit le mémo en .docx brut (texte du Markdown en paragraphes) et retourne le chemin."""
    doc = Document()
    for line in render_markdown(memo).splitlines():
        if _is_table_separator(line):
            continue
        doc.add_paragraph(line)

    path = output_path(memo, "docx", output_dir)
    try:
        doc.save(str(path))
    except OSError as exc:
        raise RuntimeError(f"Écriture du mémo Word impossible ({path}) : {exc}") from exc
    return path
