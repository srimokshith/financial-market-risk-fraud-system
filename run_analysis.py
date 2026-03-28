from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from financial_market_risk_fraud import MarketRiskFraudSystem, ProjectConfig


def main() -> None:
    config = ProjectConfig()
    system = MarketRiskFraudSystem(config)
    results = system.run_full_analysis(run_realtime=True)

    risk_frame = results["risk_frame"]
    event_summary = results["event_summary"]
    latest = risk_frame.iloc[-1]

    print("Financial Market Risk and Fraud System completed.")
    print(f"Prepared data rows: {len(results['prepared_data'])}")
    print(f"Scored feature rows: {len(risk_frame)}")
    print(f"Latest historical risk score: {latest['risk_score']:.2f}")
    print(f"Latest historical risk category: {latest['risk_category']}")
    print(f"Total detected anomalies: {int(risk_frame['anomaly'].sum())}")

    supported_events = event_summary[event_summary.get("Supported", False) == True]
    print(f"Supported election windows: {len(supported_events)}")

    realtime = results["realtime_summary"]
    if realtime.get("status") == "available":
        print(
            "Real-time snapshot:",
            f"date={realtime['timestamp']},",
            f"risk_score={realtime['current_risk_score']:.2f},",
            f"risk_category={realtime['risk_category']},",
            f"fraud_alert={'Yes' if realtime['fraud_alert'] else 'No'}",
        )
    else:
        print("Real-time snapshot unavailable:", realtime.get("reason", "unknown reason"))

    if results["notes"]:
        print("\nImplementation notes:")
        for note in results["notes"]:
            print(f"- {note}")

    print("\nOutputs:")
    print(PROJECT_ROOT / "outputs" / "prepared_market_data.csv")
    print(PROJECT_ROOT / "outputs" / "risk_fraud_feature_store.csv")
    print(PROJECT_ROOT / "outputs" / "event_summary.csv")
    print(PROJECT_ROOT / "reports" / "generated_exam_explanation.md")


if __name__ == "__main__":
    main()
