import csv
from curses import raw

import pandas as pd
import numpy as np

from pathlib import Path
from shapely import wkt

script_dir = Path(__file__).parent

##########################################

# Process mobility metrics data
raw_mobility = script_dir / '../data/raw-data/mobility_income.csv'
output_mobility = script_dir / '../data/derived-data/mobility_hist.csv'

# Read in the raw mobility data
mobility_df = pd.read_csv(raw_mobility, encoding='latin-1')

# Clean up mobility file

# Correct state/county fips columns
mobility_df['state'] = mobility_df['state'].astype(int).astype(str)
mobility_df['county'] = mobility_df['county'].astype(int).astype(str)

# Pad each to 2 and 3 digits, respectively
mobility_df['state'] = mobility_df['state'].str.zfill(2)
mobility_df['county'] = mobility_df['county'].str.zfill(3)

# Combine to create a single fips code column
mobility_df['fips'] = mobility_df['state'] + mobility_df['county']

# Filter the two years, merge, and compute difference
mobility_df_2014 = mobility_df[mobility_df['year'] == 2014][['fips', 'ratio_living_wage']].rename(columns={'ratio_living_wage': 'ratio_living_wage_2014'})
mobilidy_df_2024 = mobility_df[mobility_df['year'] == 2024][['fips', 'ratio_living_wage']].rename(columns={'ratio_living_wage': 'ratio_living_wage_2024'})
mobility_df_change = pd.merge(mobility_df_2014, mobilidy_df_2024, on='fips', how='inner')
mobility_df_change['ratio_living_wage_change'] = mobility_df_change['ratio_living_wage_2024'] - mobility_df_change['ratio_living_wage_2014']

# Add an indicator variable to denote counties where living wage ratios have increased
mobility_df_change['living_wage_increase'] = (mobility_df_change['ratio_living_wage_change'] > 0).astype(int)

# Output mobility dataset for histogram viz
mobility_df_change.to_csv(output_mobility)

##########################################

# Process Opportunity Atlas data for childhood income outcomes
raw_op75 = script_dir / '../data/raw-data/cty_kfr_rP_gP_p75.csv'
raw_op50 = script_dir / '../data/raw-data/cty_kfr_rP_gP_p50.csv'
raw_op25 = script_dir / '../data/raw-data/cty_kfr_rP_gP_p25.csv'

# Output file path
output_income = script_dir / '../data/derived-data/mobility_outcome_merged.csv'

# read in atlas files
opinc75_df = pd.read_csv(raw_op75, encoding='latin-1')
opinc50_df = pd.read_csv(raw_op50, encoding='latin-1')
opinc25_df = pd.read_csv(raw_op25, encoding='latin-1')

# Rename column 1 header to 'cty' in each dataframe
opinc75_df.rename(columns={opinc75_df.columns[0]: 'cty'}, inplace=True)
opinc50_df.rename(columns={opinc50_df.columns[0]: 'cty'}, inplace=True)
opinc25_df.rename(columns={opinc25_df.columns[0]: 'cty'}, inplace=True) 

# merge all three files based on cty column
opportunity_df = opinc75_df.merge(
        opinc50_df,
        on='cty',
        how='inner'
    ).merge(
        opinc25_df,
        on='cty',
        how='inner')

# Drop redundant name columns
opportunity_df = opportunity_df.drop(columns=['Name_x', 'Name_y'], inplace=False)

# Rename annoying outcome columnes to be more intuitive
opportunity_df = opportunity_df.rename(columns={
    'Household_Income_at_Age_35_rP_gP_p75': 'outcome_p75',
    'Household_Income_at_Age_35_rP_gP_p50': 'outcome_p50',
    'Household_Income_at_Age_35_rP_gP_p25': 'outcome_p25'
}, inplace=False)

# Fix cty column to drop cty prefix and convert to string, change name of column to fips for clarity
opportunity_df['fips'] = opportunity_df['cty'].str.replace('cty', '').astype(str)

# Reorder columns to have name column second, drop old cty column
opportunity_df = opportunity_df[['fips', 'Name', 'outcome_p25', 'outcome_p50', 'outcome_p75']]

# Merge Opportunity Atlas Data with Mobility Data based on FIPS code
merged_df = pd.merge(opportunity_df,
                     mobility_df_change,
                     how='inner')

merged_df.to_csv(output_income, index=False)

##########################################

# Preprocess state homelessness data

# Process homelessness metrics data
raw_homeless = script_dir / '../data/raw-data/mobility_homelessness.csv'
output_homeless = script_dir / '../data/derived-data/homelessness_states.csv'

homeless_df = pd.read_csv(raw_homeless, encoding='latin-1')

# Clean up columns with values we need
homeless_df['Year'] = homeless_df['Year'].astype(int).astype(str)
homeless_df['Overall Homelessness'] = homeless_df['Overall Homelessness'].astype(str).str.replace(',', '', regex=False)
homeless_df['Overall Homelessness'] = pd.to_numeric(homeless_df['Overall Homelessness'], errors='coerce').astype('Int64')

# Filter the two years, merge, and compute difference
homeless_df_2015 = homeless_df[homeless_df['Year'] == '2015'][['State', 'Overall Homelessness']].rename(columns={'Overall Homelessness': 'Overall Homelessness_2015'})
homeless_df_2024 = homeless_df[homeless_df['Year'] == '2024'][['State', 'Overall Homelessness']].rename(columns={'Overall Homelessness': 'Overall Homelessness_2024'})
homeless_df_change = pd.merge(homeless_df_2015, homeless_df_2024, on='State', how='inner')
homeless_df_change['homelessness_change_10_years'] = homeless_df_change['Overall Homelessness_2024'] - homeless_df_change['Overall Homelessness_2015']

# Add an indicator variable to denote counties where living wage ratios have increased
homeless_df_change['Homelessness_decrease'] = (homeless_df_change['homelessness_change_10_years'] < 0).astype(int)

# Tidy up output to match other data
# change 'Washington, D.C.' to 'District of Columbia' for consistency with other datasets
homeless_df_change['State'] = homeless_df_change['State'].replace('Washington, D.C.', 'District of Columbia')
# Remove "Total" row if it exists
homeless_df_change = homeless_df_change[homeless_df_change['State'] != 'Total']

homeless_df_change.head()

# Output homelessness dataset for histogram viz
output_homeless.parent.mkdir(parents=True, exist_ok=True)
try:
    homeless_df_change.to_csv(output_homeless, index=False)
except PermissionError:
    print(f"Permission denied: {output_homeless}. Close any program using the file and try again.")

##########################################

# Preprocess state level federal government assistance data
raw_fed_assist = script_dir / '../data/raw-data/acs_federal_assistance.csv'
output_fed_assist = script_dir / '../data/derived-data/acs_federal_assistance.csv'

df = pd.read_csv(raw_fed_assist, skipinitialspace=True)

df.head()

# Strip leading/trailing spaces from the State column (the metric names)
df['State'] = df['State'].str.strip()

df.set_index('State', inplace=True)

# Transpose
df_t = df.transpose()

df_t.head()
# Clean state names in index: remove '!!Estimate'
df_t.index = df_t.index.str.replace('!!Estimate', '', regex=False)

# Reset index to make states a column
df_t.reset_index(inplace=True)

# Rename the index column to 'State'
df_t.rename(columns={'index': 'State'}, inplace=True)

# string map column names
col_mapping = {
    'With public assistance income - 2024': 'Public Assistance 2024',
    'With public assistance income - 2015': 'Public Assistance 2015',
    'Change in public assistance income over 10 years': 'public_assistance_change_10_years'
}
df_t.rename(columns=col_mapping, inplace=True)

# Select columns in desired order
df_final = df_t[['State', 'Public Assistance 2024', 'Public Assistance 2015', 'public_assistance_change_10_years']]

##########################################

# Merge state level datasets for homelessness and federal assistance
df_merged = pd.merge(
    homeless_df_change,
    df_final,
    on='State',
    how='outer'
)

# --- Display or save the result ---
print(df_merged.head())

# Drop all rows but state, homelessness change, and federal assistance change for scatterplot viz
df_merged = df_merged[['State', 'homelessness_change_10_years', 'public_assistance_change_10_years']]

# Output
df_merged.to_csv(output_fed_assist, index=False)

##########################################

# Preprocess federal unemployment data for 2024
input_file = script_dir / '../data/raw-data/acs_employment_2024.csv'
output_file = script_dir / '../data/raw-data/acs_unemp_2024.csv' # STILL IN RAW DATA

# States/territories to exclude
excluded = {"United States", "Puerto Rico"}

with open(input_file, "r", encoding="utf-8-sig") as f_in:
    reader = csv.reader(f_in)
    header = next(reader)

    # Find the index of the column containing "Unemployment Rate"
    rate_idx = None
    for i, col in enumerate(header):
        if "Unemployment Rate" in col:
            rate_idx = i
            break
    if rate_idx is None:
        raise ValueError("Could not find the 'Unemployment Rate' column in the header.")

    results = []
    try:
        while True:
            # State name row
            state_row = next(reader)
            if state_row[0] and all(cell == "" for cell in state_row[1:]):
                state_name = state_row[0].strip()

                # Skip the excluded entries
                if state_name in excluded:
                    # Still need to consume the next two rows (estimate and percent)
                    _ = next(reader)  # estimate row
                    _ = next(reader)  # percent row
                    continue

                # Skip the estimate row (not needed for percentage)
                _ = next(reader)

                # Percent row – contains the unemployment rate
                percent_row = next(reader)

                # Extract the unemployment rate value from the percent row
                unemployment_rate = percent_row[rate_idx]
                results.append([state_name, unemployment_rate])
    except StopIteration:
        pass  # End of file reached

# Write the extracted data to a new CSV
with open(output_file, "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["State", "Unemployment_Rate_2024"])
    writer.writerows(results)

print(f"Done. Extracted unemployment rates saved to {output_file}")


##########################################

# same exact code for 2015
input_file = script_dir / '../data/raw-data/acs_employment_2015.csv'
output_file = script_dir / '../data/raw-data/acs_unemp_2015.csv' # STILL IN RAW DATA

# States/territories to exclude
excluded = {"United States", "Puerto Rico"}

with open(input_file, "r", encoding="utf-8-sig") as f_in:
    reader = csv.reader(f_in)
    header = next(reader)

    # Find the index of the column containing "Unemployment Rate"
    rate_idx = None
    for i, col in enumerate(header):
        if "Unemployment Rate" in col:
            rate_idx = i
            break
    if rate_idx is None:
        raise ValueError("Could not find the 'Unemployment Rate' column in the header.")

    results = []
    try:
        while True:
            # State name row
            state_row = next(reader)
            if state_row[0] and all(cell == "" for cell in state_row[1:]):
                state_name = state_row[0].strip()

                # Skip the excluded entries
                if state_name in excluded:
                    # Still need to consume the next two rows (estimate and percent)
                    _ = next(reader)  # estimate row
                    _ = next(reader)  # percent row
                    continue

                # Skip the estimate row (not needed for percentage)
                _ = next(reader)

                # Percent row – contains the unemployment rate
                percent_row = next(reader)

                # Extract the unemployment rate value from the percent row
                unemployment_rate = percent_row[rate_idx]
                results.append([state_name, unemployment_rate])
    except StopIteration:
        pass  # End of file reached

# Write the extracted data to a new CSV
with open(output_file, "w", newline="", encoding="utf-8") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["State", "Unemployment_Rate_2024"])
    writer.writerows(results)

print(f"Done. Extracted unemployment rates saved to {output_file}")

##########################################

# Merge the two years and calculate change
# same exact code for 2015
input_2015 = script_dir / '../data/raw-data/acs_unemp_2015.csv' # STILL IN RAW DATA
input_2024 = script_dir / '../data/raw-data/acs_unemp_2024.csv' # STILL IN RAW DATA
output_file = script_dir / '../data/raw-data/acs_unemp_change.csv' # Still in Raw Data

unemp_2015_df = pd.read_csv(input_2015)
unemp_2024_df = pd.read_csv(input_2024) 

# Read 2015 data
with open(input_2015, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data_2015 = {}
    for row in reader:
        state = row["State"]
        # Remove '%' and convert to float
        rate = float(row["Unemployment_Rate_2024"].strip('%'))
        data_2015[state] = rate

# Read 2024 data
with open(input_2024, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data_2024 = {}
    for row in reader:
        state = row["State"]
        rate = float(row["Unemployment_Rate_2024"].strip('%'))
        data_2024[state] = rate

# Compute change and prepare output
output = []
for state in data_2024:
    if state in data_2015:
        change = data_2024[state] - data_2015[state]
        output.append([state, change])
    else:
        print(f"Warning: {state} not found in 2015 data")

# Write output CSV
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["State", "Change_2024_vs_2015 (percentage points)"])
    writer.writerows(output)

print("Done. Change file saved as 'state_unemployment_change_2015_2024.csv'")

##########################################

# Merge unemployment change data with homlessness change data
input_file = script_dir / '../data/raw-data/acs_unemp_change.csv' # Still in Raw Data
# Merged with homeless_df_change from above, which is still in memory
output_file = script_dir / '../data/derived-data/homelessness_v_unemployment_change.csv' # Output for merged dataset

# Read unemployment change data
unemp_change_df = pd.read_csv(input_file)  


# Merge on 'State' and select relevant columns
merged = pd.merge(
    unemp_change_df,
    homeless_df_change[['State', 'homelessness_change_10_years']],
    on='State',
    how='inner'  # or 'outer' depending on need; inner keeps only states in both
)

# Rename columns for clarity (optional)
merged.rename(columns={
    'Change_2024_vs_2015 (percentage points)': 'employment_change'
}, inplace=True)

# Swap columns 2 and 3 to have State, homeless change, then employment change
cols = merged.columns.tolist()
cols[1], cols[2] = cols[2], cols[1]

merged = merged[cols]

merged.to_csv(output_file, index=False)

# Display or save result
print(merged.head())
