"""Tests des invariants de DeckSignals (couplage valeur/unité)."""

from src.models import DeckSignals


def test_valo_sans_devise_est_rejetee():
    # Une valorisation sans devise est inexploitable : les deux moitiés retombent à None.
    s = DeckSignals(pre_money_valuation=8_000_000)
    assert s.pre_money_valuation is None
    assert s.pre_money_currency is None


def test_valo_avec_devise_est_conservee():
    s = DeckSignals(pre_money_valuation=8_000_000, pre_money_currency="EUR", new_option_pool_pct=10.0)
    assert s.pre_money_valuation == 8_000_000
    assert s.pre_money_currency == "EUR"
    assert s.new_option_pool_pct == 10.0
