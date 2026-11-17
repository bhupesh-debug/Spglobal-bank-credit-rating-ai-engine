"""Unit tests for S&P Global Ratings Bank Credit Rating & Basel III Engine."""

import pytest
from src.core_engine import BankFinancials, BankCreditRatingEngine


@pytest.fixture
def bank_fixture():
    # Fortress G-SIB Bank (e.g. JPMorgan type)
    b_strong = BankFinancials(
        bank_name="Fortress National Bank",
        ticker="FNB",
        total_assets=3500000000000.0,
        total_loans=1300000000000.0,
        risk_weighted_assets=1800000000000.0,
        cet1_capital=270000000000.0,  # CET1 = 15.0%
        tier1_capital=315000000000.0, # Tier 1 Lev = 9.0%
        non_performing_assets=6500000000.0,  # NPA = 0.50%
        allowance_credit_losses=16000000000.0, # CECL coverage = 2.46x
        total_deposits=2400000000000.0,
        uninsured_deposits=700000000000.0, # Uninsured = 29.1%
        net_income=45000000000.0
    )
    # Stressed regional bank (high uninsured deposits, lower CET1)
    b_stressed = BankFinancials(
        bank_name="Vulnerable Regional Bancorp",
        ticker="VRB",
        total_assets=180000000000.0,
        total_loans=120000000000.0,
        risk_weighted_assets=135000000000.0,
        cet1_capital=10800000000.0,  # CET1 = 8.0%
        tier1_capital=12500000000.0, # Tier 1 Lev = 6.9%
        non_performing_assets=3600000000.0,  # NPA = 3.0%
        allowance_credit_losses=2700000000.0, # CECL coverage = 0.75x
        total_deposits=140000000000.0,
        uninsured_deposits=105000000000.0, # Uninsured = 75.0%
        net_income=850000000.0
    )
    return {"strong": b_strong, "stressed": b_stressed}


def test_regulatory_capital_ratios(bank_fixture):
    b = bank_fixture["strong"]
    assert round(b.cet1_ratio * 100, 1) == 15.0
    assert round(b.tier1_leverage_ratio * 100, 1) == 9.0
    assert b.cet1_ratio >= 0.045
    assert b.tier1_leverage_ratio >= 0.040


def test_sacp_rating_notching(bank_fixture):
    engine = BankCreditRatingEngine(anchor_rating="BBB+")
    eval_strong = engine.evaluate_sacp(bank_fixture["strong"])
    eval_stressed = engine.evaluate_sacp(bank_fixture["stressed"])

    # Strong bank gets positive modifiers (+2 capital, +1 risk, 0 funding) -> Notches up from BBB+ to A+
    assert eval_strong["total_adjustment_notches"] > 0
    assert eval_strong["sacp_rating"] in ["A+", "AA-", "AA"]

    # Stressed bank gets negative modifiers -> Notches down to BBB- or BB+
    assert eval_stressed["total_adjustment_notches"] < 0
    assert eval_stressed["sacp_rating"] in ["BBB-", "BB+", "BB"]


def test_dodd_frank_stress_test_simulation(bank_fixture):
    engine = BankCreditRatingEngine()
    stress_strong = engine.stress_test_dodd_frank(bank_fixture["strong"], credit_loss_rate=0.035)
    assert stress_strong["stress_test_pass"] is True
    assert stress_strong["post_stress_cet1_pct"] > 4.5

    stress_stressed = engine.stress_test_dodd_frank(bank_fixture["stressed"], credit_loss_rate=0.055)
    # Severe loss on high loan book should significantly reduce CET1
    assert stress_stressed["post_stress_cet1_pct"] < bank_fixture["stressed"].cet1_ratio * 100
