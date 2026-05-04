import argparse
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_DIR / "Electric_Vehicle_Population_Data.csv"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs"
RECENT_YEAR = 2022
MIN_UTILITY_COUNT = 100

REQUIRED_COLUMNS = [
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

COHORT_LABELS = [
    "2014 and earlier",
    "2015-2017",
    "2018-2020",
    "2021-2023",
    "2024+",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--recent-year", type=int, default=RECENT_YEAR)
    parser.add_argument("--min-utility-count", type=int, default=MIN_UTILITY_COUNT)
    return parser.parse_args()


def clean_utility_name(value):
    if pd.isna(value):
        return "UNKNOWN UTILITY"

    text = str(value).upper().strip()
    text = text.replace("||", "|")

    pieces = []
    for part in text.split("|"):
        part = " ".join(part.split())
        if part:
            pieces.append(part)

    if not pieces:
        return "UNKNOWN UTILITY"
    return " | ".join(pieces)


def read_data(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find dataset: {csv_path}")

    df = pd.read_csv(csv_path)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    return df


def clean_data(raw_df, recent_year):
    df = raw_df[REQUIRED_COLUMNS].copy()

    text_cols = [
        "County",
        "City",
        "State",
        "Make",
        "Model",
        "Electric Vehicle Type",
        "Clean Alternative Fuel Vehicle (CAFV) Eligibility",
    ]

    for col in text_cols:
        df[col] = df[col].fillna("UNKNOWN").astype(str).str.upper().str.strip()
        df[col] = df[col].str.replace(r"\s+", " ", regex=True)

    df["Utility Standardized"] = df["Electric Utility"].apply(clean_utility_name)
    df["Model Year"] = pd.to_numeric(df["Model Year"], errors="coerce").astype("Int64")
    df["Electric Range"] = pd.to_numeric(df["Electric Range"], errors="coerce")
    df["Postal Code"] = pd.to_numeric(df["Postal Code"], errors="coerce")

    df["Is BEV"] = df["Electric Vehicle Type"] == "BATTERY ELECTRIC VEHICLE (BEV)"
    df["Is PHEV"] = df["Electric Vehicle Type"] == "PLUG-IN HYBRID ELECTRIC VEHICLE (PHEV)"
    df["Is Recent Model Year"] = df["Model Year"] >= recent_year

    # Keep positive range separately because a lot of rows use 0.
    df["Range Positive"] = df["Electric Range"].where(df["Electric Range"] > 0)

    df["Model Year Cohort"] = pd.cut(
        df["Model Year"].astype(float),
        bins=[0, 2014, 2017, 2020, 2023, np.inf],
        labels=COHORT_LABELS,
    )

    return df


def make_data_quality_summary(raw_df, clean_df):
    rows = [
        ["raw_rows", len(raw_df)],
        ["raw_columns", raw_df.shape[1]],
        ["cleaned_rows", len(clean_df)],
        ["missing_original_electric_utility", raw_df["Electric Utility"].isna().sum()],
        ["standardized_utility_count", clean_df["Utility Standardized"].nunique()],
        ["missing_model_year", clean_df["Model Year"].isna().sum()],
        ["min_model_year", clean_df["Model Year"].min()],
        ["max_model_year", clean_df["Model Year"].max()],
        ["missing_electric_range", clean_df["Electric Range"].isna().sum()],
        ["zero_electric_range_records", (clean_df["Electric Range"] == 0).sum()],
        ["zero_electric_range_share", (clean_df["Electric Range"] == 0).mean()],
        ["negative_electric_range_records", (clean_df["Electric Range"] < 0).sum()],
        ["unknown_utility_records", (clean_df["Utility Standardized"] == "UNKNOWN UTILITY").sum()],
        ["bev_records", clean_df["Is BEV"].sum()],
        ["phev_records", clean_df["Is PHEV"].sum()],
    ]
    return pd.DataFrame(rows, columns=["check", "value"])


def make_utility_summary(clean_df):
    grouped = clean_df.groupby("Utility Standardized", dropna=False)

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

    column_order = [
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

    summary = summary[column_order]
    summary = summary.sort_values(["total_ev_count", "bev_share"], ascending=[False, False])
    return summary


def make_recent_adoption_ranking(utility_summary, min_utility_count):
    ranking = utility_summary[utility_summary["total_ev_count"] >= min_utility_count].copy()
    ranking["recent_adoption_score"] = ranking["recent_model_year_share"]
    ranking = ranking.sort_values(
        ["recent_adoption_score", "recent_model_year_count", "total_ev_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    ranking.insert(0, "recent_adoption_rank", range(1, len(ranking) + 1))
    return ranking


def make_cohort_distribution(clean_df):
    cohort_counts = (
        clean_df.groupby(["Utility Standardized", "Model Year Cohort"], observed=False)
        .size()
        .reset_index(name="cohort_count")
    )
    totals = (
        clean_df.groupby("Utility Standardized")
        .size()
        .reset_index(name="utility_total")
    )
    cohort_counts = cohort_counts.merge(totals, on="Utility Standardized", how="left")
    cohort_counts["cohort_share"] = (
        cohort_counts["cohort_count"] / cohort_counts["utility_total"]
    )
    cohort_counts = cohort_counts.sort_values(["Utility Standardized", "Model Year Cohort"])
    return cohort_counts.reset_index(drop=True)


def shorten_label(label, max_length=38):
    if len(label) <= max_length:
        return label
    return label[: max_length - 3].rstrip() + "..."


def write_horizontal_bar_svg(data, label_column, value_column, output_path, title, value_format="{:,.0f}"):
    plot_df = data[[label_column, value_column]].copy()
    plot_df = plot_df.sort_values(value_column, ascending=True)

    width = 1100
    row_height = 34
    left_margin = 360
    right_margin = 170
    top_margin = 70
    bottom_margin = 35
    height = top_margin + bottom_margin + row_height * len(plot_df)
    max_value = float(plot_df[value_column].max()) if len(plot_df) else 1.0
    bar_area = width - left_margin - right_margin

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="38" font-family="Arial" font-size="24" font-weight="700" fill="#202020">{escape(title)}</text>',
    ]

    for i, (_, row) in enumerate(plot_df.iterrows()):
        y = top_margin + i * row_height
        value = float(row[value_column])
        bar_width = 0 if max_value == 0 else (value / max_value) * bar_area
        label = escape(shorten_label(str(row[label_column])))
        value_text = escape(value_format.format(value))

        svg_lines.append(
            f'<text x="24" y="{y + 22}" font-family="Arial" font-size="14" fill="#202020">{label}</text>'
        )
        svg_lines.append(
            f'<rect x="{left_margin}" y="{y + 6}" width="{bar_width:.1f}" height="22" fill="#2f7f6f"/>'
        )
        svg_lines.append(
            f'<text x="{left_margin + bar_width + 8:.1f}" y="{y + 22}" font-family="Arial" font-size="14" fill="#202020">{value_text}</text>'
        )

    svg_lines.append("</svg>")
    output_path.write_text("\n".join(svg_lines), encoding="utf-8")


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw_df = read_data(args.input)
    clean_df = clean_data(raw_df, args.recent_year)

    data_quality = make_data_quality_summary(raw_df, clean_df)
    utility_summary = make_utility_summary(clean_df)
    recent_ranking = make_recent_adoption_ranking(utility_summary, args.min_utility_count)
    cohort_distribution = make_cohort_distribution(clean_df)

    clean_df.to_csv(args.output_dir / "cleaned_ev_population.csv", index=False)
    data_quality.to_csv(args.output_dir / "data_quality_summary.csv", index=False)
    utility_summary.to_csv(args.output_dir / "utility_footprint_summary.csv", index=False)
    recent_ranking.to_csv(args.output_dir / "recent_adoption_utilities.csv", index=False)
    cohort_distribution.to_csv(args.output_dir / "model_year_cohort_distribution.csv", index=False)

    write_horizontal_bar_svg(
        utility_summary.head(15),
        "Utility Standardized",
        "total_ev_count",
        args.output_dir / "top_utilities_by_ev_count.svg",
        "Top Utilities by EV Count",
    )
    write_horizontal_bar_svg(
        recent_ranking.head(15),
        "Utility Standardized",
        "recent_model_year_share",
        args.output_dir / "top_utilities_by_recent_adoption_share.svg",
        f"Top Utilities by Share of Model Year {args.recent_year}+ EVs",
        value_format="{:.1%}",
    )
    print(f"Analysis complete. Results written to: {args.output_dir}")
    print("\nTop utility by EV count:")
    print(utility_summary.head(1).to_string(index=False))
    print("\nTop utility by recent-adoption share:")
    print(recent_ranking.head(1).to_string(index=False))


if __name__ == "__main__":
    main()
