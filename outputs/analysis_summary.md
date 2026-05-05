# EV Utility Footprint Analysis Summary

Dataset source: `C:\Users\impro\Desktop\zl814_project\Electric_Vehicle_Population_Data.csv`

Rows analyzed: 276,828

Utilities analyzed: 78

Recent model-year cutoff: `2022`

Minimum utility size for growth ranking: `100` vehicles

## Main Assumptions

- Electric Utility is used as the primary grouping variable because utilities are directly affected by EV charging demand.
- Model year is used as a proxy for adoption recency because the dataset does not include a registration date for every record.
- Utility names are standardized for whitespace, case, and separator differences; records with missing utility names are retained as `UNKNOWN UTILITY`.
- Electric range values of 0 are kept in the cleaned data, but positive-range averages and medians are reported separately.

## Largest Utility Territories

| Utility Standardized | total_ev_count | bev_share | recent_model_year_share |
| --- | --- | --- | --- |
| PUGET SOUND ENERGY INC \| CITY OF TACOMA - (WA) | 98,542 | 82.6% | 73.2% |
| PUGET SOUND ENERGY INC | 58,233 | 81.2% | 69.4% |
| CITY OF SEATTLE - (WA) \| CITY OF TACOMA - (WA) | 45,996 | 80.3% | 67.1% |
| BONNEVILLE POWER ADMINISTRATION \| PUD NO 1 OF CLARK COUNTY - (WA) | 16,614 | 76.0% | 68.2% |
| BONNEVILLE POWER ADMINISTRATION \| CITY OF TACOMA - (WA) \| PENINSULA LIGHT COMPANY | 12,590 | 77.3% | 66.2% |

## Fastest-Growing Utility Territories

| growth_rank | Utility Standardized | total_ev_count | recent_model_year_share |
| --- | --- | --- | --- |
| 1 | BONNEVILLE POWER ADMINISTRATION \| CITY OF CENTRALIA - (WA) \| CITY OF TACOMA - (WA) | 315 | 73.3% |
| 2 | CITY OF TACOMA - (WA) \| TANNER ELECTRIC COOP | 388 | 73.2% |
| 3 | PUGET SOUND ENERGY INC \| CITY OF TACOMA - (WA) | 98,542 | 73.2% |
| 4 | BONNEVILLE POWER ADMINISTRATION \| VERA IRRIGATION DISTRICT #15 | 615 | 72.8% |
| 5 | BONNEVILLE POWER ADMINISTRATION \| AVISTA CORP \| INLAND POWER & LIGHT COMPANY | 4,727 | 70.2% |

## Files Produced

- `cleaned_ev_population.csv`
- `data_quality_summary.csv`
- `utility_footprint_summary.csv`
- `fastest_growing_utilities.csv`
- `model_year_cohort_distribution.csv`
- `top_utilities_by_ev_count.svg`
- `top_utilities_by_recent_share.svg`
