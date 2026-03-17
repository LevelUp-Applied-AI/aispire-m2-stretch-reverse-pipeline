import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = "data/transit_ridership.csv"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

VALID_ROUTES = {
    "R101", "R102", "R103", "R104", "R105",
    "R205", "R206", "R207", "R208",
    "R301", "R302"
}

VALID_WEATHER = {"Clear", "Overcast", "Rain", "Snow"}


def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def parse_mixed_date(value):
    if pd.isna(value):
        return pd.NaT

    s = str(value).strip()
    if not s:
        return pd.NaT

    # 1) YYYY-MM-DD
    try:
        dt = pd.to_datetime(s, format="%Y-%m-%d", errors="raise")
        if dt.year == 2024:
            return dt
    except Exception:
        pass

    # 2) مثل 03/06/2024 أو 06/21/2024
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = pd.to_datetime(s, format=fmt, errors="raise")
            if dt.year == 2024:
                return dt
        except Exception:
            pass

    # 3) مثل 14-Aug-2024
    for fmt in ("%d-%b-%Y", "%d-%B-%Y"):
        try:
            dt = pd.to_datetime(s, format=fmt, errors="raise")
            if dt.year == 2024:
                return dt
        except Exception:
            pass

    # 4) fallback
    dt = pd.to_datetime(s, errors="coerce")
    if pd.notna(dt) and dt.year == 2024:
        return dt

    return pd.NaT


def clean_date_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = df["date"].apply(parse_mixed_date)
    df = df.dropna(subset=["date"]).copy()
    return df


def normalize_route_id(value):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().upper()
    s = s.replace(" ", "").replace("-", "")
    match = re.search(r"R?(\d{3})", s)
    if match:
        route = f"R{match.group(1)}"
        if route in VALID_ROUTES:
            return route
    return pd.NA


def normalize_direction(value):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().lower()
    s = s.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s)

    mapping = {
        "inbound": "Inbound",
        "in": "Inbound",
        "inbnd": "Inbound",
        "outbound": "Outbound",
        "out": "Outbound",
        "outbnd": "Outbound",
    }

    return mapping.get(s, pd.NA)


def normalize_vehicle_type(value):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().lower()
    s = s.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s)

    mapping = {
        "standard bus": "Standard Bus",
        "std bus": "Standard Bus",
        "stdbus": "Standard Bus",
        "standard": "Standard Bus",
        "minibus": "Minibus",
        "mini bus": "Minibus",
        "articulated bus": "Articulated Bus",
        "articulated": "Articulated Bus",
    }

    return mapping.get(s, pd.NA)


def normalize_weather(value):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().title()
    return s if s in VALID_WEATHER else pd.NA


def normalize_holiday(value):
    if pd.isna(value):
        return pd.NA

    s = str(value).strip().lower()
    mapping = {
        "false": False,
        "no": False,
        "0": False,
        "true": True,
        "yes": True,
        "1": True,
    }
    return mapping.get(s, pd.NA)


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["route_id"] = df["route_id"].apply(normalize_route_id)
    df["direction"] = df["direction"].apply(normalize_direction)
    df["vehicle_type"] = df["vehicle_type"].apply(normalize_vehicle_type)
    df["weather"] = df["weather"].apply(normalize_weather)
    df["is_holiday"] = df["is_holiday"].apply(normalize_holiday)

    holiday_mode = df["is_holiday"].mode(dropna=True)
    if not holiday_mode.empty:
        df["is_holiday"] = df["is_holiday"].fillna(holiday_mode.iloc[0])

    df = df.dropna(subset=["route_id", "direction", "vehicle_type", "weather"]).copy()
    return df


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    num_cols = [
        "boarding_count",
        "alighting_count",
        "trip_duration_min",
        "temperature_c",
    ]

    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # flags before filling
    df["boarding_missing_orig"] = df["boarding_count"].isna()
    df["alighting_missing_orig"] = df["alighting_count"].isna()
    df["duration_missing_orig"] = df["trip_duration_min"].isna()
    df["temp_missing_orig"] = df["temperature_c"].isna()

    # invalid => NaN
    df.loc[df["boarding_count"] < 0, "boarding_count"] = pd.NA
    df.loc[df["alighting_count"] < 0, "alighting_count"] = pd.NA
    df.loc[df["trip_duration_min"] <= 0, "trip_duration_min"] = pd.NA
    df.loc[(df["temperature_c"] < -40) | (df["temperature_c"] > 60), "temperature_c"] = pd.NA

    # extreme trip duration as invalid
    df.loc[df["trip_duration_min"] > 180, "trip_duration_min"] = pd.NA

    # fill with median
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())

    return df


def remove_suspect_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # صفوف boarding_count كان ناقص فيها بالأصل
    # ومعها أكثر من إشارة مشكلة إضافية
    suspect_mask = (
        df["boarding_missing_orig"] &
        (
            df["alighting_missing_orig"] |
            df["duration_missing_orig"] |
            df["temp_missing_orig"]
        )
    )

    df = df[~suspect_mask].copy()
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # exact duplicates
    df = df.drop_duplicates().copy()

    # duplicates after normalization
    dedupe_cols = [
        "date",
        "route_id",
        "direction",
        "boarding_count",
        "alighting_count",
        "vehicle_type",
        "trip_duration_min",
        "weather",
        "temperature_c",
        "is_holiday",
    ]
    df = df.drop_duplicates(subset=dedupe_cols).copy()

    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    df = clean_date_column(df)
    df = clean_text_columns(df)
    df = clean_numeric_columns(df)
    df = remove_suspect_rows(df)
    df = remove_duplicates(df)

    df = df.sort_values("date").reset_index(drop=True)
    return df


def build_summary(df: pd.DataFrame) -> dict:
    daily_boardings = df.groupby("date")["boarding_count"].sum()
    avg_daily_ridership = round(daily_boardings.mean(), 1)

    ridership_by_vehicle_type = (
        df.groupby("vehicle_type")["boarding_count"]
        .sum()
        .round()
        .astype(int)
        .sort_index()
        .to_dict()
    )

    ridership_by_weather = (
        df.groupby("weather")["boarding_count"]
        .sum()
        .round()
        .astype(int)
        .sort_index()
        .to_dict()
    )

    route_totals = (
        df.groupby("route_id")["boarding_count"]
        .sum()
        .sort_values(ascending=False)
    )

    busiest_route = route_totals.index[0]

    top_5_routes_by_boarding = [
        {"route": route, "total_boardings": int(total)}
        for route, total in route_totals.head(5).items()
    ]

    summary = {
        "total_trips": int(len(df)),
        "date_range": f'{df["date"].min().strftime("%Y-%m-%d")} to {df["date"].max().strftime("%Y-%m-%d")}',
        "busiest_route": busiest_route,
        "avg_daily_ridership": avg_daily_ridership,
        "ridership_by_vehicle_type": ridership_by_vehicle_type,
        "ridership_by_weather": ridership_by_weather,
        "top_5_routes_by_boarding": top_5_routes_by_boarding,
    }

    return summary


def save_summary(summary: dict) -> None:
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def create_monthly_ridership_chart(df: pd.DataFrame) -> None:
    chart_df = df.copy()
    chart_df["month"] = chart_df["date"].dt.to_period("M").astype(str)
    monthly = chart_df.groupby("month")["boarding_count"].sum()

    plt.figure(figsize=(10, 5))
    monthly.plot(kind="line", marker="o")
    plt.title("Monthly Ridership")
    plt.xlabel("Month")
    plt.ylabel("Total Boardings")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "monthly_ridership.png")
    plt.close()


def create_top_routes_chart(df: pd.DataFrame) -> None:
    top_routes = (
        df.groupby("route_id")["boarding_count"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 5))
    top_routes.plot(kind="bar")
    plt.title("Top Routes by Boarding Count")
    plt.xlabel("Route ID")
    plt.ylabel("Total Boardings")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "top_routes.png")
    plt.close()


def create_avg_duration_vehicle_chart(df: pd.DataFrame) -> None:
    avg_duration = (
        df.groupby("vehicle_type")["trip_duration_min"]
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    avg_duration.plot(kind="bar")
    plt.title("Average Trip Duration by Vehicle Type")
    plt.xlabel("Vehicle Type")
    plt.ylabel("Average Duration (min)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "avg_duration_vehicle.png")
    plt.close()


def create_avg_boardings_weather_chart(df: pd.DataFrame) -> None:
    avg_boardings = (
        df.groupby("weather")["boarding_count"]
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    avg_boardings.plot(kind="bar")
    plt.title("Average Boardings by Weather")
    plt.xlabel("Weather")
    plt.ylabel("Average Boardings")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "avg_boardings_weather.png")
    plt.close()


def create_charts(df: pd.DataFrame) -> None:
    create_monthly_ridership_chart(df)
    create_top_routes_chart(df)
    create_avg_duration_vehicle_chart(df)
    create_avg_boardings_weather_chart(df)


def main():
    df = load_data(DATA_PATH)
    cleaned_df = clean_data(df)
    summary = build_summary(cleaned_df)

    save_summary(summary)
    create_charts(cleaned_df)

    print("Pipeline completed successfully.")
    print(f"Cleaned rows: {len(cleaned_df)}")
    print("\nGenerated summary:")
    print(json.dumps(summary, indent=2))
    print(f"\nOutputs saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()