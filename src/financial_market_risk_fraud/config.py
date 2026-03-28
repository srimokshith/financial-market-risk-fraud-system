from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"


DEFAULT_ELECTION_DATES = {
    1999: "1999-10-06",
    2004: "2004-05-13",
    2009: "2009-05-16",
    2014: "2014-05-16",
    2019: "2019-05-23",
    2024: "2024-06-04",
}


@dataclass
class ProjectConfig:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    output_dir: Path = OUTPUT_DIR
    figures_dir: Path = FIGURES_DIR
    reports_dir: Path = REPORTS_DIR
    nifty_path: Path = DATA_DIR / "NIFTY_50.csv"
    usdinr_path: Path = DATA_DIR / "USD_INR.csv"
    aligned_returns_path: Path = DATA_DIR / "Aligned_Returns.csv"
    sensex_path: Path | None = None
    candidate_sensex_files: tuple[str, ...] = ("SENSEX.csv", "BSE_SENSEX.csv", "SENSEX_30.csv")
    history_start: str = "1998-01-01"
    history_end: str = field(default_factory=lambda: (date.today() + timedelta(days=1)).isoformat())
    rolling_windows: tuple[int, int] = (10, 20)
    anomaly_contamination: float = 0.01
    random_state: int = 42
    supplement_with_yfinance: bool = True
    realtime_lookback_days: int = 365
    election_dates: dict[int, str] = field(default_factory=lambda: DEFAULT_ELECTION_DATES.copy())
    event_windows: dict[str, tuple[int, int]] = field(
        default_factory=lambda: {
            "Short (-5 to +5)": (-5, 5),
            "Long (-20 to +40)": (-20, 40),
        }
    )
    ticker_map: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "NIFTY_Close": ("^NSEI",),
            "SENSEX_Close": ("^BSESN",),
            "USDINR_Close": ("INR=X", "USDINR=X"),
        }
    )
