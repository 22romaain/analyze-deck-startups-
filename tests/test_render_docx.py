"""Tests du rendu Word brut. On relit le .docx et on vérifie le contenu texte,
pas de mise en page (plus de tableaux, plus d'encadré)."""

from docx import Document

from src.output.render_docx import render_docx
from tests.test_render_markdown import make_memo


def test_render_docx_cree_fichier_et_contenu(tmp_path):
    memo = make_memo()
    path = render_docx(memo, output_dir=tmp_path)

    assert path.exists()
    assert path.name == "memo_Acme_SaaS_2026-07-12.docx"

    doc = Document(str(path))
    assert len(doc.tables) == 0  # rendu brut : aucun tableau Word
    textes = "\n".join(p.text for p in doc.paragraphs)
    assert "Verdict : APPROFONDIR" in textes
    assert "Contre-analyse indisponible (erreur API)." in textes  # bandeau §6, en texte simple


def test_render_docx_saute_les_separateurs_de_tableau(tmp_path):
    # Les lignes '| --- | --- |' du markdown ne doivent pas apparaître dans le docx.
    path = render_docx(make_memo(), output_dir=tmp_path)
    doc = Document(str(path))
    assert all("---" not in p.text for p in doc.paragraphs)
