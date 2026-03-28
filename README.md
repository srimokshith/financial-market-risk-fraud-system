# Financial Market Risk and Fraud System

This project upgrades your election-impact analysis into a placement-ready market-surveillance system. It keeps the original financial analytics core, then adds feature engineering, GARCH-based volatility intelligence, anomaly detection, risk scoring, election-window monitoring, a real-time simulation layer, and a Streamlit dashboard.

## What the project does

- Aligns NIFTY, SENSEX, and USD/INR market data by date.
- Computes fresh log returns from the close prices.
- Builds advanced features such as rolling volatility, z-scores, moving averages, deviation from trend, and volatility ratio.
- Fits a GARCH(1,1) model and compares its conditional volatility with rolling volatility.
- Uses Isolation Forest to flag anomalous market sessions that may indicate suspicious stress behavior, shock days, manipulation risk, or election-led dislocation.
- Converts model outputs into a weighted risk score and Low/Medium/High categories.
- Analyzes election windows `(-5, +5)` and `(-20, +40)` for anomaly concentration and volatility spikes.
- Produces charts and a generated exam explanation report.
- Runs a live market simulation with `yfinance` for current risk score and fraud alert output.

## Project structure

- `run_analysis.py`: main pipeline runner.
- `dashboard.py`: Streamlit dashboard entry point.
- `src/financial_market_risk_fraud/config.py`: project settings and election dates.
- `src/financial_market_risk_fraud/pipeline.py`: end-to-end data, modeling, visualization, and reporting logic.
- `data/raw/`: local CSV inputs.
- `outputs/`: generated datasets, metrics, metadata, and figures.
- `reports/generated_exam_explanation.md`: exam-style explanation produced after running the pipeline.

## Local inputs already copied into this folder

- `data/raw/NIFTY_50.csv`
- `data/raw/USD_INR.csv`
- `data/raw/Aligned_Returns.csv`

If you also have a benchmark file, place it in `data/raw/` as one of:

- `SENSEX.csv`
- `BSE_SENSEX.csv`
- `SENSEX_30.csv`

If no local SENSEX file is available, the code tries to fetch it from `yfinance`.

## Setup

Create or activate the project virtual environment:

```bash
cd /home/mokshith/Documents/Projects/financial_market_risk_fraud_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the full analysis

```bash
cd /home/mokshith/Documents/Projects/financial_market_risk_fraud_system
source .venv/bin/activate
python run_analysis.py
```

Main generated outputs:

- `outputs/prepared_market_data.csv`
- `outputs/diagnostics_summary.csv`
- `outputs/risk_fraud_feature_store.csv`
- `outputs/event_summary.csv`
- `outputs/analysis_metadata.json`
- `outputs/figures/*.png`
- `reports/generated_exam_explanation.md`

## Run the dashboard

```bash
cd /home/mokshith/Documents/Projects/financial_market_risk_fraud_system
source .venv/bin/activate
streamlit run dashboard.py
```

## How the fraud logic should be explained in viva or placements

In a financial-market setting, an anomaly does not automatically mean illegal fraud. It means the day behaved abnormally relative to its normal joint pattern of returns, volatility, and FX movement. Those sessions become surveillance candidates for:

- rumor-driven trading,
- panic liquidation,
- politically sensitive repricing,
- coordinated speculative moves,
- unusual cross-market stress.

That framing makes the project relevant for both market risk and fraud analytics roles.
