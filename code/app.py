from curses import raw

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from pathlib import Path
from shapely import wkt

script_dir = Path(__file__).parent

input_unemploy = script_dir / '../data/derived-data/homelessness_v_unemployment_change.csv'
input_assist = script_dir / '../data/derived-data/acs_federal_assistance.csv'


st.set_page_config(page_title="Homelessness vs. Assistance/Unemployment", layout="wide")
st.title("Homelessness Change vs. Federal Assistance & Unemployment Change")
st.markdown("Explore the relationship between the 10‑year change in homelessness and changes in federal assistance recipients or unemployment rate across U.S. states.")

@st.cache_data
def load_data():
    df_fed = pd.read_csv(input_assist)
    df_fed["public_assistance_change_10_years"] = (
        df_fed["public_assistance_change_10_years"]
        .replace({",": ""}, regex=True)
        .astype(int)
    )
    df_unemp = pd.read_csv(input_unemploy)
    df = pd.merge(df_fed, df_unemp, on="State", suffixes=("", "_dup"))
    if "homelessness_change_10_years_dup" in df.columns:
        df.drop(columns=["homelessness_change_10_years_dup"], inplace=True)
    return df

df = load_data()

st.sidebar.header("Select Y‑axis metric")
y_axis_choice = st.sidebar.radio(
    "Choose the variable to compare with homelessness change:",
    ("Federal Assistance Change", "Unemployment Rate Change")
)

if y_axis_choice == "Federal Assistance Change":
    y_col = "public_assistance_change_10_years"
    y_label = "Change in public assistance recipients (10 years)"
else:
    y_col = "employment_change"
    y_label = "Change in unemployment rate (percentage points, 10 years)"

# Base chart encoding (shared by points and regression)
base = alt.Chart(df).encode(
    x=alt.X("homelessness_change_10_years:Q", title="Change in homelessness (10 years)"),
    y=alt.Y(f"{y_col}:Q", title=y_label),
)

# Scatter points (no text labels)
points = base.mark_circle(size=80, opacity=0.7, color="steelblue").encode(
    tooltip=["State:N", "homelessness_change_10_years:Q", f"{y_col}:Q"]
)

# Linear regression line – use transform_regression with extent to cover the full x range
regression = base.transform_regression(
    "homelessness_change_10_years", y_col, method="linear", extent=[df["homelessness_change_10_years"].min(), df["homelessness_change_10_years"].max()]
).mark_line(color="red", size=3)

# Combine layers
chart = (points + regression).properties(
    title=f"Homelessness Change vs. {y_label}",
    width=800,
    height=500
).interactive()

st.altair_chart(chart, use_container_width=True)

with st.expander("Show raw data"):
    st.dataframe(df)

st.markdown("Data sources: ACS (federal assistance) and BLS (unemployment).")