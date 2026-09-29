"""Tests du moteur de waterfall (liquidation preferences). Finance vérifiable à la main."""

import pytest

from src.analysis import detect_waterfall_flag
from src.captable import LiquidationPref, compute_waterfall


def test_waterfall_non_participating_mange_la_sortie():
    # Sortie 12M, pref 10M en 1x non-participating pour 50%. Elle reprend 10M,
    # il reste 2M pour les fondateurs (au lieu de 6M sans preference).
    pref = LiquidationPref(name="Serie A", invested=10_000_000, as_converted_pct=50.0)
    res = compute_waterfall(12_000_000, [pref], founder_pct=50.0)
    assert res.founders_payout == pytest.approx(2_000_000)
    assert res.preferred_payout == pytest.approx(10_000_000)


def test_waterfall_participating_double_dip():
    # Sortie 20M, pref 10M 1x PARTICIPATING pour 50%. Elle prend 10M puis re-participe :
    # reste 10M partage 50/50 -> fondateurs 5M, preferentiel 15M.
    pref = LiquidationPref(name="Serie A", invested=10_000_000, participating=True, as_converted_pct=50.0)
    res = compute_waterfall(20_000_000, [pref], founder_pct=50.0)
    assert res.founders_payout == pytest.approx(5_000_000)
    assert res.preferred_payout == pytest.approx(15_000_000)


def test_waterfall_seniority_sert_le_senior_dabord():
    # Sortie 10M insuffisante. Senior (invest 8M) servi avant junior (invest 5M) :
    # senior prend 8M, junior prend les 2M restants, fondateurs 0.
    senior = LiquidationPref(name="B", invested=8_000_000, as_converted_pct=30.0, seniority=2)
    junior = LiquidationPref(name="A", invested=5_000_000, as_converted_pct=30.0, seniority=1)
    res = compute_waterfall(10_000_000, [junior, senior], founder_pct=40.0)
    assert res.founders_payout == pytest.approx(0.0)
    assert res.preferred_payout == pytest.approx(10_000_000)


def test_waterfall_grosse_sortie_fondateurs_touchent():
    # Sortie 50M, pref 10M 1x non-participating 50%. Pref reprend 10M, reste 40M aux fondateurs.
    pref = LiquidationPref(name="Serie A", invested=10_000_000, as_converted_pct=50.0)
    res = compute_waterfall(50_000_000, [pref], founder_pct=50.0)
    assert res.founders_payout == pytest.approx(40_000_000)
    assert res.founders_pct_of_exit == pytest.approx(80.0)


def test_waterfall_flag_critique_quand_fondateurs_ecrases():
    # Post-money 12M. Prefs empilees 2x pour 11M investis : au post-money, les
    # fondateurs passent sous 10% -> red flag CRITIQUE.
    prefs = [LiquidationPref(name="A", invested=5_500_000, multiple=2.0, as_converted_pct=45.0)]
    flag = detect_waterfall_flag(prefs, founder_pct=55.0, post_money=12_000_000)
    assert flag is not None and flag.severity == "CRITIQUE"
    assert "Waterfall" in flag.message


def test_waterfall_flag_absent_quand_fondateurs_proteges():
    # Preference legere (2M en 1x) sur un post-money de 20M : fondateurs bien au-dessus du plancher.
    prefs = [LiquidationPref(name="A", invested=2_000_000, as_converted_pct=20.0)]
    assert detect_waterfall_flag(prefs, founder_pct=80.0, post_money=20_000_000) is None


def test_waterfall_flag_absent_sans_prefs():
    # Pas de preference connue -> pas de simulation, pas d'alerte.
    assert detect_waterfall_flag([], founder_pct=80.0, post_money=20_000_000) is None


def test_run_analysis_remonte_le_flag_waterfall():
    # Branchement complet : des prefs lourdes dans les signaux -> flag CRITIQUE dans l'analyse.
    from src.analysis import run_analysis
    from src.models import DeckSignals

    signals = DeckSignals(
        founder_ownership_pct=55.0, pre_money_valuation=8_000_000, pre_money_currency="EUR",
        liquidation_prefs=[LiquidationPref(name="A", invested=6_000_000, multiple=2.0, as_converted_pct=45.0)],
    )
    result = run_analysis(signals, "serie-a", "4M EUR")  # post-money = 12M
    assert any(f.severity == "CRITIQUE" and "Waterfall" in f.message for f in result.red_flags)
