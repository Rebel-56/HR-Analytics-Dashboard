"""Shared data loading and KPI calculations for the HR dashboard."""

from pathlib import Path

import pandas as pd

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "hr_data_sample.csv"

AGE_BINS = [0, 24, 34, 44, 54, 100]
AGE_LABELS = ["Under 25", "25-34", "35-44", "45-54", "55+"]
TENURE_BINS = [-1, 1, 4, 9, 100]
TENURE_LABELS = ["0-1 yrs", "2-4 yrs", "5-9 yrs", "10+ yrs"]


def load_data(path: Path = DEFAULT_DATA) -> pd.DataFrame:
    """Load the HR CSV and add helper columns."""
    df = pd.read_csv(path)
    df["Left"] = (df["Attrition"] == "Yes").astype(int)
    df["AgeGroup"] = pd.cut(df["Age"], AGE_BINS, labels=AGE_LABELS)
    df["TenureBand"] = pd.cut(df["YearsAtCompany"], TENURE_BINS, labels=TENURE_LABELS)
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    """Headline numbers for the dashboard cards."""
    total = len(df)
    if total == 0:
        return {"headcount": 0, "attrition_count": 0, "attrition_rate": 0.0,
                "avg_income": 0, "avg_tenure": 0.0, "avg_satisfaction": 0.0,
                "overtime_rate": 0.0}
    left = int(df["Left"].sum())
    return {
        "headcount": total,
        "attrition_count": left,
        "attrition_rate": round(100 * left / total, 1),
        "avg_income": int(round(df["MonthlyIncome"].mean())),
        "avg_tenure": round(float(df["YearsAtCompany"].mean()), 1),
        "avg_satisfaction": round(float(df["JobSatisfaction"].mean()), 2),
        "overtime_rate": round(float(100 * (df["OverTime"] == "Yes").mean()), 1),
    }


def attrition_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Headcount and attrition rate (%) for each value of `col`."""
    grouped = df.groupby(col, observed=True)["Left"].agg(["count", "mean"])
    out = grouped.rename(columns={"count": "headcount", "mean": "attrition_rate"}).reset_index()
    out["attrition_rate"] = (out["attrition_rate"] * 100).round(1)
    return out
