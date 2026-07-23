"""Tests de la contre-analyse LLM (avocat du diable), sans API."""

from src.analysis import run_analysis
from src.models import DeckSignals
from src.review import _summarize, charger_these, generate_review, rassembler_contexte_cours
from src.rag.index import SearchHit
from tests.test_build_memo_data import make_deck


class _Resp:
    """Fausse réponse Mistral : expose .choices[0].message.content."""
    def __init__(self, content):
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]


def _analysis():
    return run_analysis(DeckSignals(), "serie-a")


def test_summarize_contient_les_faits():
    s = _summarize(make_deck(), _analysis())
    assert "serie-a" in s and "Red flags" in s and "Équipe" in s


def test_generate_review_renvoie_le_texte():
    fake = lambda client, model, messages: _Resp("Le moat n'est pas defendable.")
    assert generate_review(None, make_deck(), _analysis(), complete=fake) == "Le moat n'est pas defendable."


def test_generate_review_none_si_echec():
    def boom(client, model, messages):
        raise RuntimeError("api down")
    # Toute erreur est absorbee : le memo garde son mode degrade.
    assert generate_review(None, make_deck(), _analysis(), complete=boom) is None


def test_generate_review_none_si_reponse_vide():
    fake = lambda client, model, messages: _Resp("   ")
    assert generate_review(None, make_deck(), _analysis(), complete=fake) is None


def test_charger_these_ignore_les_commentaires(tmp_path):
    # Un fichier qui n'a que des consignes en commentaire HTML = thèse vide.
    p = tmp_path / "these.md"
    p.write_text("<!-- consignes du gabarit -->\n", encoding="utf-8")
    assert charger_these(p) == ""
    # Du texte réel sous les commentaires est bien récupéré.
    p.write_text("<!-- consignes -->\nOn ne finance que du B2B SaaS europeen.", encoding="utf-8")
    assert "B2B SaaS europeen" in charger_these(p)


def test_rassembler_contexte_cours_dedoublonne():
    def fake(query, k):
        return {
            "a": [SearchHit(text="Founder-market fit.", source="vc.md", section="Equipe", distance=0.3)],
            "b": [SearchHit(text="TAM bottom-up.", source="vc.md", section="Marche", distance=0.4),
                  SearchHit(text="Founder-market fit.", source="vc.md", section="Equipe", distance=0.3)],
        }.get(query, [])

    texte, cits = rassembler_contexte_cours(fake, ["a", "b"])
    assert len(cits) == 2  # le doublon (Equipe) est écarté
    assert "Founder-market fit." in texte and "TAM bottom-up." in texte


def test_rassembler_contexte_cours_budget_caracteres():
    def fake(query, k):
        return [SearchHit(text="x" * 400, source="vc.md", section=str(query), distance=0.2)]

    texte, cits = rassembler_contexte_cours(fake, ["1", "2", "3"], max_chars=500)
    # 500 caractères : un seul extrait (~400 + entête) tient, le reste est coupé.
    assert len(cits) == 1


def test_rassembler_contexte_cours_sans_retriever():
    assert rassembler_contexte_cours(None, ["a"]) == ("", [])


def test_generate_review_injecte_la_these():
    # La thèse fournie doit apparaître dans le prompt système envoyé au LLM.
    captured = {}
    def fake(client, model, messages):
        captured["system"] = messages[0]["content"]
        return _Resp("ok")
    generate_review(None, make_deck(), _analysis(), complete=fake, these="Angle contrarian sur la fintech.")
    assert "Angle contrarian sur la fintech." in captured["system"]


def test_generate_review_injecte_la_doctrine_des_cours():
    # Le bloc de contexte cours doit entrer dans le prompt système (doctrine appliquée).
    captured = {}
    def fake(client, model, messages):
        captured["system"] = messages[0]["content"]
        return _Resp("ok")
    generate_review(None, make_deck(), _analysis(), complete=fake,
                    these="", contexte_cours="[vc.md §Marche] Exiger un TAM bottom-up.")
    assert "Exiger un TAM bottom-up." in captured["system"]
