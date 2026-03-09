# Create income regresions over three income percentiles

import pandas as pd
import numpy as np
import altair as alt
from altair_saver import save
from pathlib import Path

script_dir = Path(__file__).parent
data_path = script_dir / '../data/derived-data/mobility_outcome_merged.csv'
output_path = script_dir / '../data/derived-data/mobility_regression.html'

print(data_path)
df = pd.read_csv(data_path)

# Convert columns to safe types
df['Name'] = df['Name'].astype(str)
df['ratio_living_wage_change'] = pd.to_numeric(df['ratio_living_wage_change'], errors='coerce')
df['outcome_p75'] = pd.to_numeric(df['outcome_p75'], errors='coerce')
df['outcome_p50'] = pd.to_numeric(df['outcome_p50'], errors='coerce')
df['outcome_p25'] = pd.to_numeric(df['outcome_p25'], errors='coerce')
df['living_wage_increase'] = pd.to_numeric(df['living_wage_increase'], errors='coerce')

# Drop rows with missing values in essential columns
df_clean = df.dropna(subset=['ratio_living_wage_change', 'outcome_p75'])

# Reshape data to long format: one row per percentile
df_long = df_clean.melt(
    id_vars=['Name', 'ratio_living_wage_change', 'living_wage_increase'],
    value_vars=['outcome_p75', 'outcome_p50', 'outcome_p25'],
    var_name='percentile',
    value_name='income_outcome'
)

# Map percentile codes to descriptive labels
percentile_labels = {
    'outcome_p75': '75th Percentile',
    'outcome_p50': '50th Percentile',
    'outcome_p25': '25th Percentile'
}
df_long['percentile_label'] = df_long['percentile'].map(percentile_labels)

# -----------------------------------------------------------------
# Compute regression equations for each percentile (using full data)
# -----------------------------------------------------------------
df_reg = df_long.dropna(subset=['income_outcome', 'ratio_living_wage_change'])
equations = []
for percentile in ['75th Percentile', '50th Percentile', '25th Percentile']:
    group = df_reg[df_reg['percentile_label'] == percentile]
    x = group['ratio_living_wage_change'].values
    y = group['income_outcome'].values
    if len(x) >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        eq = f"{percentile[:3]}: y = {slope:.2f}x + {intercept:.0f}"
    else:
        eq = f"{percentile[:3]}: insufficient data"
    equations.append(eq)
text_block = "\n".join(equations)

# Position the text near the top‑left within the y‑axis domain
x_min, x_max = df_reg['ratio_living_wage_change'].min(), df_reg['ratio_living_wage_change'].max()
x_pos = x_max - 0.05 * (x_max - x_min)   # near high x (left side after reversal)
y_pos = 190000                            # fixed within [10000, 200000]

text_df = pd.DataFrame({'x': [x_pos], 'y': [y_pos], 'eq': [text_block]})

# -----------------------------------------------------------------
# Base chart using full data (for regression lines and text)
# -----------------------------------------------------------------
base_full = alt.Chart(df_long).properties(
    width=600,
    height=400,
    title='Child Outcome vs County Outcomes, by Parental Income Percentile'
)

# Regression lines – darker shades, computed from full data
regression = base_full.transform_regression(
    'ratio_living_wage_change',
    'income_outcome',
    method='linear',
    groupby=['percentile_label']
).mark_line(strokeWidth=3, clip=True).encode(      # clip=True
    x=alt.X('ratio_living_wage_change:Q',
            scale=alt.Scale(reverse=True)),
    y='income_outcome:Q',
    color=alt.Color('percentile_label:N',
                    scale=alt.Scale(
                        domain=['75th Percentile', '50th Percentile', '25th Percentile'],
                        range=['darkgreen', 'darkgoldenrod', 'darkred']
                    ),
                    legend=None)
)

# Text annotation
text_ann = alt.Chart(text_df).mark_text(
    align='left',
    baseline='top',
    fontSize=12,
    font='monospace',
    color='black',
    lineBreak='\n'
).encode(
    x='x:Q',
    y='y:Q',
    text='eq:N'
)

# -----------------------------------------------------------------
# Points layer – filtered to the visible y‑domain
# -----------------------------------------------------------------
points = base_full.transform_filter(
    (alt.datum.income_outcome >= 10000) & (alt.datum.income_outcome <= 200000)
).mark_circle(size=10, opacity=0.6, clip=True).encode(
    x=alt.X('ratio_living_wage_change:Q',
            title='Change in County Living Wage (2014-2024)',
            scale=alt.Scale(reverse=True)),
    y=alt.Y('income_outcome:Q', title='Children\'s Income at Adulthood ($)'),
    color=alt.Color('percentile_label:N',
                    scale=alt.Scale(
                        domain=['75th Percentile', '50th Percentile', '25th Percentile'],
                        range=['lightgreen', 'lightyellow', 'lightcoral']
                    ),
                    legend=alt.Legend(title='Parental Income Percentile')),
    tooltip=[
        alt.Tooltip('Name:N', title='County'),
        alt.Tooltip('income_outcome:Q', title='Income'),
        alt.Tooltip('ratio_living_wage_change:Q', title='Ratio Change'),
        alt.Tooltip('living_wage_increase:O', title='Living Wage Increased')
    ]
)

# -----------------------------------------------------------------
# Combine layers and enforce global y‑scale
# -----------------------------------------------------------------
layered_chart = alt.layer(points, regression, text_ann).resolve_scale(
    color='independent'
).encode(
    y=alt.Y(scale=alt.Scale(type='log', domain=[10000, 200000]))
)

final_chart = layered_chart.configure_axisY(
    title="Children's Income Outcome"
)

final_chart.save(output_path)