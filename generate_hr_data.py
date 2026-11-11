"""Generate a SYNTHETIC HR dataset (employee records with attrition).

This is sample data so the project runs out of the box. It is NOT real company
data. To use real data, see the "Using real data" section of the README.

Run:  python data/generate_hr_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).with_name("hr_data_sample.csv")

# role -> (department, base monthly salary in INR)
ROLES = {
    "Software Engineer": ("Engineering", 65000),
    "Data Analyst": ("Engineering", 55000),
    "QA Engineer": ("Engineering", 45000),
    "DevOps Engineer": ("Engineering", 70000),
    "Sales Executive": ("Sales", 40000),
    "Sales Manager": ("Sales", 85000),
    "Accountant": ("Finance", 38000),
    "Financial Analyst": ("Finance", 55000),
    "Marketing Executive": ("Marketing", 42000),
    "Content Specialist": ("Marketing", 38000),
    "HR Executive": ("HR", 40000),
    "Recruiter": ("HR", 36000),
}
DEPT_WEIGHTS = {"Engineering": 0.40, "Sales": 0.25, "Finance": 0.15, "Marketing": 0.12, "HR": 0.08}


def make_dataset(n: int = 1500, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    department = rng.choice(list(DEPT_WEIGHTS), size=n, p=list(DEPT_WEIGHTS.values()))
    roles_by_dept = {d: [r for r, (dd, _) in ROLES.items() if dd == d] for d in DEPT_WEIGHTS}
    job_role = np.array([rng.choice(roles_by_dept[d]) for d in department])
    base = np.array([ROLES[r][1] for r in job_role], dtype=float)

    age = np.clip(rng.normal(34, 8, n).round(), 21, 60).astype(int)
    years_at = np.minimum(age - 21, rng.exponential(5, n).round().astype(int))
    since_promo = np.minimum(years_at, rng.exponential(2.2, n).round().astype(int))

    expected_income = base * (1 + 0.04 * years_at)
    income_noise = rng.normal(1.0, 0.12, n)
    income = (np.round(expected_income * income_noise / 500) * 500).astype(int)

    overtime = rng.random(n) < 0.28
    job_sat = rng.choice([1, 2, 3, 4], n, p=[0.15, 0.20, 0.35, 0.30])
    wlb = rng.choice([1, 2, 3, 4], n, p=[0.10, 0.25, 0.50, 0.15])
    perf = rng.choice([1, 2, 3, 4], n, p=[0.02, 0.08, 0.60, 0.30])
    edu = rng.choice([1, 2, 3, 4, 5], n, p=[0.10, 0.20, 0.40, 0.25, 0.05])
    distance = rng.integers(1, 31, n)
    gender = rng.choice(["Male", "Female"], n, p=[0.55, 0.45])

    # Attrition probability: higher with overtime, low satisfaction/work-life
    # balance, short tenure, long time without promotion, low relative pay,
    # long commute, and (slightly) in Sales.
    logit = (
        -2.6
        + 0.9 * overtime
        + 0.6 * (job_sat <= 2)
        + 0.4 * (wlb <= 2)
        + 0.5 * (years_at <= 2)
        + 0.4 * (since_promo >= 5)
        - 1.5 * (income_noise - 1.0)
        + 0.02 * (distance - 15)
        + 0.4 * (department == "Sales")
    )
    attrition = rng.random(n) < 1 / (1 + np.exp(-logit))

    return pd.DataFrame({
        "EmployeeID": [f"E{i:04d}" for i in range(1, n + 1)],
        "Department": department,
        "JobRole": job_role,
        "Gender": gender,
        "Age": age,
        "EducationLevel": edu,
        "MonthlyIncome": income,
        "YearsAtCompany": years_at,
        "YearsSinceLastPromotion": since_promo,
        "OverTime": np.where(overtime, "Yes", "No"),
        "DistanceFromHome": distance,
        "JobSatisfaction": job_sat,
        "WorkLifeBalance": wlb,
        "PerformanceRating": perf,
        "Attrition": np.where(attrition, "Yes", "No"),
    })


if __name__ == "__main__":
    data = make_dataset()
    data.to_csv(OUT, index=False)
    print(f"Wrote {len(data)} rows to {OUT}")
