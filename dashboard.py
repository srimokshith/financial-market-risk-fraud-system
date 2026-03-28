from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from financial_market_risk_fraud import MarketRiskFraudSystem, ProjectConfig


st.set_page_config(
    page_title="Election Market Risk and Fraud Monitor",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def run_cached_analysis(run_realtime: bool) -> dict:
    system = MarketRiskFraudSystem(ProjectConfig())
    return system.run_full_analysis(run_realtime=run_realtime)


st.title("Real-Time Risk and Fraud Detection System for Financial Markets")
st.caption(
    "Election-driven market surveillance using NIFTY, SENSEX, USD/INR, GARCH volatility, "
    "Isolation Forest anomaly detection, and a composite risk score."
)

run_realtime = st.sidebar.checkbox("Run real-time yfinance simulation", value=True)
results = run_cached_analysis(run_realtime=run_realtime)

risk_frame: pd.DataFrame = results["risk_frame"].copy()
event_summary: pd.DataFrame = results["event_summary"].copy()
notes: list[str] = results["notes"]
realtime = results["realtime_summary"]

if risk_frame.empty:
    st.error("No scored rows are available. Check the raw data inputs and dependencies.")
    st.stop()

latest_historical = risk_frame.iloc[-1]
current_score = (
    realtime["current_risk_score"] if realtime.get("status") == "available" else latest_historical["risk_score"]
)
current_category = (
    realtime["risk_category"] if realtime.get("status") == "available" else latest_historical["risk_category"]
)
fraud_alert = (
    "Yes" if realtime.get("status") == "available" and realtime.get("fraud_alert") else "No"
)

metric_cols = st.columns(4)
metric_cols[0].metric("Current Risk Score", f"{current_score:.2f}")
metric_cols[1].metric("Current Risk Category", str(current_category))
metric_cols[2].metric("Detected Anomalies", int(risk_frame["anomaly"].sum()))
metric_cols[3].metric("Fraud Alert", fraud_alert)

if realtime.get("status") == "available":
    st.info(
        f"Real-time snapshot date: {realtime['timestamp']} | "
        f"NIFTY return: {realtime['nifty_return']:.2f}% | "
        f"USD/INR return: {realtime['usdinr_return']:.2f}%"
    )
elif realtime.get("status") == "unavailable":
    st.warning(realtime.get("reason", "Real-time simulation is unavailable."))

if notes:
    with st.expander("Implementation Notes"):
        for note in notes:
            st.write(f"- {note}")

chart_col_1, chart_col_2 = st.columns(2)
with chart_col_1:
    st.subheader("Risk Score Over Time")
    st.line_chart(risk_frame[["risk_score"]], height=320)

with chart_col_2:
    st.subheader("Volatility Comparison")
    vol_cols = [col for col in ["GARCH_Volatility", "NIFTY_Rolling_Vol_10", "NIFTY_Rolling_Vol_20"] if col in risk_frame.columns]
    st.line_chart(risk_frame[vol_cols], height=320)

st.subheader("Returns and Anomalies")
returns_view = risk_frame[["NIFTY_Return", "anomaly", "risk_score", "risk_category"]].copy()
st.dataframe(returns_view.tail(30), use_container_width=True)

st.subheader("Risk Category Distribution")
st.bar_chart(risk_frame["risk_category"].value_counts().sort_index())

supported_events = event_summary[event_summary.get("Supported", False) == True].copy()
st.subheader("Election Event Analysis")
if supported_events.empty:
    st.warning("No election windows are supported by the currently available historical coverage.")
else:
    st.dataframe(
        supported_events[
            [
                "Event_Year",
                "Window",
                "Anomaly_Count",
                "Anomaly_Frequency",
                "Volatility_Spike_Pct",
                "Average_Risk_Score",
                "Peak_Risk_Score",
                "Insight",
            ]
        ],
        use_container_width=True,
    )

st.subheader("Generated Figures")
for label, path in results["figures"].items():
    st.image(path, caption=label.replace("_", " ").title(), use_container_width=True)
