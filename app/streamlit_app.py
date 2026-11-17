"""
S&P Global Ratings Bank Credit Rating & Basel III Streamlit Portal
Author: Bhupesh Chandra Dimri
"""

import streamlit as st
import pandas as pd
from src.core_engine import BankFinancials, BankCreditRatingEngine

st.set_page_config(page_title="S&P Bank Credit Rating Portal", layout="wide")
st.title("S&P Global Ratings — Bank Credit Rating & Basel III Capital Intelligence Engine")
st.markdown("**Stand-Alone Credit Profile (SACP) Modeling, CAMELS Analytics & CCAR Stress-Testing**")

engine = BankCreditRatingEngine(anchor_rating="BBB+")

banks = [
    BankFinancials("JPMorgan Chase & Co", "JPM", 3875000000000.0, 1320000000000.0, 1780000000000.0, 275000000000.0, 318000000000.0, 7200000000.0, 18500000000.0, 2400000000000.0, 680000000000.0, 49500000000.0),
    BankFinancials("Bank of America Corp", "BAC", 3180000000000.0, 1050000000000.0, 1620000000000.0, 195000000000.0, 230000000000.0, 5800000000.0, 14200000000.0, 1950000000000.0, 720000000000.0, 26500000000.0),
    BankFinancials("PNC Financial Services", "PNC", 562000000000.0, 320000000000.0, 440000000000.0, 44500000000.0, 51000000000.0, 2400000000.0, 5400000000.0, 425000000000.0, 190000000000.0, 5600000000.0),
    BankFinancials("Sample Stressed Regional", "SSR", 120000000000.0, 85000000000.0, 95000000000.0, 7800000000.0, 8900000000.0, 2800000000.0, 1900000000.0, 92000000000.0, 68000000000.0, 650000000.0)
]

st.subheader("US Commercial Bank Peer Group Credit Surveillance")
rows = []
for b in banks:
    sacp = engine.evaluate_sacp(b)
    stress = engine.stress_test_dodd_frank(b, credit_loss_rate=0.035)
    rows.append({
        "Bank Name": b.bank_name,
        "Ticker": b.ticker,
        "CET1 Ratio": f"{sacp['cet1_ratio']:.2f}%",
        "Leverage": f"{sacp['tier1_leverage']:.2f}%",
        "NPA Ratio": f"{sacp['npa_ratio']:.2f}%",
        "CECL Coverage": f"{sacp['cecl_coverage']:.2f}x",
        "Anchor": sacp["anchor_rating"],
        "Notch Delta": f"{sacp['total_adjustment_notches']:+d}",
        "SACP Rating": sacp["sacp_rating"],
        "Post-Stress CET1": f"{stress['post_stress_cet1_pct']:.2f}%"
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True)
