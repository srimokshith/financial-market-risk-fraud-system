# 🚀 Real-Time Risk & Fraud Detection System for Financial Markets

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**An industry-ready financial surveillance system combining GARCH volatility modeling, machine learning-based fraud detection, and real-time market monitoring.**

This project demonstrates advanced quantitative finance, machine learning, and data engineering skills - perfect for placements, interviews, and exams.

## Live Link : 
https://financial-market-risk-fraud-system-afh54kluyhfzcuikrwh4ai.streamlit.app/

## ✨ Key Features

### 🎯 10-Step Professional Implementation

1. **📊 Data Preparation**
   - Multi-source ingestion (NIFTY, SENSEX, USD/INR)
   - Local CSV + yfinance API fallback
   - Automated date alignment and log returns calculation

2. **🔧 Feature Engineering**
   - Rolling volatility (10, 20-day windows)
   - Z-score normalization for outlier detection
   - Moving averages and trend deviations
   - Volatility ratios and market spreads

3. **📈 GARCH Volatility Modeling**
   - GARCH(1,1) conditional volatility forecasting
   - Persistence analysis (alpha + beta)
   - Comparison with rolling volatility
   - Industry-standard risk metrics

4. **🤖 ML-Based Anomaly Detection**
   - Isolation Forest algorithm (contamination=0.01)
   - Fraud/manipulation signal detection
   - Anomaly scoring and ranking
   - Feature standardization

5. **⚠️ Risk Scoring System**
   - Composite score: 0.5×volatility + 0.3×anomaly + 0.2×z-score
   - Three-tier classification (Low/Medium/High)
   - Normalized components (0-1 scale)
   - Real-time risk assessment

6. **🗳️ Event Analysis**
   - Election impact studies (1999-2019)
   - Short (-5, +5) and long (-20, +40) windows
   - Anomaly concentration during events
   - Volatility spike detection

7. **📊 Professional Visualizations**
   - NIFTY returns with anomaly highlights
   - Volatility comparison (Rolling vs GARCH)
   - Risk score timeline with categories
   - Event window analysis plots

8. **⚡ Real-Time Simulation**
   - Live data fetch via yfinance
   - On-the-fly feature calculation
   - Instant fraud alerts (YES/NO)
   - Current risk score output

9. **🖥️ Interactive Dashboard**
   - Streamlit web interface
   - Real-time metrics and charts
   - Event analysis tables
   - Cached performance optimization

10. **📝 Business Reporting**
    - Auto-generated exam-style explanations
    - Methodology documentation
    - Results summary with statistics
    - Business impact analysis

### 🔬 Advanced Statistical Tests
- **ADF Test** - Stationarity verification
- **ARCH-LM Test** - Volatility clustering detection
- **Ljung-Box Test** - Autocorrelation analysis

### 🏗️ Production-Ready Architecture
- Type-hinted Python code
- Modular design with clear separation
- Comprehensive error handling
- Configuration management
- Automated output persistence

## 📁 Project Structure

```
financial_market_risk_fraud_system/
├── src/financial_market_risk_fraud/
│   ├── __init__.py              # Package exports
│   ├── config.py                # Election dates & parameters
│   └── pipeline.py              # Core system (1005 lines)
├── data/raw/                    # Input data (see data/raw/README.md)
│   ├── README.md                # Data source instructions
│   ├── NIFTY_50.csv            # (gitignored)
│   ├── USD_INR.csv             # (gitignored)
│   └── Aligned_Returns.csv     # (gitignored)
├── outputs/                     # Generated results (gitignored)
│   ├── figures/                 # 4 visualization PNGs
│   ├── risk_fraud_feature_store.csv
│   ├── event_summary.csv
│   ├── event_detail.csv
│   ├── diagnostics_summary.csv
│   └── analysis_metadata.json
├── reports/
│   ├── exam_business_explanation.md
│   └── generated_exam_explanation.md  # Auto-generated
├── dashboard.py                 # Streamlit app (120 lines)
├── run_analysis.py              # CLI runner
├── requirements.txt             # Python dependencies
├── .gitignore                   # Proper exclusions
├── README.md                    # This file
├── FEATURE_CHECKLIST.md         # Implementation details
└── QUICK_START.md               # Demo guide
```

## 📊 Data Sources

The system requires historical market data. See `data/raw/README.md` for detailed instructions.

### Required Files (place in `data/raw/`)
- `NIFTY_50.csv` - NIFTY 50 index data
- `USD_INR.csv` - USD/INR exchange rates
- `Aligned_Returns.csv` - Pre-calculated returns (optional)
- `SENSEX.csv` / `BSE_SENSEX.csv` - Benchmark data (optional)

### Data Sources
1. **Yahoo Finance** - `^NSEI` (NIFTY), `INR=X` (USD/INR)
2. **NSE India** - [nseindia.com](https://www.nseindia.com/)
3. **yfinance API** - Automatic fallback if local files missing

**Note:** CSV files are gitignored. The system auto-fetches from yfinance if local data is unavailable.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to project
cd /home/mokshith/Documents/Projects/financial_market_risk_fraud_system

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Dashboard (Recommended)

```bash
streamlit run dashboard.py
```

**Dashboard opens at:** `http://localhost:8501`

### 3. Run CLI Analysis (Alternative)

```bash
python run_analysis.py
```

**Outputs saved to:** `outputs/` directory

---

## 📈 What You'll See

### Dashboard Features
- 📊 **Current Risk Score** - Real-time market risk level
- 🚨 **Anomaly Count** - Fraud/manipulation signals detected
- ⚠️ **Fraud Alert** - YES/NO indicator
- 📉 **4 Interactive Charts** - Returns, volatility, risk, events
- 🗳️ **Event Analysis** - Election impact statistics
- ⚡ **Real-time Monitor** - Live yfinance data

### Generated Outputs
```
outputs/
├── figures/
│   ├── nifty_returns_with_anomalies.png
│   ├── volatility_comparison.png
│   ├── risk_score_over_time.png
│   └── event_window_visualization.png
├── risk_fraud_feature_store.csv        # All features
├── event_summary.csv                   # Election analysis
├── event_detail.csv                    # Daily event data
├── diagnostics_summary.csv             # Statistical tests
├── prepared_market_data.csv            # Clean data
└── analysis_metadata.json              # Run metadata

reports/
└── generated_exam_explanation.md       # Business report
```

## 🎓 Technical Highlights

### Models & Algorithms
- **GARCH(1,1)** - Conditional volatility forecasting with persistence analysis
- **Isolation Forest** - Unsupervised anomaly detection (contamination=0.01)
- **Composite Risk Scoring** - Weighted multi-factor model
- **Event Study Methodology** - Election impact analysis

### Technologies Used
- **Python 3.12** - Core language
- **pandas & numpy** - Data manipulation
- **statsmodels** - Statistical tests (ADF, ARCH, Ljung-Box)
- **arch** - GARCH modeling
- **scikit-learn** - ML (Isolation Forest, scalers)
- **matplotlib & seaborn** - Visualizations
- **yfinance** - Real-time data
- **streamlit** - Interactive dashboard

### Code Quality
- ✅ Type hints throughout
- ✅ Modular architecture
- ✅ Comprehensive error handling
- ✅ Configuration management
- ✅ Automated testing ready
- ✅ Production-ready structure

---

## 💼 Business Impact

### Use Cases
1. **Risk Management** - Early warning system for portfolio managers
2. **Fraud Detection** - Automated surveillance for suspicious patterns
3. **Regulatory Compliance** - SEBI/SEC market monitoring
4. **Event Monitoring** - Policy/election impact tracking
5. **Real-time Alerts** - Immediate high-risk notifications

### Value Proposition
- Prevents financial losses through early detection
- Identifies market manipulation patterns
- Improves market integrity and transparency
- Reduces manual surveillance costs
- Enables data-driven risk decisions

---

## 🎯 For Placements & Interviews

### What Makes This Project Stand Out
✅ **Quantitative Finance** - GARCH, volatility modeling, event studies  
✅ **Machine Learning** - Isolation Forest, feature engineering  
✅ **Data Engineering** - Multi-source pipeline, ETL  
✅ **Software Engineering** - Clean code, type hints, modularity  
✅ **Real-time Systems** - Live monitoring, API integration  
✅ **Business Context** - Clear problem statement and impact  
✅ **Visualization** - Professional charts and dashboard  
✅ **Statistical Rigor** - ADF, ARCH, Ljung-Box tests  

### Interview Talking Points
See `QUICK_START.md` for:
- 30-second elevator pitch
- Demo flow (6 minutes)
- Q&A preparation
- Technical deep-dives

---

## 📚 Documentation

- **README.md** (this file) - Project overview
- **FEATURE_CHECKLIST.md** - Detailed implementation breakdown
- **QUICK_START.md** - Demo guide and interview prep
- **data/raw/README.md** - Data source instructions
- **reports/generated_exam_explanation.md** - Auto-generated business report

---

## 🔧 Troubleshooting

### Dashboard won't start?
```bash
source .venv/bin/activate
pip install streamlit
streamlit run dashboard.py
```

### No data showing?
- Ensure internet connection (for yfinance)
- Check `data/raw/` for CSV files
- System auto-fetches if local data missing

### Import errors?
```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

This is a personal project for placements/exams. Feel free to fork and adapt for your needs.

### Fraud Detection Explanation (for Interviews)

**Important:** In financial markets, "anomaly" ≠ illegal fraud. It means abnormal behavior relative to normal patterns of returns, volatility, and FX movement.

**Anomalies indicate surveillance candidates for:**
- Rumor-driven trading
- Panic liquidation
- Politically sensitive repricing
- Coordinated speculative moves
- Unusual cross-market stress
- Potential manipulation patterns

This framing makes the project relevant for both **market risk** and **fraud analytics** roles.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👤 Author

**Mokshith**  
Financial Risk Analytics & Machine Learning  
[GitHub](https://github.com/srimokshith/financial-market-risk-fraud-system)

---

## 🙏 Acknowledgments

- NSE India for market data standards
- Yahoo Finance for API access
- Statsmodels & arch libraries for financial modeling
- Streamlit for dashboard framework

---
