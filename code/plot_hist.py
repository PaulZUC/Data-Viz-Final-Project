# Create histogram to demonstrate change in living wage over time for all counties

import pandas as pd
import altair as alt
from altair_saver import save
from pathlib import Path

script_dir = Path(__file__).parent
data_path = script_dir / '../data/derived-data/mobility_hist.csv'
output_path = script_dir / '../data/derived-data/mobility_hist.html'

df = pd.read_csv(data_path)

# Remove any missing values if necessary
df_clean = df.dropna(subset=['ratio_living_wage_change'])

# 1. Create bins (adjust number of bins as needed)
num_bins = 30
df_clean['bin'] = pd.cut(df_clean['ratio_living_wage_change'], bins=num_bins, include_lowest=True)

# 2. Compute counts per bin
bin_counts = df_clean.groupby('bin', observed=False).size().reset_index(name='count')

# 3. Compute proportions
total = len(df_clean)
bin_counts['proportion'] = bin_counts['count'] / total

# 4. Extract numeric bin edges from the ORIGINAL categories (not from bin_counts)
original_categories = df_clean['bin'].cat.categories
bin_edges = pd.DataFrame({
    'bin': original_categories,
    'bin_start': original_categories.left.astype(float),
    'bin_end': original_categories.right.astype(float)
})

# Merge using string representations to avoid categorical dtype issues
bin_counts['bin_str'] = bin_counts['bin'].astype(str)
bin_edges['bin_str'] = bin_edges['bin'].astype(str)
bin_counts = bin_counts.merge(bin_edges[['bin_str', 'bin_start', 'bin_end']], on='bin_str', how='left')

# Drop the original Interval column and the helper string column
bin_counts.drop(columns=['bin', 'bin_str'], inplace=True)

# 5. Ensure bin_start and bin_end are float (they should be, but safe)
bin_counts['bin_start'] = bin_counts['bin_start'].astype(float)
bin_counts['bin_end'] = bin_counts['bin_end'].astype(float)

# 6. Create Altair histogram with proportions
hist = alt.Chart(bin_counts).mark_bar().encode(
    x=alt.X('bin_start:Q', title='Living Wage Change (2014–2024)', bin='binned'),
    x2='bin_end:Q',
    y=alt.Y('proportion:Q', axis=alt.Axis(title='Proportion of Counties', format='%')),
    tooltip=['bin_start', 'bin_end', 'count', alt.Tooltip('proportion:Q', format='.2%')]
).properties(
    title='Distribution of Living Wage Change Across Counties'
)

hist.save(output_path)