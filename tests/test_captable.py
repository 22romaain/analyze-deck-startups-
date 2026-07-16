"""Tests du moteur de dilution (phase 4). Vérité finance vérifiable à la main."""

import pytest

from src.captable import RoundInput, compute_dilution


def test_compute_dilution_basique():
    # Pre 8M, tour 2M -> post 10M. Investisseur = 20%. Fondateurs 80% -> 80% x 0,8 = 64%.
    res = compute_dilution(RoundInput(pre_money=8_000_000, amount=2_000_000, founder_pct_pre=80.0))
    assert res.post_money == 10_000_000
    assert res.new_investor_pct == pytest.approx(20.0)
    assert res.founder_pct_post == pytest.approx(64.0)
    assert res.founder_dilution_points == pytest.approx(16.0)


def test_compute_dilution_tour_egal_pre_money():
    # Tour = pre-money : l'investisseur prend 50%, les fondateurs sont divises par deux.
    res = compute_dilution(RoundInput(pre_money=5_000_000, amount=5_000_000, founder_pct_pre=60.0))
    assert res.new_investor_pct == pytest.approx(50.0)
    assert res.founder_pct_post == pytest.approx(30.0)


def test_compute_dilution_avec_option_pool_pre_money():
    # Meme tour + pool de 10% cree pre-money. Investisseur reste a 20% (non dilue par le pool).
    # Fondateurs 80% x (1 - 0,20 - 0,10) = 80% x 0,70 = 56% (8 points de plus qu'a 64%).
    res = compute_dilution(RoundInput(
        pre_money=8_000_000, amount=2_000_000, founder_pct_pre=80.0, new_option_pool_pct=10.0))
    assert res.new_investor_pct == pytest.approx(20.0)
    assert res.option_pool_pct == pytest.approx(10.0)
    assert res.founder_pct_post == pytest.approx(56.0)
    assert res.founder_dilution_points == pytest.approx(24.0)


def test_compute_dilution_termes_incoherents_leve_erreur():
    # Pool de 90% avec un investisseur a 20% : plus de 100% preleve, termes absurdes.
    with pytest.raises(ValueError):
        compute_dilution(RoundInput(
            pre_money=8_000_000, amount=2_000_000, founder_pct_pre=80.0, new_option_pool_pct=90.0))


def test_round_input_refuse_valeurs_absurdes():
    # pre_money et amount doivent etre strictement positifs ; part fondateurs dans [0, 100].
    with pytest.raises(ValueError):
        RoundInput(pre_money=0, amount=1_000_000, founder_pct_pre=80.0)
    with pytest.raises(ValueError):
        RoundInput(pre_money=1_000_000, amount=1_000_000, founder_pct_pre=120.0)
