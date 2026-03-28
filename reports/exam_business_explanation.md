# Exam Business Explanation

## Problem Statement
The project studies the impact of Indian general elections on stock market returns, volatility, and exchange-rate movement, then extends that academic study into a practical market-risk and anomaly-monitoring solution. The business objective is to identify stress periods quickly so financial institutions can detect unusual trading behavior, control exposure, and respond to politically sensitive market conditions.

## Methodology
1. NIFTY, SENSEX, and USD/INR datasets are aligned on trading dates.
2. Log returns are computed from clean close prices.
3. Statistical diagnostics such as ADF, ARCH-LM, and Ljung-Box validate return behavior and volatility clustering.
4. Rolling-volatility and trend-based features are engineered to capture short-term and long-term market stress.
5. A GARCH(1,1) model estimates conditional volatility and captures volatility persistence.
6. Isolation Forest identifies anomalous sessions using returns, volatility, z-score, and exchange-rate features.
7. A normalized weighted risk score classifies each session into Low, Medium, or High risk.
8. Election event windows are analyzed to measure anomaly concentration and volatility spikes.
9. A real-time simulation fetches fresh market data and produces a current risk score and fraud alert.

## Models Used
- Log-return model for market movement representation
- ADF for stationarity testing
- ARCH-LM for volatility clustering detection
- Ljung-Box for residual autocorrelation review
- GARCH(1,1) for conditional volatility forecasting
- Isolation Forest for anomaly detection
- Min-max normalized weighted risk scoring for business interpretation

## Results to Highlight
- The project converts a static election-impact study into an operational monitoring framework.
- It does not rely only on historical interpretation; it also generates current risk and alert outputs.
- It integrates econometrics and machine learning in one flow, which is stronger for analytics and quant-facing interviews.
- It is useful for market surveillance because the anomaly signal identifies abnormal joint behavior, not just large returns.

## Business Impact
- Risk management teams can identify periods of elevated market stress and respond faster.
- Fraud and surveillance teams can review abnormal sessions flagged by the anomaly engine.
- Treasury, broking, and trading desks can use the risk score to support hedge and exposure decisions.
- The dashboard makes the output understandable for non-technical users.

## Placement Value
This project is stronger than a standard event-study notebook because it demonstrates:

- financial time-series preprocessing,
- statistical diagnostics,
- volatility modeling,
- machine learning anomaly detection,
- risk-score design,
- dashboard deployment,
- business translation of model output.

After running the pipeline, use `reports/generated_exam_explanation.md` for the version populated with actual project metrics.
