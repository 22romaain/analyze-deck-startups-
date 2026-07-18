"""Tests de la contre-analyse LLM (avocat du diable), sans API."""

from src.analysis import run_analysis
from src.models import DeckSignals
from src.review import _summarize, generate_review
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
