"""Tests du rendu Streamlit du mémo.

Streamlit exécute un script pour produire une page : on ne peut pas inspecter le
résultat en appelant les fonctions directement. AppTest joue le script sans
navigateur et donne accès aux éléments produits. La fonction passée à AppTest est
exécutée dans un contexte séparé, d'où ses imports refaits à l'intérieur.
"""

from streamlit.testing.v1 import AppTest


def _page_memo_complet():
    """Script joué par AppTest : rend le mémo de référence."""
    from src.output.render_streamlit import render_memo
    from tests.test_render_markdown import make_memo

    render_memo(make_memo())


def _page_memo_avec_narratif():
    """Script joué par AppTest : le même mémo, dont une dimension porte un narratif."""
    from src.output.render_streamlit import render_memo
    from tests.test_render_markdown import make_memo

    memo = make_memo()
    memo.dimensions[0].narratif = "Deux fondateurs, dont un CTO ex-Criteo."
    render_memo(memo)


def _page_memo_sans_chiffres():
    """Script joué par AppTest : le mémo de référence sans aucun chiffre brut."""
    from src.output.render_streamlit import render_memo
    from tests.test_render_markdown import make_memo

    memo = make_memo()
    memo.chiffres_deck = []
    render_memo(memo)


def _lance(script) -> AppTest:
    at = AppTest.from_function(script, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_render_memo_affiche_toutes_les_sections():
    """Les sections du mémo pivoté doivent être présentes, dans l'ordre du document."""
    at = _lance(_page_memo_complet)
    attendus = [
        "Recommandation : APPROFONDIR", "Synthèse", "Grille d'attendus",
        "Ce que le deck affirme", "Analyse par dimension", "Incohérences internes",
        "Analyse au regard de ta thèse", "Cap table et dilution",
    ]
    assert [s.value for s in at.subheader] == attendus


def test_render_memo_affiche_le_bandeau_de_contre_analyse():
    # Mode dégradé : le bandeau explique pourquoi la section est vide.
    at = _lance(_page_memo_complet)
    assert any("indisponible" in i.value for i in at.info)


def test_render_memo_affiche_le_narratif_quand_il_existe():
    at = _lance(_page_memo_avec_narratif)
    textes = [m.value for m in at.markdown]
    assert "**Ce que dit le deck**" in textes


def test_render_memo_sans_narratif_n_affiche_pas_le_titre():
    """Le narratif est optionnel : sans lui, son intitulé ne doit pas apparaître."""
    at = _lance(_page_memo_complet)
    assert "**Ce que dit le deck**" not in [m.value for m in at.markdown]


def test_deck_figures_absent_quand_aucun_chiffre():
    """Inventaire optionnel : sans chiffre brut, la section n'apparaît pas."""
    at = _lance(_page_memo_sans_chiffres)
    assert "Ce que le deck affirme" not in [s.value for s in at.subheader]
