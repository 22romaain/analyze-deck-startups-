"""Rendu PDF du mémo, via reportlab. Quatrième format du même agrégat MemoData.

Comme le rendu Word, ce module part du Markdown déjà construit plutôt que de relire
MemoData section par section : une seule source de vérité pour l'ordre et le contenu.
Il fait un pas de plus que le .docx en traduisant les niveaux de titre et les listes
en vrais styles, parce qu'un PDF est le format qu'on envoie à un tiers.

Limite assumée : les tableaux (tableau de bord, red flags) sortent en lignes de texte
séparées par des barres verticales, pas en tableaux mis en forme.

Police : Vera, livrée avec reportlab. Les polices PDF de base ne gèrent que le
latin-1 et perdraient les tirets cadratins du mémo.
"""

import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.output.memo_data import MemoData
from src.output.render_docx import is_table_separator
from src.output.render_markdown import output_path, render_markdown

FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
REGULAR, BOLD = "Vera", "Vera-Bold"

# Caractères absents de Vera, remplacés par un équivalent lisible. On ne corrige que
# le PDF : le mémo Markdown garde sa flèche, qui s'affiche partout ailleurs.
SUBSTITUTIONS = {"→": "->"}


def _register_fonts() -> None:
    """Déclare Vera et sa graisse grasse, et les relie pour que <b> fonctionne."""
    if REGULAR in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont(REGULAR, str(FONT_DIR / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont(BOLD, str(FONT_DIR / "VeraBd.ttf")))
    addMapping(REGULAR, 0, 0, REGULAR)  # normal
    addMapping(REGULAR, 1, 0, BOLD)     # gras


def _to_markup(text: str) -> str:
    """Passe une ligne de Markdown en balisage reportlab.

    L'échappement vient en premier : reportlab lit un mini-HTML, donc un '&' ou un
    '<' venant du deck casserait le rendu s'il n'était pas neutralisé avant.
    """
    for source, target in SUBSTITUTIONS.items():
        text = text.replace(source, target)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(text))


def _styles():
    """Feuille de styles reportlab, repolicée en Vera (titres en gras)."""
    sheet = getSampleStyleSheet()
    for name in ("Title", "Heading1", "Heading2", "Heading3"):
        sheet[name].fontName = BOLD
    for name in ("BodyText", "Bullet"):
        sheet[name].fontName = REGULAR
    return sheet


def _flowables(memo: MemoData) -> list:
    """Traduit le mémo Markdown en éléments de mise en page reportlab.

    Le préfixe de chaque ligne décide de son style : '#' un titre, '- ' une puce,
    le reste un paragraphe. Les séparateurs de tableau markdown n'ont pas de sens
    hors markdown et sont sautés, comme dans le rendu Word.
    """
    sheet = _styles()
    prefixes = [("### ", "Heading3"), ("## ", "Heading2"), ("# ", "Title")]
    flow: list = []
    for line in render_markdown(memo).splitlines():
        if is_table_separator(line):
            continue
        stripped = line.strip()
        if not stripped:
            flow.append(Spacer(1, 4))
            continue
        for prefix, style in prefixes:
            if stripped.startswith(prefix):
                flow.append(Paragraph(_to_markup(stripped[len(prefix):]), sheet[style]))
                break
        else:
            if stripped.startswith("- "):
                flow.append(Paragraph(_to_markup(stripped[2:]), sheet["Bullet"], bulletText="•"))
            else:
                flow.append(Paragraph(_to_markup(stripped), sheet["BodyText"]))
    return flow


def _build(memo: MemoData, target) -> None:
    """Écrit le PDF dans une cible (chemin ou tampon mémoire). Pagination automatique."""
    _register_fonts()
    doc = SimpleDocTemplate(
        target, pagesize=A4, title=f"Mémo d'investissement : {memo.societe}",
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    doc.build(_flowables(memo))


def render_pdf_bytes(memo: MemoData) -> bytes:
    """Rend le mémo PDF en octets (fichier en mémoire), pour un téléchargement direct."""
    buffer = BytesIO()
    _build(memo, buffer)
    return buffer.getvalue()


def render_pdf(memo: MemoData, output_dir: Path | None = None) -> Path:
    """Écrit le mémo en .pdf et retourne le chemin. Erreur claire si l'écriture échoue."""
    path = output_path(memo, "pdf", output_dir)
    try:
        _build(memo, str(path))
    except OSError as exc:
        raise RuntimeError(f"Écriture du mémo PDF impossible ({path}) : {exc}") from exc
    return path
