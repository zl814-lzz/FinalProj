# CS 210 Final Project: EV Utility Footprint Analysis

This project analyzes the Washington Electric Vehicle Population dataset by electric utility territory. It follows the proposal focus: BEV share, electric range profiles, and fastest-growing utility territories using model-year cohorts.

## Dataset

Expected local dataset path:

```text
C:\Users\impro\Desktop\zl814_project\Electric_Vehicle_Population_Data.csv
```

The script also accepts a custom path with `--input`.

## How to Run

From this folder:

```powershell
py -m pip install -r requirements.txt
py src\analyze_ev_utilities.py
```

Or with an explicit dataset path:

```powershell
py src\analyze_ev_utilities.py --input "C:\Users\impro\Desktop\zl814_project\Electric_Vehicle_Population_Data.csv"
```

## Outputs

The script creates an `outputs` folder containing:

- `cleaned_ev_population.csv`: cleaned analysis-ready rows and derived columns.
- `data_quality_summary.csv`: row counts, missing values, year range, range checks, and utility counts.
- `utility_footprint_summary.csv`: total EV count, BEV/PHEV counts, BEV share, range metrics, and recent adoption metrics by utility.
- `fastest_growing_utilities.csv`: ranked utilities using recent model-year share as the growth proxy.
- `model_year_cohort_distribution.csv`: cohort counts and shares by utility.
- `top_utilities_by_ev_count.svg`: visualization of the largest utility territories by EV count.
- `top_utilities_by_recent_share.svg`: visualization of utilities with the highest recent model-year share.
- `analysis_summary.md`: short written summary of key findings and assumptions.

## Method Notes

- The electric utility field is standardized by trimming spaces, uppercasing names, and normalizing separator characters.
- Rows with missing electric utility are labeled `UNKNOWN UTILITY` so they remain traceable.
- BEV share is calculated as `BEV count / total EV count`.
- Recent adoption is proxied with model years greater than or equal to 2022, matching the project proposal.
- Growth rankings use a minimum utility size threshold of 100 vehicles by default to reduce misleading rankings from very small utilities.
- Electric range values of 0 are preserved in the cleaned dataset, but positive-range summary metrics are also reported because many newer records use 0 where range is unavailable or not listed.

