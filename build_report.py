"""Build a self-contained HTML dashboard and a PNG preview from the HR data.

Run:  python src/build_report.py
      python src/build_report.py --data path/to/your.csv

Open outputs/hr_dashboard.html in any browser.
"""

import argparse
import base64
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kpis import DEFAULT_DATA, attrition_rate_by, compute_kpis, load_data

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
BLUE, ORANGE = "#2563eb", "#ea580c"


# ---------------------------------------------------------------- charts
def bar_rate(col: str, title: str):
    def draw(ax, df):
        d = attrition_rate_by(df, col)
        bars = ax.bar(d[col].astype(str), d["attrition_rate"], color=BLUE)
        ax.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel("Attrition rate (%)")
        ax.set_ylim(0, max(d["attrition_rate"].max() * 1.25, 1))
        ax.axhline(df["Left"].mean() * 100, color=ORANGE, ls="--", lw=1, label="Company average")
        ax.legend(fontsize=8, loc="upper right")
        ax.tick_params(axis="x", labelsize=8)
    return draw


def draw_income_by_role(ax, df):
    d = df.groupby("JobRole")["MonthlyIncome"].mean().sort_values() / 1000
    bars = ax.barh(d.index, d.values, color=BLUE)
    ax.bar_label(bars, fmt="%.0fk", padding=2, fontsize=8)
    ax.set_title("Average monthly income by role (INR)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Thousands of INR")
    ax.tick_params(axis="y", labelsize=8)
    ax.set_xlim(0, d.max() * 1.15)


CHARTS = [
    ("attrition_by_department", bar_rate("Department", "Attrition by department")),
    ("attrition_by_overtime", bar_rate("OverTime", "Attrition: overtime vs no overtime")),
    ("attrition_by_age_group", bar_rate("AgeGroup", "Attrition by age group")),
    ("attrition_by_tenure", bar_rate("TenureBand", "Attrition by tenure")),
    ("attrition_by_satisfaction", bar_rate("JobSatisfaction", "Attrition by job satisfaction (1 low - 4 high)")),
    ("income_by_role", draw_income_by_role),
]


def render_png(draw, df) -> bytes:
    fig, ax = plt.subplots(figsize=(6.5, 4))
    draw(ax, df)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    return buf.getvalue()


# -------------------------------------------------------------- insights
def build_insights(df) -> list[str]:
    """Plain-English findings computed from the data (nothing hard-coded)."""
    overall = df["Left"].mean() * 100
    insights = []

    dept = attrition_rate_by(df, "Department").sort_values("attrition_rate", ascending=False)
    top = dept.iloc[0]
    insights.append(
        f"{top['Department']} has the highest attrition at {top['attrition_rate']}% "
        f"(company average {overall:.1f}%)."
    )

    ot = attrition_rate_by(df, "OverTime").set_index("OverTime")["attrition_rate"]
    if {"Yes", "No"} <= set(ot.index) and ot["No"] > 0:
        insights.append(
            f"Employees working overtime leave at {ot['Yes']}% versus {ot['No']}% for those who "
            f"don't ({ot['Yes'] / ot['No']:.1f}x higher)."
        )

    low = df[df["JobSatisfaction"] <= 2]["Left"].mean() * 100
    high = df[df["JobSatisfaction"] >= 3]["Left"].mean() * 100
    insights.append(
        f"Employees with low job satisfaction (1-2) leave at {low:.1f}% versus {high:.1f}% for "
        f"satisfied employees (3-4)."
    )

    ten = attrition_rate_by(df, "TenureBand").set_index("TenureBand")["attrition_rate"]
    insights.append(
        f"Employees in their first two years leave at {ten.iloc[0]}%; "
        f"those with 10+ years leave at {ten.iloc[-1]}%."
    )
    return insights


# ------------------------------------------------------------------ HTML
HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HR Analytics Dashboard</title>
<style>
  body {font-family: Segoe UI, Arial, sans-serif; background:#f1f5f9; margin:0; color:#0f172a;}
  header {background:#1e3a8a; color:white; padding:20px 32px;}
  header h1 {margin:0; font-size:24px;} header p {margin:4px 0 0; opacity:.8; font-size:13px;}
  main {max-width:1250px; margin:0 auto; padding:24px;}
  .cards {display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-bottom:20px;}
  .card {background:white; border-radius:10px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.1);}
  .card .label {font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:.04em;}
  .card .value {font-size:28px; font-weight:700; margin-top:4px;}
  .insights {background:white; border-radius:10px; padding:16px 22px; margin-bottom:20px;
             box-shadow:0 1px 3px rgba(0,0,0,.1);}
  .insights h2 {margin:0 0 8px; font-size:16px;} .insights li {margin:6px 0; font-size:14px;}
  .grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); gap:16px;}
  .grid img {width:100%; background:white; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.1);}
  footer {text-align:center; font-size:12px; color:#64748b; padding:16px;}
</style></head>
<body>
<header><h1>HR Analytics Dashboard</h1><p>Workforce overview and attrition analysis</p></header>
<main>
  <div class="cards">{{CARDS}}</div>
  <div class="insights"><h2>Key insights</h2><ul>{{INSIGHTS}}</ul></div>
  <div class="grid">{{IMAGES}}</div>
</main>
<footer>Built with Python, Pandas and Matplotlib. Sample data is synthetic.</footer>
</body></html>
"""


def build_html(df) -> str:
    k = compute_kpis(df)
    cards = [
        ("Headcount", f"{k['headcount']:,}"),
        ("Attrition rate", f"{k['attrition_rate']}%"),
        ("Employees who left", f"{k['attrition_count']:,}"),
        ("Avg monthly income", f"INR {k['avg_income']:,}"),
        ("Avg tenure", f"{k['avg_tenure']} yrs"),
        ("Avg job satisfaction", f"{k['avg_satisfaction']} / 4"),
        ("Overtime rate", f"{k['overtime_rate']}%"),
    ]
    cards_html = "".join(
        f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>'
        for label, value in cards
    )
    insights_html = "".join(f"<li>{text}</li>" for text in build_insights(df))
    images_html = "".join(
        f'<img alt="{name}" src="data:image/png;base64,{base64.b64encode(render_png(draw, df)).decode()}">'
        for name, draw in CHARTS
    )
    return (HTML_TEMPLATE.replace("{{CARDS}}", cards_html)
            .replace("{{INSIGHTS}}", insights_html)
            .replace("{{IMAGES}}", images_html))


def build_preview(df, path: Path) -> None:
    k = compute_kpis(df)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for ax, (_, draw) in zip(axes.ravel(), CHARTS):
        draw(ax, df)
    fig.suptitle(
        f"HR Analytics Dashboard  |  Headcount: {k['headcount']:,}  |  Attrition: {k['attrition_rate']}%  |  "
        f"Avg income: INR {k['avg_income']:,}  |  Avg tenure: {k['avg_tenure']} yrs",
        fontsize=14, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HR dashboard report")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"{args.data} not found. Run: python data/generate_hr_data.py")

    df = load_data(args.data)
    OUTPUT_DIR.mkdir(exist_ok=True)

    (OUTPUT_DIR / "hr_dashboard.html").write_text(build_html(df), encoding="utf-8")
    build_preview(df, OUTPUT_DIR / "dashboard_preview.png")

    print("KPIs:", compute_kpis(df))
    print("\nKey insights:")
    for text in build_insights(df):
        print(" -", text)
    print(f"\nSaved {OUTPUT_DIR / 'hr_dashboard.html'} and dashboard_preview.png")


if __name__ == "__main__":
    main()
