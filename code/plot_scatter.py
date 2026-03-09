# Create scatter plot to demonstrate living wage and children outcomes

import pandas as pd
import numpy as np # To calculate regression line
import altair as alt
from altair_saver import save
from pathlib import Path

script_dir = Path(__file__).parent
data_path = script_dir / '../data/derived-data/mobility_outcome_merged.csv'
output_path = script_dir / '../data/derived-data/mobility_scatter.html'

print(data_path)
df = pd.read_csv(data_path)

# Convert columns to safe types
df['Name'] = df['Name'].astype(str)                     # ensure string
df['ratio_living_wage_change'] = pd.to_numeric(df['ratio_living_wage_change'], errors='coerce')
df['outcome_p75'] = pd.to_numeric(df['outcome_p75'], errors='coerce')
df['outcome_p50'] = pd.to_numeric(df['outcome_p50'], errors='coerce')
df['outcome_p25'] = pd.to_numeric(df['outcome_p25'], errors='coerce')
df['living_wage_increase'] = pd.to_numeric(df['living_wage_increase'], errors='coerce')

# Drop rows with missing values in the essential columns
df_clean = df.dropna(subset=['ratio_living_wage_change', 'outcome_p75'])

# --- Compute regression coefficients for the label ---
x = df_clean['ratio_living_wage_change']
y = df_clean['outcome_p75']
slope, intercept = np.polyfit(x, y, 1)                # linear fit
equation = f'y = {slope:.2f}x + {intercept:.2f}'      # format nicely

# Create a tiny DataFrame just for the text label
params_df = pd.DataFrame({'equation': [equation]})

## Base chart with common data and dimensions
base = alt.Chart(df_clean).properties(
    width=600,
    height=400,
    title='Child Outcome vs County Outcomes, by Parental Income in 75th Percentile'
)

# CREATE 75th Percentile Parental Income SCATTERPLOT WITH REGRESSION LINE

points75 = base.mark_circle(size=60, opacity=0.6).encode(
    x=alt.X('ratio_living_wage_change:Q',
            title='Change in County Living Wage (2014–2024)',
            scale=alt.Scale(reverse=True)),
    y=alt.Y('outcome_p75:Q', title='Children\'s Income at Adulthood'),
    tooltip=[
        alt.Tooltip('Name:N', title='County'),
        alt.Tooltip('outcome_p75:Q', title='Income (75th)'),
        alt.Tooltip('ratio_living_wage_change:Q', title='Ratio Change'),
        alt.Tooltip('living_wage_increase:O', title='Living Wage Increased')
    ]
)

# Linear regression line
regression75 = base.transform_regression(
    'ratio_living_wage_change',       # independent variable (x)
    'outcome_p75',                    # dependent variable (y)
    method='linear'
).mark_line(color='green', strokeWidth=3).encode(
    x='ratio_living_wage_change:Q',
    y='outcome_p75:Q'
)

# Combine main layers
chart75 = points75 + regression75

# --- Right‑side legend with regression equation ---
legend_chart = alt.Chart(params_df).mark_text(
    align='left',
    baseline='middle',
    fontSize=12,
    dx=5,               # slight padding from the left edge of the legend box
    dy=5
).encode(
    x=alt.value(10),    # pixels from the left edge of the legend chart
    y=alt.value(200),   # vertically centered (assuming height 400)
    text='equation:N'
).properties(
    width=200,
    height=400,
    title='Linear Regression Equation (75th Percentile)'
)

# Combine horizontally: main chart on the left, legend on the right
final_chart = alt.hconcat(chart75, legend_chart).configure_view(
    stroke=None         # remove the default frame around both charts
)

# Save the combined chart
final_chart.save(output_path)