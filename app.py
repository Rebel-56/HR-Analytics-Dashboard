"""Interactive Streamlit HR dashboard with filters.

Run:  streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent / "src"))
from kpis import DEFAULT_DATA, attrition_rate_by, compute_kpis, load_data  # noqa: E402

st.set_page_config(page_title="HR Analytics Dashboard", page_icon="👥", layout="wide")


@st.cache_data
def get_data():
    return load_data(DEFAULT_DATA)


df = get_data()

st.title("👥 HR Analytics Dashboard")

# ---- sidebar filters
st.sidebar.header("Filters")
departments = st.sidebar.multiselect("Department", sorted(df["Department"].unique()),
                                     default=sorted(df["Department"].unique()))
genders = st.sidebar.multiselect("Gender", sorted(df["Gender"].unique()),
                                 default=sorted(df["Gender"].unique()))
overtime = st.sidebar.multiselect("Overtime", ["Yes", "No"], default=["Yes", "No"])

view = df[df["Department"].isin(departments) & df["Gender"].isin(genders) & df["OverTime"].isin(overtime)]

if view.empty:
    st.warning("No employees match the selected filters.")
    st.stop()

# ---- KPI row
k = compute_kpis(view)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Headcount", f"{k['headcount']:,}")
c2.metric("Attrition rate", f"{k['attrition_rate']}%")
c3.metric("Avg monthly income", f"₹ {k['avg_income']:,}")
c4.metric("Avg tenure", f"{k['avg_tenure']} yrs")
c5.metric("Avg satisfaction", f"{k['avg_satisfaction']} / 4")

# ---- charts
left, right = st.columns(2)
with left:
    st.subheader("Attrition rate by department (%)")
    st.bar_chart(attrition_rate_by(view, "Department").set_index("Department")["attrition_rate"])
    st.subheader("Attrition rate by tenure (%)")
    st.bar_chart(attrition_rate_by(view, "TenureBand").set_index("TenureBand")["attrition_rate"])
with right:
    st.subheader("Attrition rate by overtime (%)")
    st.bar_chart(attrition_rate_by(view, "OverTime").set_index("OverTime")["attrition_rate"])
    st.subheader("Attrition rate by job satisfaction (%)")
    st.bar_chart(attrition_rate_by(view, "JobSatisfaction").set_index("JobSatisfaction")["attrition_rate"])

with st.expander("View employee data"):
    st.dataframe(view.drop(columns=["Left"]), use_container_width=True, hide_index=True)
