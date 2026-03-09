# Homelessness & Poverty Analysis

This project processes and visualizes variables that are related to poverty and homelessness

## Setup

```bash
conda env create -f environment.yml
conda activate dap
```


## Project Structure

```
data/
  raw-data/          
    acs_employment_2015.csv         # Raw Data file - ACS employment data
    acs_employment_2024.csv         # Raw Data file - ACS employment data
    acs_federal_assistance.csv      # Raw data file - ACS federal assistance data
    cty_kfr_rp_gp_p25.csv           # Raw data file - Opportunity Atlas Children's outcome data by parental income quartile 25th, by county
    cty_kfr_rp_gp_p50csv           # Raw data file - Opportunity Atlas Children's outcome data by parental income quartile 50th, by county
    cty_kfr_rp_gp_p75.csv           # Raw data file - Opportunity Atlas Children's outcome data by parental income quartile 75th, by county
    mobility_homelessness.csv       # Raw data file - Urban Institute Mobility Project Homelessness data by state, by year
    mobility_income.csv             # Raw data file - Urban Istitute Mobility Project living wage index by county, by year
    Other .csv files are preprocessing files required for derived data

  derived-data/       # Filtered data and output plots
    acs_federal_assistance.csv          # Derived data used to measure change in homelessness against change in federal assistance, by state
    homelessness_v_unemployment_change  # Derived data used to measure change in homelessness against change in unemployment figures, by state
    mobility_hist.csv                   # Derived data to show living wage index by county
    mobility_outcome_merged.csv         # Derived data to show childhood outcomes by county, separated by parent's income by quartile

code/
  preprocessing.py    # Filters raw data and processes for final viz csvs
  app.py              # Streamlit dashboard to examine relationship between homelessness, unemployment rate, and federal assistance
  plot_hist.py        # Plots histogram of change in county living wage over 10 years
  plot_scatter.py     # Plots county scatter and linear regression relationship between change in living wage index and children's adult earnings, for 75th percentile of parent income
  plot_income_regresion,py # same as above, but for 75, 50, 25 quartile
```

## Usage

1. Run preprocessing to filter data:
   ```bash
   python code/preprocessing.py
   ```

2. Generate the various viz plots
   ```bash
   python code/plot_hist, scatter, and income_regression
   ```

3. Generate the streamlit app
   ```bash
   python code/app.py
   Will need to wake app up if it hasn't run for 24 hours
   ```
