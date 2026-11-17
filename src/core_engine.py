"""
S&P Global Ratings Bank Credit Rating & Basel III Capital Intelligence Core Engine
Author: Bhupesh Chandra Dimri
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class BankFinancials:
    bank_name: str
    ticker: str
    total_assets: float
    total_loans: float
    risk_weighted_assets: float
    cet1_capital: float
    tier1_capital: float
    non_performing_assets: float
    allowance_credit_losses: float
    total_deposits: float
    uninsured_deposits: float
    net_income: float

    @property
    def cet1_ratio(self) -> float:
        if self.risk_weighted_assets <= 0:
            return 0.0
        return self.cet1_capital / self.risk_weighted_assets

    @property
    def tier1_leverage_ratio(self) -> float:
        if self.total_assets <= 0:
            return 0.0
        return self.tier1_capital / self.total_assets

    @property
    def npa_ratio(self) -> float:
        if self.total_loans <= 0:
            return 0.0
        return self.non_performing_assets / self.total_loans

    @property
    def cecl_npa_coverage(self) -> float:
        if self.non_performing_assets <= 0:
            return 999.0
        return self.allowance_credit_losses / self.non_performing_assets

    @property
    def uninsured_deposit_pct(self) -> float:
        if self.total_deposits <= 0:
            return 0.0
        return self.uninsured_deposits / self.total_deposits

    @property
    def roaa(self) -> float:
        """Return on Average Assets."""
        if self.total_assets <= 0:
            return 0.0
        return self.net_income / self.total_assets


class BankCreditRatingEngine:
    """S&P Bank Rating Methodology & Basel III Stress Evaluation Engine."""

    RATING_SCALE = [
        "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
        "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B"
    ]

    def __init__(self, anchor_rating: str = "BBB+"):
        self.anchor_rating = anchor_rating
        self.anchor_index = self.RATING_SCALE.index(anchor_rating)

    def evaluate_sacp(self, bank: BankFinancials) -> Dict[str, any]:
        """Calculates Stand-Alone Credit Profile (SACP) using S&P analytical modifiers."""
        score_modifier = 0

        # 1. Capital & Earnings Modifier (CET1 Ratio)
        if bank.cet1_ratio >= 0.14:
            cap_mod = +2  # Very Strong
        elif bank.cet1_ratio >= 0.11:
            cap_mod = +1  # Strong
        elif bank.cet1_ratio >= 0.08:
            cap_mod = 0   # Adequate
        else:
            cap_mod = -2  # Weak

        # 2. Risk Position / Asset Quality (NPA Ratio)
        if bank.npa_ratio <= 0.0075 and bank.cecl_npa_coverage >= 1.5:
            risk_mod = +1  # Strong
        elif bank.npa_ratio <= 0.020:
            risk_mod = 0   # Adequate
        else:
            risk_mod = -2  # Weak / Concentrated Losses

        # 3. Funding & Liquidity (Uninsured Deposit Ratio)
        if bank.uninsured_deposit_pct <= 0.35:
            fund_mod = 0   # Strong / Granular
        elif bank.uninsured_deposit_pct <= 0.60:
            fund_mod = -1  # Moderate Wholesale Reliance
        else:
            fund_mod = -2  # Volatile Funding Run Risk

        total_notch_adjustment = cap_mod + risk_mod + fund_mod
        final_index = int(np.clip(self.anchor_index - total_notch_adjustment, 0, len(self.RATING_SCALE) - 1))
        sacp_rating = self.RATING_SCALE[final_index]

        return {
            "bank_name": bank.bank_name,
            "anchor_rating": self.anchor_rating,
            "capital_modifier": cap_mod,
            "risk_modifier": risk_mod,
            "funding_modifier": fund_mod,
            "total_adjustment_notches": total_notch_adjustment,
            "sacp_rating": sacp_rating,
            "cet1_ratio": round(bank.cet1_ratio * 100, 2),
            "tier1_leverage": round(bank.tier1_leverage_ratio * 100, 2),
            "npa_ratio": round(bank.npa_ratio * 100, 2),
            "cecl_coverage": round(bank.cecl_npa_coverage, 2)
        }

    def stress_test_dodd_frank(
        self, bank: BankFinancials, credit_loss_rate: float = 0.035, rwa_expansion: float = 0.15
    ) -> Dict[str, float]:
        """Simulates CCAR severely adverse macroeconomic stress scenario."""
        stress_losses = bank.total_loans * credit_loss_rate
        post_stress_cet1_capital = max(0.0, bank.cet1_capital - stress_losses)
        post_stress_rwa = bank.risk_weighted_assets * (1.0 + rwa_expansion)

        post_stress_cet1_ratio = post_stress_cet1_capital / post_stress_rwa if post_stress_rwa > 0 else 0.0
        cushion_above_min = post_stress_cet1_ratio - 0.045  # 4.5% regulatory threshold

        return {
            "baseline_cet1_pct": round(bank.cet1_ratio * 100, 2),
            "simulated_credit_losses": round(stress_losses, 2),
            "post_stress_cet1_pct": round(post_stress_cet1_ratio * 100, 2),
            "cushion_above_4_5pct": round(cushion_above_min * 100, 2),
            "stress_test_pass": cushion_above_min >= 0.0
        }
