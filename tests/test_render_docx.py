"""Tests du rendu Word (tranche 6). Pas de comparaison binaire : on relit le .docx
avec python-docx et on vérifie sa structure (tableaux, bandeau §6, encadré grisé)."""

from docx import Document
from docx.oxml.ns import qn

from src.output.render_docx import render_docx
from tests.test_render_markdown import make_memo


def test_render_docx_cree_fichier_et_structure(tmp_path):
    memo = make_memo()
    path = render_docx(memo, output_dir=tmp_path)

    assert path.exists()
    assert path.name == "memo_Acme_SaaS_2026-07-12.docx"

    doc = Document(str(path))
    # Deux tableaux natifs : tableau de bord (§2) et red flags (§4).
    assert len(doc.tables) == 2
    textes = "\n".join(p.text for p in doc.paragraphs)
    assert "Contre-analyse indisponible (erreur API)." in textes  # bandeau §6
    assert "Verdict : APPROFONDIR" in textes


def test_render_docx_encadre_contre_analyse_grise(tmp_path):
    path = render_docx(make_memo(), output_dir=tmp_path)
    doc = Document(str(path))
    bandeau = next(p for p in doc.paragraphs if "Contre-analyse indisponible" in p.text)
    pPr = bandeau._p.pPr
    assert pPr is not None and pPr.find(qn("w:shd")) is not None  # fond grisé posé
