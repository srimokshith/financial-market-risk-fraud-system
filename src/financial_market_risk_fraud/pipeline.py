from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import yfinance as yf
from arch import arch_model
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.stattools import adfuller

from .config import ProjectConfig


sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["figure.figsize"] = (15, 7)
pd.options.display.float_format = "{:,.4f}".format
warnings.filterwarnings("ignore")


class MarketRiskFraudSystem:
    """Industry-style pipeline for election-driven market risk and anomaly monitoring."""

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)

        self.notes: list[str] = []
        self.model_features: list[str] = []
        self.anomaly_scaler: StandardScaler | None = None
        self.anomaly_model: IsolationForest | None = None
        self.volatility_scaler: MinMaxScaler | None = None
        self.zscore_scaler: MinMaxScaler | None = None
        self.garch_result: Any | None = None

    def run_full_analysis(self, run_realtime: bool = True) -> dict[str, Any]:
        prepared_data = self.prepare_data()
        diagnostics = self.run_diagnostics(prepared_data)

        feature_frame = self.engineer_features(prepared_data)
        feature_frame, garch_summary = self.add_garch_feature(feature_frame, store_model=True)
        feature_frame, anomaly_summary = self.add_anomaly_detection(feature_frame, fit=True)
        feature_frame, risk_summary = self.add_risk_scoring(feature_frame, fit=True)

        risk_frame = feature_frame.dropna(subset=["risk_score"]).copy()
        event_summary, event_detail = self.run_event_analysis(risk_frame)
        figures = self.create_visualizations(risk_frame, event_summary, event_detail)

        realtime_summary = self.simulate_realtime_monitor() if run_realtime else {
            "status": "skipped",
            "reason": "Real-time simulation was not requested.",
        }

        business_explanation = self.generate_business_explanation(
            prepared_data=prepared_data,
            risk_frame=risk_frame,
            diagnostics=diagnostics,
            garch_summary=garch_summary,
            anomaly_summary=anomaly_summary,
            risk_summary=risk_summary,
            event_summary=event_summary,
            realtime_summary=realtime_summary,
        )

        self.persist_outputs(
            prepared_data=prepared_data,
            diagnostics=diagnostics,
            risk_frame=risk_frame,
            event_summary=event_summary,
            event_detail=event_detail,
            garch_summary=garch_summary,
            anomaly_summary=anomaly_summary,
            risk_summary=risk_summary,
            realtime_summary=realtime_summary,
            business_explanation=business_explanation,
            figures=figures,
        )

        return {
            "prepared_data": prepared_data,
            "diagnostics": diagnostics,
            "risk_frame": risk_frame,
            "event_summary": event_summary,
            "event_detail": event_detail,
            "garch_summary": garch_summary,
            "anomaly_summary": anomaly_summary,
            "risk_summary": risk_summary,
            "realtime_summary": realtime_summary,
            "business_explanation": business_explanation,
            "figures": figures,
            "notes": self.notes,
        }

    def prepare_data(self) -> pd.DataFrame:
        series_map: dict[str, pd.Series] = {}
        local_sources = {
            "NIFTY_Close": self._load_price_series(self.config.nifty_path, "NIFTY_Close"),
            "USDINR_Close": self._load_price_series(self.config.usdinr_path, "USDINR_Close"),
            "SENSEX_Close": self._load_benchmark_series(),
        }

        for label, local_series in local_sources.items():
            combined = local_series
            if self.config.supplement_with_yfinance:
                remote_series = self._download_price_series(
                    tickers=self.config.ticker_map.get(label, ()),
                    label=label,
                    start=self.config.history_start,
                    end=self.config.history_end,
                )
                if local_series is not None and remote_series is not None:
                    combined = local_series.combine_first(remote_series).sort_index()
                    if len(combined) > len(local_series):
                        self._record_note(
                            f"{label} was extended with yfinance history beyond the local CSV coverage."
                        )
                elif combined is None:
                    combined = remote_series

            if combined is not None and not combined.empty:
                series_map[label] = combined.sort_index()
            elif label != "SENSEX_Close":
                raise FileNotFoundError(
                    f"Required input for {label} is unavailable. "
                    f"Check the local CSV or yfinance connectivity."
                )
            else:
                self._record_note(
                    "SENSEX benchmark series is unavailable locally and could not be downloaded. "
                    "The rest of the pipeline will continue without the benchmark return column."
                )

        market = pd.concat(series_map.values(), axis=1).sort_index()
        market = market[~market.index.duplicated(keep="last")]

        required_close_cols = list(series_map.keys())
        market = market.dropna(subset=required_close_cols).copy()
        for close_col in required_close_cols:
            return_col = close_col.replace("_Close", "_Return")
            market[return_col] = 100 * np.log(market[close_col] / market[close_col].shift(1))

        required_return_cols = [
            col for col in ["NIFTY_Return", "SENSEX_Return", "USDINR_Return"] if col in market.columns
        ]
        market = market.dropna(subset=required_return_cols).copy()

        reference = self._load_reference_returns()
        if reference is not None:
            market = market.join(reference, how="left")
            for calc_col, ref_col, gap_col in [
                ("NIFTY_Return", "Reference_NIFTY_Return", "NIFTY_Return_Validation_Gap"),
                ("USDINR_Return", "Reference_USDINR_Return", "USDINR_Return_Validation_Gap"),
            ]:
                if calc_col in market.columns and ref_col in market.columns:
                    market[gap_col] = market[calc_col] - market[ref_col]

        market.index.name = "Date"
        return market

    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        feature_frame = data.copy()
        short_window, long_window = self.config.rolling_windows

        feature_frame[f"NIFTY_Rolling_Vol_{short_window}"] = (
            feature_frame["NIFTY_Return"].rolling(short_window).std()
        )
        feature_frame[f"NIFTY_Rolling_Vol_{long_window}"] = (
            feature_frame["NIFTY_Return"].rolling(long_window).std()
        )

        rolling_mean = feature_frame["NIFTY_Return"].rolling(long_window).mean()
        rolling_std = feature_frame["NIFTY_Return"].rolling(long_window).std()
        feature_frame["NIFTY_Return_ZScore"] = (
            feature_frame["NIFTY_Return"] - rolling_mean
        ) / rolling_std
        feature_frame["NIFTY_Absolute_ZScore"] = feature_frame["NIFTY_Return_ZScore"].abs()

        feature_frame[f"NIFTY_MA_{short_window}"] = feature_frame["NIFTY_Close"].rolling(short_window).mean()
        feature_frame[f"NIFTY_MA_{long_window}"] = feature_frame["NIFTY_Close"].rolling(long_window).mean()
        feature_frame[f"NIFTY_Deviation_From_MA_{short_window}"] = 100 * (
            feature_frame["NIFTY_Close"] - feature_frame[f"NIFTY_MA_{short_window}"]
        ) / feature_frame[f"NIFTY_MA_{short_window}"]
        feature_frame[f"NIFTY_Deviation_From_MA_{long_window}"] = 100 * (
            feature_frame["NIFTY_Close"] - feature_frame[f"NIFTY_MA_{long_window}"]
        ) / feature_frame[f"NIFTY_MA_{long_window}"]
        feature_frame["NIFTY_Volatility_Ratio"] = (
            feature_frame[f"NIFTY_Rolling_Vol_{short_window}"]
            / feature_frame[f"NIFTY_Rolling_Vol_{long_window}"]
        )

        if "SENSEX_Return" in feature_frame.columns:
            feature_frame["Market_Spread_Return"] = (
                feature_frame["NIFTY_Return"] - feature_frame["SENSEX_Return"]
            )

        return feature_frame

    def add_garch_feature(
        self,
        data: pd.DataFrame,
        store_model: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        frame = data.copy()
        series = frame["NIFTY_Return"].dropna()
        if len(series) < 60:
            raise ValueError("At least 60 return observations are required for stable GARCH fitting.")

        garch = arch_model(
            series,
            mean="Constant",
            vol="GARCH",
            p=1,
            q=1,
            dist="normal",
            rescale=False,
        )
        result = garch.fit(disp="off")
        if store_model:
            self.garch_result = result

        frame["GARCH_Volatility"] = result.conditional_volatility.reindex(frame.index)
        frame["Volatility_Gap_vs_Roll20"] = (
            frame["GARCH_Volatility"] - frame[f"NIFTY_Rolling_Vol_{self.config.rolling_windows[1]}"]
        )
        frame["GARCH_to_Roll20_Ratio"] = (
            frame["GARCH_Volatility"] / frame[f"NIFTY_Rolling_Vol_{self.config.rolling_windows[1]}"]
        )

        params = result.params
        summary = {
            "model": "GARCH(1,1)",
            "omega": float(params.get("omega", np.nan)),
            "alpha": float(params.get("alpha[1]", np.nan)),
            "beta": float(params.get("beta[1]", np.nan)),
            "persistence": float(params.get("alpha[1]", 0.0) + params.get("beta[1]", 0.0)),
            "aic": float(result.aic),
            "bic": float(result.bic),
            "volatility_correlation_with_roll20": float(
                frame[[f"NIFTY_Rolling_Vol_{self.config.rolling_windows[1]}", "GARCH_Volatility"]]
                .dropna()
                .corr()
                .iloc[0, 1]
            ),
        }
        return frame, summary

    def run_diagnostics(self, data: pd.DataFrame) -> pd.DataFrame:
        diagnostics: list[dict[str, Any]] = []
        for column in ["NIFTY_Return", "SENSEX_Return", "USDINR_Return"]:
            if column not in data.columns:
                continue
            series = data[column].dropna()
            if len(series) < 30:
                continue

            lag_count = max(1, min(10, len(series) // 5))
            adf_stat, adf_pvalue, used_lag, nobs, *_ = adfuller(series, autolag="AIC")
            ljung_box = acorr_ljungbox(series, lags=[lag_count], return_df=True)
            arch_lm = het_arch(series, nlags=lag_count)

            diagnostics.append(
                {
                    "Series": column,
                    "ADF_Statistic": float(adf_stat),
                    "ADF_pvalue": float(adf_pvalue),
                    "Used_Lag": int(used_lag),
                    "Observations": int(nobs),
                    "LjungBox_Lag": int(lag_count),
                    "LjungBox_pvalue": float(ljung_box["lb_pvalue"].iloc[0]),
                    "ARCH_LM_pvalue": float(arch_lm[1]),
                    "Stationary_At_5pct": bool(adf_pvalue < 0.05),
                    "ARCH_Effect_At_5pct": bool(arch_lm[1] < 0.05),
                }
            )

        return pd.DataFrame(diagnostics)

    def add_anomaly_detection(
        self,
        data: pd.DataFrame,
        fit: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        frame = data.copy()

        if fit or not self.model_features:
            self.model_features = self._select_model_features(frame)

        model_frame = frame.dropna(subset=self.model_features).copy()
        if model_frame.empty:
            raise ValueError("No complete rows are available for anomaly detection after feature engineering.")

        if fit:
            self.anomaly_scaler = StandardScaler()
            scaled = self.anomaly_scaler.fit_transform(model_frame[self.model_features])
            self.anomaly_model = IsolationForest(
                contamination=self.config.anomaly_contamination,
                random_state=self.config.random_state,
                n_estimators=300,
            )
            predictions = self.anomaly_model.fit_predict(scaled)
            scores = -self.anomaly_model.score_samples(scaled)
        else:
            if self.anomaly_scaler is None or self.anomaly_model is None:
                raise ValueError("Anomaly model is not fitted yet.")
            scaled = self.anomaly_scaler.transform(model_frame[self.model_features])
            predictions = self.anomaly_model.predict(scaled)
            scores = -self.anomaly_model.score_samples(scaled)

        frame["anomaly"] = 0
        frame["anomaly_score"] = np.nan
        frame.loc[model_frame.index, "anomaly"] = (predictions == -1).astype(int)
        frame.loc[model_frame.index, "anomaly_score"] = scores

        anomaly_rows = frame[frame["anomaly"] == 1].copy()
        summary = {
            "feature_columns": self.model_features,
            "anomaly_count": int(len(anomaly_rows)),
            "anomaly_rate": float(frame["anomaly"].mean()),
            "top_anomaly_dates": [
                ts.strftime("%Y-%m-%d") for ts in anomaly_rows["anomaly_score"].nlargest(5).index
            ],
        }
        return frame, summary

    def add_risk_scoring(
        self,
        data: pd.DataFrame,
        fit: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        frame = data.copy()
        valid_rows = frame.dropna(subset=["GARCH_Volatility", "NIFTY_Absolute_ZScore"]).copy()
        if valid_rows.empty:
            raise ValueError("Risk scoring cannot run because the GARCH or z-score columns are empty.")

        if fit:
            self.volatility_scaler = MinMaxScaler()
            self.zscore_scaler = MinMaxScaler()
            self.volatility_scaler.fit(valid_rows[["GARCH_Volatility"]])
            self.zscore_scaler.fit(valid_rows[["NIFTY_Absolute_ZScore"]])
        elif self.volatility_scaler is None or self.zscore_scaler is None:
            raise ValueError("Risk scorers are not fitted yet.")

        vol_component = np.clip(
            self.volatility_scaler.transform(valid_rows[["GARCH_Volatility"]]).ravel(),
            0,
            1,
        )
        z_component = np.clip(
            self.zscore_scaler.transform(valid_rows[["NIFTY_Absolute_ZScore"]]).ravel(),
            0,
            1,
        )
        anomaly_component = valid_rows["anomaly"].fillna(0).astype(float).to_numpy()

        valid_rows["volatility_component"] = vol_component
        valid_rows["zscore_component"] = z_component
        valid_rows["risk_score"] = (
            0.5 * valid_rows["volatility_component"]
            + 0.3 * anomaly_component
            + 0.2 * valid_rows["zscore_component"]
        )
        valid_rows["risk_category"] = pd.cut(
            valid_rows["risk_score"],
            bins=[-0.001, 0.33, 0.66, 1.001],
            labels=["Low Risk", "Medium Risk", "High Risk"],
            include_lowest=True,
        ).astype("string")

        frame["volatility_component"] = np.nan
        frame["zscore_component"] = np.nan
        frame["risk_score"] = np.nan
        frame["risk_category"] = pd.Series(pd.NA, index=frame.index, dtype="string")

        for column in ["volatility_component", "zscore_component", "risk_score", "risk_category"]:
            frame.loc[valid_rows.index, column] = valid_rows[column]

        latest = valid_rows.iloc[-1]
        summary = {
            "latest_risk_score": float(latest["risk_score"]),
            "latest_risk_category": str(latest["risk_category"]),
            "high_risk_share": float((valid_rows["risk_category"] == "High Risk").mean()),
            "medium_risk_share": float((valid_rows["risk_category"] == "Medium Risk").mean()),
            "low_risk_share": float((valid_rows["risk_category"] == "Low Risk").mean()),
        }
        return frame, summary

    def run_event_analysis(self, data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        summary_rows: list[dict[str, Any]] = []
        detail_frames: list[pd.DataFrame] = []
        trading_index = pd.DatetimeIndex(data.index).sort_values()

        for event_year, official_date in self.config.election_dates.items():
            for window_name, window in self.config.event_windows.items():
                support = self._check_window_support(trading_index, official_date, window)
                base_summary = {
                    "Event_Year": event_year,
                    "Window": window_name,
                    "Official_Event_Date": official_date,
                    "Trading_Event_Date": (
                        support["trading_event_date"].strftime("%Y-%m-%d")
                        if support["trading_event_date"] is not None
                        else None
                    ),
                    "Supported": support["supported"],
                    "Reason": support["reason"],
                }

                if not support["supported"] or support["trading_event_date"] is None:
                    summary_rows.append(base_summary)
                    continue

                event_loc = trading_index.get_loc(support["trading_event_date"])
                event_slice = self._slice_relative(data, event_loc, window[0], window[1]).copy()
                event_slice["relative_day"] = np.arange(window[0], window[1] + 1)
                event_slice["event_year"] = event_year
                event_slice["event_window"] = window_name
                detail_frames.append(event_slice.reset_index())

                pre_event = self._slice_relative(
                    data,
                    event_loc,
                    max(-20, -event_loc),
                    -1,
                )
                baseline_vol = pre_event["GARCH_Volatility"].mean()
                peak_vol = event_slice["GARCH_Volatility"].max()
                vol_spike_pct = np.nan
                if pd.notna(baseline_vol) and baseline_vol != 0:
                    vol_spike_pct = ((peak_vol - baseline_vol) / baseline_vol) * 100

                anomaly_count = int(event_slice["anomaly"].sum())
                anomaly_frequency = float(event_slice["anomaly"].mean())
                avg_risk = float(event_slice["risk_score"].mean())
                peak_risk = float(event_slice["risk_score"].max())

                summary_rows.append(
                    {
                        **base_summary,
                        "Anomaly_Count": anomaly_count,
                        "Anomaly_Frequency": anomaly_frequency,
                        "Peak_GARCH_Volatility": float(peak_vol),
                        "Baseline_PreEvent_Volatility": float(baseline_vol) if pd.notna(baseline_vol) else np.nan,
                        "Volatility_Spike_Pct": float(vol_spike_pct) if pd.notna(vol_spike_pct) else np.nan,
                        "Average_Risk_Score": avg_risk,
                        "Peak_Risk_Score": peak_risk,
                        "NIFTY_Cumulative_Return": float(event_slice["NIFTY_Return"].sum()),
                        "USDINR_Cumulative_Return": float(event_slice["USDINR_Return"].sum())
                        if "USDINR_Return" in event_slice.columns
                        else np.nan,
                        "Insight": self._build_event_insight(
                            anomaly_frequency=anomaly_frequency,
                            peak_risk=peak_risk,
                            vol_spike_pct=vol_spike_pct,
                        ),
                    }
                )

        event_summary = pd.DataFrame(summary_rows)
        event_detail = pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame()
        return event_summary, event_detail

    def create_visualizations(
        self,
        data: pd.DataFrame,
        event_summary: pd.DataFrame,
        event_detail: pd.DataFrame,
    ) -> dict[str, str]:
        figures = {
            "returns_anomalies": self._plot_returns_with_anomalies(data),
            "volatility_comparison": self._plot_volatility_comparison(data),
            "risk_score": self._plot_risk_score(data),
            "event_window": self._plot_event_window(event_summary, event_detail),
        }
        return figures

    def simulate_realtime_monitor(self) -> dict[str, Any]:
        try:
            end_ts = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
            start_ts = end_ts - pd.Timedelta(days=self.config.realtime_lookback_days)

            realtime_nifty = self._download_price_series(
                self.config.ticker_map["NIFTY_Close"],
                "NIFTY_Close",
                start=start_ts.strftime("%Y-%m-%d"),
                end=end_ts.strftime("%Y-%m-%d"),
            )
            realtime_sensex = self._download_price_series(
                self.config.ticker_map["SENSEX_Close"],
                "SENSEX_Close",
                start=start_ts.strftime("%Y-%m-%d"),
                end=end_ts.strftime("%Y-%m-%d"),
            )
            realtime_fx = self._download_price_series(
                self.config.ticker_map["USDINR_Close"],
                "USDINR_Close",
                start=start_ts.strftime("%Y-%m-%d"),
                end=end_ts.strftime("%Y-%m-%d"),
            )

            if realtime_nifty is None or realtime_fx is None:
                return {
                    "status": "unavailable",
                    "reason": "Unable to fetch the latest NIFTY or USD/INR series from yfinance.",
                }

            realtime_series = [realtime_nifty, realtime_fx]
            if realtime_sensex is not None:
                realtime_series.append(realtime_sensex)

            realtime_frame = pd.concat(realtime_series, axis=1).sort_index()
            required_cols = [col for col in ["NIFTY_Close", "SENSEX_Close", "USDINR_Close"] if col in realtime_frame.columns]
            realtime_frame = realtime_frame.dropna(subset=required_cols).copy()
            for close_col in required_cols:
                return_col = close_col.replace("_Close", "_Return")
                realtime_frame[return_col] = 100 * np.log(realtime_frame[close_col] / realtime_frame[close_col].shift(1))
            required_returns = [col for col in ["NIFTY_Return", "USDINR_Return"] if col in realtime_frame.columns]
            realtime_frame = realtime_frame.dropna(subset=required_returns).copy()
            realtime_frame.index.name = "Date"

            realtime_frame = self.engineer_features(realtime_frame)
            realtime_frame, _ = self.add_garch_feature(realtime_frame, store_model=False)
            realtime_frame, _ = self.add_anomaly_detection(realtime_frame, fit=False)
            realtime_frame, _ = self.add_risk_scoring(realtime_frame, fit=False)

            scored = realtime_frame.dropna(subset=["risk_score"]).copy()
            if scored.empty:
                return {
                    "status": "unavailable",
                    "reason": "Real-time data did not produce enough complete rows after feature engineering.",
                }

            latest = scored.iloc[-1]
            fraud_alert = bool(latest["anomaly"] == 1 or latest["risk_category"] == "High Risk")
            return {
                "status": "available",
                "timestamp": latest.name.strftime("%Y-%m-%d"),
                "current_risk_score": float(latest["risk_score"]),
                "risk_category": str(latest["risk_category"]),
                "fraud_alert": fraud_alert,
                "anomaly": int(latest["anomaly"]),
                "nifty_return": float(latest["NIFTY_Return"]),
                "usdinr_return": float(latest["USDINR_Return"]),
                "garch_volatility": float(latest["GARCH_Volatility"]),
            }
        except Exception as exc:
            return {
                "status": "unavailable",
                "reason": f"Real-time simulation failed: {exc}",
            }

    def generate_business_explanation(
        self,
        prepared_data: pd.DataFrame,
        risk_frame: pd.DataFrame,
        diagnostics: pd.DataFrame,
        garch_summary: dict[str, Any],
        anomaly_summary: dict[str, Any],
        risk_summary: dict[str, Any],
        event_summary: pd.DataFrame,
        realtime_summary: dict[str, Any],
    ) -> str:
        supported_events = event_summary[event_summary.get("Supported", False) == True].copy()
        top_event_line = "No election window had enough observations in the available data."
        if not supported_events.empty:
            top_event = supported_events.sort_values(
                ["Peak_Risk_Score", "Anomaly_Frequency"],
                ascending=False,
            ).iloc[0]
            top_event_line = (
                f"The most stressed supported event window was {int(top_event['Event_Year'])} "
                f"{top_event['Window']} with peak risk {top_event['Peak_Risk_Score']:.2f} "
                f"and anomaly frequency {top_event['Anomaly_Frequency']:.2%}."
            )

        latest_row = risk_frame.iloc[-1]
        diagnostics_line = "Diagnostics could not be computed from the available data."
        if not diagnostics.empty:
            stationary_share = diagnostics["Stationary_At_5pct"].mean()
            arch_share = diagnostics["ARCH_Effect_At_5pct"].mean()
            diagnostics_line = (
                f"Return diagnostics show {stationary_share:.0%} of available series are stationary at the 5% level "
                f"and {arch_share:.0%} exhibit ARCH effects, supporting volatility-model use."
            )

        realtime_line = "Real-time simulation was not available."
        if realtime_summary.get("status") == "available":
            realtime_line = (
                f"Real-time monitor output for {realtime_summary['timestamp']}: "
                f"risk score {realtime_summary['current_risk_score']:.2f}, "
                f"category {realtime_summary['risk_category']}, "
                f"fraud alert {'Yes' if realtime_summary['fraud_alert'] else 'No'}."
            )
        elif realtime_summary.get("status") == "unavailable":
            realtime_line = f"Real-time simulation was unavailable because {realtime_summary['reason']}"

        note_block = ""
        if self.notes:
            note_block = "\n".join(f"- {note}" for note in self.notes)
            note_block = f"\n## Implementation Notes\n{note_block}\n"

        explanation = f"""# Exam-Ready Business Explanation

## Problem Statement
The project studies how Indian general-election outcomes influence stock-market stress, volatility transmission, and currency dynamics, then upgrades that academic analysis into a risk surveillance system. The objective is to detect unusual market conditions in near real time so a financial institution, brokerage, treasury desk, or market-surveillance team can react early to election-driven instability or suspicious price behavior.

## Methodology
1. Local NIFTY, USD/INR, and optional SENSEX data are aligned by trading date, sorted, and cleaned.
2. Log returns are calculated for each available market series to create a stable risk-analysis base.
3. Rolling volatility, rolling z-scores, moving averages, deviation-from-trend measures, and a short-vs-long volatility ratio are engineered as risk indicators.
4. A GARCH(1,1) model estimates conditional volatility so the system captures clustering and persistence in market shocks.
5. Isolation Forest flags unusual combinations of returns, volatility, and exchange-rate behavior as market anomalies.
6. A weighted risk-scoring layer converts the analytics into Low, Medium, and High risk categories for operational use.
7. Election-event windows are evaluated to measure anomaly concentration and volatility spikes around result announcements.
8. A real-time simulation layer uses yfinance to fetch the latest market data and generate a live fraud alert and current risk score.

## Models Used
- Statistical diagnostics: ADF, ARCH-LM, Ljung-Box
- Volatility model: GARCH(1,1)
- Unsupervised anomaly model: Isolation Forest with contamination = {self.config.anomaly_contamination:.2f}
- Risk scoring model: normalized weighted score = 0.5 * volatility + 0.3 * anomaly + 0.2 * z-score

## Results
The clean prepared dataset spans {prepared_data.index.min().strftime("%Y-%m-%d")} to {prepared_data.index.max().strftime("%Y-%m-%d")} with {len(prepared_data):,} aligned observations.

{diagnostics_line}

The fitted GARCH model produced persistence of {garch_summary['persistence']:.4f}, indicating how strongly volatility shocks carry forward across sessions. The 20-day rolling volatility and GARCH volatility have correlation {garch_summary['volatility_correlation_with_roll20']:.4f}, which helps compare simple realized volatility with model-based conditional volatility.

The anomaly engine detected {anomaly_summary['anomaly_count']} anomalous sessions, equal to {anomaly_summary['anomaly_rate']:.2%} of the scored sample. In financial context, these anomalies represent sessions where returns, volatility, and FX behavior depart materially from normal market structure. This does not prove fraud by itself; instead it acts as a surveillance trigger for potential manipulation, panic trading, information shocks, or election-driven repricing.

The latest historical observation in the feature store has risk score {risk_summary['latest_risk_score']:.2f} and category {risk_summary['latest_risk_category']}. The most recent scored market day in the dataset is {latest_row.name.strftime("%Y-%m-%d")}.

{top_event_line}

{realtime_line}

## Business Impact
This upgraded project is useful in both risk management and fraud analytics:

- Risk management: it highlights volatility escalation early, helping treasury and trading teams rebalance exposure during politically sensitive periods.
- Fraud detection: anomaly flags identify suspicious return-volatility combinations that merit analyst review for spoofing, rumor-led trading, coordinated dumping, or abnormal cross-market behavior.
- Operations: the dashboard converts technical model outputs into monitoring-friendly KPIs such as risk score, anomaly count, and alert status.
- Placement value: the project now combines econometrics, machine learning, event analysis, and dashboard deployment, making it stronger for analytics, risk, surveillance, and quant-oriented interviews.
{note_block}"""
        return explanation.strip() + "\n"

    def persist_outputs(
        self,
        prepared_data: pd.DataFrame,
        diagnostics: pd.DataFrame,
        risk_frame: pd.DataFrame,
        event_summary: pd.DataFrame,
        event_detail: pd.DataFrame,
        garch_summary: dict[str, Any],
        anomaly_summary: dict[str, Any],
        risk_summary: dict[str, Any],
        realtime_summary: dict[str, Any],
        business_explanation: str,
        figures: dict[str, str],
    ) -> None:
        prepared_data.reset_index().to_csv(
            self.config.output_dir / "prepared_market_data.csv",
            index=False,
        )
        diagnostics.to_csv(self.config.output_dir / "diagnostics_summary.csv", index=False)
        risk_frame.reset_index().to_csv(
            self.config.output_dir / "risk_fraud_feature_store.csv",
            index=False,
        )
        event_summary.to_csv(self.config.output_dir / "event_summary.csv", index=False)
        if not event_detail.empty:
            event_detail.to_csv(self.config.output_dir / "event_detail.csv", index=False)

        metadata = {
            "garch_summary": garch_summary,
            "anomaly_summary": anomaly_summary,
            "risk_summary": risk_summary,
            "realtime_summary": realtime_summary,
            "figures": figures,
            "notes": self.notes,
        }
        (self.config.output_dir / "analysis_metadata.json").write_text(
            json.dumps(metadata, indent=2, default=str),
            encoding="utf-8",
        )
        (self.config.reports_dir / "generated_exam_explanation.md").write_text(
            business_explanation,
            encoding="utf-8",
        )

    def _plot_returns_with_anomalies(self, data: pd.DataFrame) -> str:
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.plot(data.index, data["NIFTY_Return"], color="#0f4c81", linewidth=1.6, label="NIFTY Returns")
        anomaly_points = data[data["anomaly"] == 1]
        ax.scatter(
            anomaly_points.index,
            anomaly_points["NIFTY_Return"],
            color="#c0392b",
            s=55,
            label="Anomaly",
            zorder=3,
        )
        for official_date in self.config.election_dates.values():
            event_ts = pd.Timestamp(official_date)
            if data.index.min() <= event_ts <= data.index.max():
                ax.axvline(event_ts, color="#7f8c8d", linestyle="--", linewidth=0.9, alpha=0.7)
        ax.set_title("NIFTY Returns with Election-Era Anomalies Highlighted")
        ax.set_xlabel("Date")
        ax.set_ylabel("Log Return (%)")
        ax.legend()
        return self._save_figure(fig, "nifty_returns_with_anomalies.png")

    def _plot_volatility_comparison(self, data: pd.DataFrame) -> str:
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.plot(
            data.index,
            data[f"NIFTY_Rolling_Vol_{self.config.rolling_windows[0]}"],
            color="#1abc9c",
            linewidth=1.7,
            label=f"{self.config.rolling_windows[0]}-Day Rolling Vol",
        )
        ax.plot(
            data.index,
            data[f"NIFTY_Rolling_Vol_{self.config.rolling_windows[1]}"],
            color="#f39c12",
            linewidth=1.7,
            label=f"{self.config.rolling_windows[1]}-Day Rolling Vol",
        )
        ax.plot(
            data.index,
            data["GARCH_Volatility"],
            color="#8e44ad",
            linewidth=2.0,
            label="GARCH Volatility",
        )
        ax.set_title("Rolling Volatility vs GARCH Conditional Volatility")
        ax.set_xlabel("Date")
        ax.set_ylabel("Volatility")
        ax.legend()
        return self._save_figure(fig, "volatility_comparison.png")

    def _plot_risk_score(self, data: pd.DataFrame) -> str:
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.plot(data.index, data["risk_score"], color="#2c3e50", linewidth=2.0, label="Risk Score")
        ax.fill_between(data.index, data["risk_score"], color="#5dade2", alpha=0.25)
        ax.axhline(0.33, color="#27ae60", linestyle="--", linewidth=1, label="Low/Medium")
        ax.axhline(0.66, color="#c0392b", linestyle="--", linewidth=1, label="Medium/High")
        ax.set_title("Composite Risk Score Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Risk Score (0-1)")
        ax.legend()
        return self._save_figure(fig, "risk_score_over_time.png")

    def _plot_event_window(
        self,
        event_summary: pd.DataFrame,
        event_detail: pd.DataFrame,
    ) -> str:
        fig, ax = plt.subplots(figsize=(16, 7))

        if event_detail.empty:
            ax.text(
                0.5,
                0.5,
                "No supported election windows in the current data coverage.",
                ha="center",
                va="center",
                fontsize=16,
            )
            ax.axis("off")
            return self._save_figure(fig, "event_window_visualization.png")

        heatmap_frame = (
            event_detail.assign(Event_Label=lambda df: df["event_year"].astype(str) + " | " + df["event_window"])
            .pivot_table(index="Event_Label", columns="relative_day", values="risk_score", aggfunc="mean")
            .sort_index()
        )

        sns.heatmap(heatmap_frame, cmap="YlOrRd", linewidths=0.25, ax=ax)
        ax.set_title("Election Event Window Risk Heatmap")
        ax.set_xlabel("Trading Day Relative to Result")
        ax.set_ylabel("Election Window")
        return self._save_figure(fig, "event_window_visualization.png")

    def _save_figure(self, fig: plt.Figure, filename: str) -> str:
        path = self.config.figures_dir / filename
        fig.tight_layout()
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return str(path)

    def _load_price_series(self, path: Path, label: str) -> pd.Series | None:
        if path is None or not Path(path).exists():
            return None

        df = pd.read_csv(path)
        if df.empty:
            return None

        date_col = "Date" if "Date" in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        value_col = next((col for col in ["Adj Close", "Close", "Price", label] if col in df.columns), None)
        if value_col is None:
            numeric_cols = [col for col in df.columns if col != date_col]
            for candidate in numeric_cols:
                df[candidate] = pd.to_numeric(df[candidate], errors="coerce")
            value_col = next((col for col in numeric_cols if df[col].notna().any()), None)

        if value_col is None:
            raise ValueError(f"No usable numeric price column was found in {path}.")

        series = (
            df[[date_col, value_col]]
            .dropna()
            .rename(columns={date_col: "Date", value_col: label})
            .set_index("Date")[label]
            .sort_index()
        )
        series.index = pd.to_datetime(series.index).tz_localize(None)
        return series.astype(float)

    def _load_benchmark_series(self) -> pd.Series | None:
        search_paths: list[Path] = []
        if self.config.sensex_path is not None:
            search_paths.append(Path(self.config.sensex_path))

        for filename in self.config.candidate_sensex_files:
            search_paths.append(self.config.data_dir / filename)
            search_paths.append(Path.home() / "Downloads" / filename)

        for candidate in search_paths:
            if candidate.exists():
                return self._load_price_series(candidate, "SENSEX_Close")
        return None

    def _load_reference_returns(self) -> pd.DataFrame | None:
        path = self.config.aligned_returns_path
        if path is None or not Path(path).exists():
            return None

        df = pd.read_csv(path)
        if df.empty or "Date" not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        keep_cols = {
            "NIFTY_Return": "Reference_NIFTY_Return",
            "USDINR_Return": "Reference_USDINR_Return",
            "NIFTY_Volatility": "Reference_NIFTY_Volatility",
            "USDINR_Volatility": "Reference_USDINR_Volatility",
        }
        available = [col for col in keep_cols if col in df.columns]
        if not available:
            return None
        reference = (
            df[["Date", *available]]
            .rename(columns=keep_cols)
            .set_index("Date")
            .sort_index()
        )
        reference.index = pd.to_datetime(reference.index).tz_localize(None)
        return reference

    def _download_price_series(
        self,
        tickers: tuple[str, ...],
        label: str,
        start: str,
        end: str,
    ) -> pd.Series | None:
        if not tickers:
            return None

        last_error: Exception | None = None
        for ticker in tickers:
            try:
                raw = yf.download(
                    ticker,
                    start=start,
                    end=end,
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
                if raw is None or raw.empty:
                    continue

                if isinstance(raw.columns, pd.MultiIndex):
                    close_series = None
                    for candidate in ["Adj Close", "Close"]:
                        if (candidate, ticker) in raw.columns:
                            close_series = raw[(candidate, ticker)]
                            break
                    if close_series is None:
                        close_series = raw.xs("Close", axis=1, level=0).squeeze()
                else:
                    close_col = "Adj Close" if "Adj Close" in raw.columns else "Close"
                    close_series = raw[close_col]

                close_series = close_series.squeeze().dropna().rename(label)
                close_series.index = pd.to_datetime(close_series.index).tz_localize(None)
                return close_series.astype(float).sort_index()
            except Exception as exc:
                last_error = exc

        if last_error is not None:
            self._record_note(f"yfinance download failed for {label}: {last_error}")
        return None

    def _select_model_features(self, frame: pd.DataFrame) -> list[str]:
        features = [
            "NIFTY_Return",
            "USDINR_Return",
            f"NIFTY_Rolling_Vol_{self.config.rolling_windows[0]}",
            f"NIFTY_Rolling_Vol_{self.config.rolling_windows[1]}",
            "NIFTY_Volatility_Ratio",
            "NIFTY_Return_ZScore",
            "GARCH_Volatility",
        ]
        if "SENSEX_Return" in frame.columns:
            features.insert(1, "SENSEX_Return")
        if "Market_Spread_Return" in frame.columns:
            features.append("Market_Spread_Return")
        return features

    def _check_window_support(
        self,
        index: pd.DatetimeIndex,
        official_date: str,
        window: tuple[int, int],
    ) -> dict[str, Any]:
        official_ts = pd.Timestamp(official_date)
        try:
            trading_date = self._next_trading_day(index, official_ts)
        except ValueError:
            return {
                "supported": False,
                "trading_event_date": None,
                "reason": f"No trading session exists on or after {official_date}.",
            }

        loc = index.get_loc(trading_date)
        if loc + window[0] < 0:
            return {
                "supported": False,
                "trading_event_date": trading_date,
                "reason": f"Insufficient pre-event observations for window {window}.",
            }
        if loc + window[1] >= len(index):
            return {
                "supported": False,
                "trading_event_date": trading_date,
                "reason": f"Insufficient post-event observations for window {window}.",
            }
        return {
            "supported": True,
            "trading_event_date": trading_date,
            "reason": "ok",
        }

    def _next_trading_day(self, index: pd.DatetimeIndex, target: pd.Timestamp) -> pd.Timestamp:
        eligible = index[index >= target]
        if len(eligible) == 0:
            raise ValueError("No trading session exists on or after the target date.")
        return pd.Timestamp(eligible[0])

    def _slice_relative(
        self,
        data: pd.DataFrame,
        event_loc: int,
        start_offset: int,
        end_offset: int,
    ) -> pd.DataFrame:
        return data.iloc[event_loc + start_offset : event_loc + end_offset + 1].copy()

    def _build_event_insight(
        self,
        anomaly_frequency: float,
        peak_risk: float,
        vol_spike_pct: float | float,
    ) -> str:
        if pd.notna(vol_spike_pct) and anomaly_frequency >= 0.10 and peak_risk >= 0.66:
            return "Dense anomalies and a sharp volatility shock indicate a stressed election reaction window."
        if pd.notna(vol_spike_pct) and vol_spike_pct >= 25:
            return "Volatility increased materially even without a large anomaly cluster."
        if anomaly_frequency > 0:
            return "Isolated anomaly signals appeared during the election window."
        return "The election window was comparatively stable in the scored sample."

    def _record_note(self, message: str) -> None:
        if message not in self.notes:
            self.notes.append(message)
