"""Tests du rendu PDF. On relit le PDF produit et on vérifie son contenu texte.

Pas de comparaison binaire : deux PDF du même contenu diffèrent octet à octet
(date de création, ordre interne). On teste ce qui est lisible, pas le fichier.
"""

import fitz  # PyMuPDF, déjà utilisé par l'ingestion

from src.output.render_pdf import render_pdf, render_pdf_bytes
from tests.test_render_markdown import make_memo


def _texte_du_pdf(path) -> str:
    """Extrait tout le texte d'un PDF, pages concaténées."""
    doc = fitz.open(str(path))
    texte = "\n".join(page.get_text() for page in doc)
    doc.close()
    return texte


def test_render_pdf_bytes_est_un_pdf_valide():
    # Un PDF commence toujours par la signature "%PDF-".
    data = render_pdf_bytes(make_memo())
    assert isinstance(data, bytes) and data[:5] == b"%PDF-"


def test_render_pdf_cree_fichier_et_contenu(tmp_path):
    path = render_pdf(make_memo(), output_dir=tmp_path)

    assert path.exists()
    assert path.name == "memo_Acme_SaaS_2026-07-12.pdf"

    texte = _texte_du_pdf(path)
    assert "Recommandation : APPROFONDIR" in texte
    assert "indisponible" in texte  # bandeau de l'analyse LLM


def test_render_pdf_ne_laisse_pas_de_markdown_brut(tmp_path):
    """Les marqueurs de gras et les séparateurs de tableau sont traduits, pas recopiés."""
    texte = _texte_du_pdf(render_pdf(make_memo(), output_dir=tmp_path))
    assert "**" not in texte
    assert "| --- |" not in texte


def test_render_pdf_remplace_la_fleche_absente_de_la_police(tmp_path):
    """La police embarquée n'a pas de flèche : le PDF doit porter la substitution."""
    texte = _texte_du_pdf(render_pdf(make_memo(), output_dir=tmp_path))
    assert "→" not in texte
    assert "60% -> 45%" in texte  # ligne de dilution des fondateurs


def test_render_pdf_echappe_les_caracteres_de_balisage(tmp_path):
    """Un '&' ou un '<' venant du deck ne doit ni casser le rendu ni sortir échappé.

    reportlab lit un mini-HTML : sans neutralisation, ces caractères font échouer
    la composition de la page.
    """
    memo = make_memo()
    memo.societe = "Acme & Co <test>"
    texte = _texte_du_pdf(render_pdf(memo, output_dir=tmp_path))
    assert "Acme & Co <test>" in texte
    assert "&amp;" not in texte
