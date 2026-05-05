from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

import numpy as np
import pandas as pd


DEFAULT_INPUT = Path(
    r"C:\Users\impro\Desktop\zl814_project\Electric_Vehicle_Population_Data.csv"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
RECENT_YEAR_CUTOFF = 2022
MIN_UTILITY_COUNT_FOR_GROWTH_RANKING = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze EV adoption by electric utility territory."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to Electric_Vehicle_Population_Data.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where result files will be written.",
    )
    parser.add_argument(
        "--recent-year",
        type=int,
        default=RECENT_YEAR_CUTOFF,
        help="Model year cutoff used as the recent-adoption proxy.",
    )
    parser.add_argument(
        "--min-utility-count",
        type=int,
        default=MIN_UTILITY_COUNT_FOR_GROWTH_RANKING,
        help="Minimum utility EV count included in growth ranking.",
    )
    return parser.parse_args()


def standardize_utility(value: object) -> str:
    if pd.isna(value):
        return "UNKNOWN UTILITY"

    text = str(value).strip().upper()
    text = text.replace("||", "|")
    parts = [" ".join(part.split()) for part in text.split("|")]
    parts = [part for part in parts if part]
    return " | ".join(parts) if parts else "UNKNOWN UTILITY"


def load_and_clean(input_path: Path, recent_year: int) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Dataset not found: {input_path}")

    df = pd.read_csv(input_path)
    required_columns = [
        "VIN (1-10)",
        "County",
        "City",
        "State",
        "Postal Code",
        "Model Year",
        "Make",
        "Model",
        "Electric Vehicle Type",
        "Clean Alternative Fuel Vehicle (CAFV) Eligibility",
        "Electric Range",
        "DOL Vehicle ID",
        "Electric Utility",
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    cleaned = df[required_columns].copy()

    text_columns = [
        "County",
        "City",
        "State",
        "Make",
        "Model",
        "Electric Vehicle Type",
        "Clean Alternative Fuel Vehicle (CAFV) Eligibility",
    ]
    for column in text_columns:
        cleaned[column] = (
            cleaned[column]
            .fillna("UNKNOWN")
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(r"\s+", " ", regex=True)
        )

    cleaned["Utility Standardized"] = cleaned["Electric Utility"].apply(
        standardize_utility
    )
    cleaned["Model Year"] = pd.to_numeric(
        cleaned["Model Year"], errors="coerce"
    ).astype("Int64")
    cleaned["Electric Range"] = pd.to_numeric(
        cleaned["Electric Range"], errors="coerce"
    )
    cleaned["Postal Code"] = pd.to_numeric(cleaned["Postal Code"], errors="coerce")
    cleaned["Is BEV"] = cleaned["Electric Vehicle Type"].eq(
        "BATTERY ELECTRIC VEHICLE (BEV)"
    )
    cleaned["Is PHEV"] = cleaned["Electric Vehicle Type"].eq(
        "PLUG-IN HYBRID ELECTRIC VEHICLE (PHEV)"
    )
    cleaned["Is Recent Model Year"] = cleaned["Model Year"].ge(recent_year)
    cleaned["Range Positive"] = cleaned["Electric Range"].where(
        cleaned["Electric Range"].gt(0)
    )
    cleaned["Model Year Cohort"] = pd.cut(
        cleaned["Model Year"].astype("float"),
        bins=[0, 2014, 2017, 2020, 2023, np.inf],
        labels=["2014 and earlier", "2015-2017", "2018-2020", "2021-2023", "2024+"],
        right=True,
    )
    return cleaned


def build_data_quality_summary(raw: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("raw_rows", len(raw)),
        ("raw_columns", raw.shape[1]),
        ("cleaned_rows", len(cleaned)),
        ("missing_original_electric_utility", raw["Electric Utility"].isna().sum()),
        ("standardized_utility_count", cleaned["Utility Standardized"].nunique()),
        ("missing_model_year", cleaned["Model Year"].isna().sum()),
        ("min_model_year", cleaned["Model Year"].min()),
        ("max_model_year", cleaned["Model Year"].max()),
        ("missing_electric_range", cleaned["Electric Range"].isna().sum()),
        ("zero_electric_range_records", cleaned["Electric Range"].eq(0).sum()),
        ("negative_electric_range_records", cleaned["Electric Range"].lt(0).sum()),
        ("bev_records", cleaned["Is BEV"].sum()),
        ("phev_records", cleaned["Is PHEV"].sum()),
    ]
    return pd.DataFrame(checks, columns=["check", "value"])


def build_utility_summary(cleaned: pd.DataFrame) -> pd.DataFrame:
    grouped = cleaned.groupby("Utility Standardized", dropna=False)
    summary = grouped.agg(
        total_ev_count=("DOL Vehicle ID", "count"),
        bev_count=("Is BEV", "sum"),
        phev_count=("Is PHEV", "sum"),
        recent_model_year_count=("Is Recent Model Year", "sum"),
        average_electric_range=("Electric Range", "mean"),
        median_electric_range=("Electric Range", "median"),
        average_positive_electric_range=("Range Positive", "mean"),
        median_positive_electric_range=("Range Positive", "median"),
        min_model_year=("Model Year", "min"),
        median_model_year=("Model Year", "median"),
        max_model_year=("Model Year", "max"),
        county_count=("County", "nunique"),
        city_count=("City", "nunique"),
    ).reset_index()

    summary["bev_share"] = summary["bev_count"] / summary["total_ev_count"]
    summary["phev_share"] = summary["phev_count"] / summary["total_ev_count"]
    summary["recent_model_year_share"] = (
        summary["recent_model_year_count"] / summary["total_ev_count"]
    )
    ordered_columns = [
        "Utility Standardized",
        "total_ev_count",
        "bev_count",
        "bev_share",
        "phev_count",
        "phev_share",
        "recent_model_year_count",
        "recent_model_year_share",
        "average_electric_range",
        "median_electric_range",
        "average_positive_electric_range",
        "median_positive_electric_range",
        "min_model_year",
        "median_model_year",
        "max_model_year",
        "county_count",
        "city_count",
    ]
    return summary[ordered_columns].sort_values(
        ["total_ev_count", "bev_share"], ascending=[False, False]
    )


def build_growth_ranking(
    utility_summary: pd.DataFrame, min_utility_count: int
) -> pd.DataFrame:
    ranking = utility_summary[
        utility_summary["total_ev_count"].ge(min_utility_count)
    ].copy()
    ranking["growth_rank_score"] = ranking["recent_model_year_share"]
    ranking = ranking.sort_values(
        ["growth_rank_score", "recent_model_year_count", "total_ev_count"],
        ascending=[False, False, False],
    )
    ranking.insert(0, "growth_rank", range(1, len(ranking) + 1))
    return ranking


def build_cohort_distribution(cleaned: pd.DataFrame) -> pd.DataFrame:
    cohort_counts = (
        cleaned.groupby(["Utility Standardized", "Model Year Cohort"], observed=False)
        .size()
        .reset_index(name="cohort_count")
    )
    totals = cleaned.groupby("Utility Standardized").size().rename("utility_total")
    cohort_counts = cohort_counts.merge(totals, on="Utility Standardized")
    cohort_counts["cohort_share"] = (
        cohort_counts["cohort_count"] / cohort_counts["utility_total"]
    )
    return cohort_counts.sort_values(
        ["Utility Standardized", "Model Year Cohort"]
    ).reset_index(drop=True)


def shorten_label(label: str, max_length: int = 38) -> str:
    if len(label) <= max_length:
        return label
    return label[: max_length - 3].rstrip() + "..."


def write_horizontal_bar_svg(
    data: pd.DataFrame,
    label_column: str,
    value_column: str,
    output_path: Path,
    title: str,
    value_format: str = "{:,.0f}",
) -> None:
    plot_data = data[[label_column, value_column]].copy()
    plot_data = plot_data.sort_values(value_column, ascending=True)

    width = 1100
    row_height = 34
    left_margin = 360
    right_margin = 170
    top_margin = 70
    bottom_margin = 35
    height = top_margin + bottom_margin + row_height * len(plot_data)
    max_value = float(plot_data[value_column].max()) if len(plot_data) else 1.0
    bar_area = width - left_margin - right_margin

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="38" font-family="Arial" font-size="24" font-weight="700" fill="#202020">{title}</text>',
    ]

    for index, (_, row) in enumerate(plot_data.iterrows()):
        y = top_margin + index * row_height
        value = float(row[value_column])
        bar_width = 0 if max_value == 0 else (value / max_value) * bar_area
        label = shorten_label(str(row[label_column]))
        value_text = value_format.format(value)
        lines.extend(
            [
                f'<text x="24" y="{y + 22}" font-family="Arial" font-size="14" fill="#202020">{label}</text>',
                f'<rect x="{left_margin}" y="{y + 6}" width="{bar_width:.1f}" height="22" fill="#2f7f6f"/>',
                f'<text x="{left_margin + bar_width + 8:.1f}" y="{y + 22}" font-family="Arial" font-size="14" fill="#202020">{value_text}</text>',
            ]
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    def escape_cell(value: object) -> str:
        return str(value).replace("|", r"\|")

    display = df.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            if "share" in column.lower():
                display[column] = display[column].map(lambda value: f"{value:.1%}")
            else:
                display[column] = display[column].map(lambda value: f"{value:,.2f}")
        elif pd.api.types.is_integer_dtype(display[column]):
            display[column] = display[column].map(lambda value: f"{value:,}")
        else:
            display[column] = display[column].astype(str)

    headers = [escape_cell(column) for column in display.columns]
    rows = display.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(escape_cell(value) for value in row) + " |")
    return "\n".join(lines)


def write_markdown_summary(
    output_path: Path,
    input_path: Path,
    cleaned: pd.DataFrame,
    utility_summary: pd.DataFrame,
    growth_ranking: pd.DataFrame,
    recent_year: int,
    min_utility_count: int,
) -> None:
    top_count = utility_summary.head(5)[
        ["Utility Standardized", "total_ev_count", "bev_share", "recent_model_year_share"]
    ]
    top_growth = growth_ranking.head(5)[
        ["growth_rank", "Utility Standardized", "total_ev_count", "recent_model_year_share"]
    ]

    content = f"""# EV Utility Footprint Analysis Summary

Dataset source: `{input_path}`

Rows analyzed: {len(cleaned):,}

Utilities analyzed: {cleaned["Utility Standardized"].nunique():,}

Recent model-year cutoff: `{recent_year}`

Minimum utility size for growth ranking: `{min_utility_count}` vehicles

## Main Assumptions

- Electric Utility is used as the primary grouping variable because utilities are directly affected by EV charging demand.
- Model year is used as a proxy for adoption recency because the dataset does not include a registration date for every record.
- Utility names are standardized for whitespace, case, and separator differences; records with missing utility names are retained as `UNKNOWN UTILITY`.
- Electric range values of 0 are kept in the cleaned data, but positive-range averages and medians are reported separately.

## Largest Utility Territories

{dataframe_to_markdown(top_count)}

## Fastest-Growing Utility Territories

{dataframe_to_markdown(top_growth)}

## Files Produced

- `cleaned_ev_population.csv`
- `data_quality_summary.csv`
- `utility_footprint_summary.csv`
- `fastest_growing_utilities.csv`
- `model_year_cohort_distribution.csv`
- `top_utilities_by_ev_count.svg`
- `top_utilities_by_recent_share.svg`
"""
    output_path.write_text(textwrap.dedent(content), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(args.input)
    cleaned = load_and_clean(args.input, args.recent_year)
    data_quality = build_data_quality_summary(raw, cleaned)
    utility_summary = build_utility_summary(cleaned)
    growth_ranking = build_growth_ranking(utility_summary, args.min_utility_count)
    cohort_distribution = build_cohort_distribution(cleaned)

    cleaned.to_csv(args.output_dir / "cleaned_ev_population.csv", index=False)
    data_quality.to_csv(args.output_dir / "data_quality_summary.csv", index=False)
    utility_summary.to_csv(
        args.output_dir / "utility_footprint_summary.csv", index=False
    )
    growth_ranking.to_csv(
        args.output_dir / "fastest_growing_utilities.csv", index=False
    )
    cohort_distribution.to_csv(
        args.output_dir / "model_year_cohort_distribution.csv", index=False
    )

    write_horizontal_bar_svg(
        utility_summary.head(15),
        "Utility Standardized",
        "total_ev_count",
        args.output_dir / "top_utilities_by_ev_count.svg",
        "Top Utilities by EV Count",
    )
    write_horizontal_bar_svg(
        growth_ranking.head(15),
        "Utility Standardized",
        "recent_model_year_share",
        args.output_dir / "top_utilities_by_recent_share.svg",
        f"Top Utilities by Share of Model Year {args.recent_year}+ EVs",
        value_format="{:.1%}",
    )
    write_markdown_summary(
        args.output_dir / "analysis_summary.md",
        args.input,
        cleaned,
        utility_summary,
        growth_ranking,
        args.recent_year,
        args.min_utility_count,
    )

    print(f"Analysis complete. Results written to: {args.output_dir}")
    print("Top utility by EV count:")
    print(utility_summary.head(1).to_string(index=False))
    print("\nTop utility by recent model-year share:")
    print(growth_ranking.head(1).to_string(index=False))


if __name__ == "__main__":
    main()
