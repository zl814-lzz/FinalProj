# CS 210 Final Project: EV Utility Footprint Analysis

USE VSCODE

This project analyzes the Washington Electric Vehicle Population dataset by electric utility territory. It focuses on EV mix, electric-range patterns, and utility territories with the highest share of recent model-year EVs.

## Dataset

The dataset is now included in the project root:

```text
Electric_Vehicle_Population_Data.csv
```

You can also pass a custom location with `--input`.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## How to Run

From the project folder:

```powershell
py -m pip install -r requirements.txt
py your address\analyze_ev_utilities.py
```

Or with an explicit dataset path and custom output folder:

```powershell
py Your Adress\analyze_ev_utilities.py --input ".\Electric_Vehicle_Population_Data.csv" --output-dir ".\outputs"
```

## Outputs

The script creates an `outputs` folder containing:

- `cleaned_ev_population.csv`: cleaned analysis-ready rows and derived columns.
- `data_quality_summary.csv`: row counts, missing values, year range, range checks, utility counts, and zero-range share.
- `utility_footprint_summary.csv`: total EV count, BEV/PHEV counts, BEV share, range metrics, and recent-adoption metrics by utility.
- `fastest_growing_utilities.csv`: ranked utilities using recent model-year share as the recency indicator.
- `model_year_cohort_distribution.csv`: cohort counts and shares by utility.
- `top_utilities_by_ev_count.svg`: visualization of the largest utility territories by EV count.
- `top_utilities_by_recent_share.svg`: visualization of utilities with the highest recent model-year share.
- `analysis_summary.md`: written summary of key findings, assumptions, and limitations.

## Method Notes

- The electric utility field is standardized by trimming spaces, uppercasing names, and normalizing separator characters.
- Rows with missing electric utility are labeled `UNKNOWN UTILITY` so they remain traceable.
- BEV share is calculated as `BEV count / total EV count`.
- Recent adoption is proxied with model years greater than or equal to 2022.
- The recent-adoption ranking uses a minimum utility size threshold of 100 vehicles by default to reduce misleading rankings from very small utilities.
- The ranking is a recency proxy, not a true year-over-year growth rate, because the dataset does not include a direct utility-level registration time series.
- Electric range values of 0 are preserved in the cleaned dataset, but positive-range summary metrics are also reported because many newer records use 0 where range is unavailable or not listed.

## Reproducibility Notes

- No manual spreadsheet editing is required; all outputs are generated directly by the script.
- The script writes lightweight SVG charts directly, so no plotting library is needed.
- If your dataset file is not stored in the project root, use `--input` to point to the correct file.
