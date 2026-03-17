import os
import json
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "data/transit_ridership.csv"
OUTPUT_DIR = "output"


def load_data(filepath):
    """Load the raw CSV into a DataFrame."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} rows from {filepath}")
    return df


def clean_data(df):
    """Clean and standardize the raw transit ridership data."""
    df = df.copy()

    print(f"Initial rows: {len(df)}")

    # Remove exact duplicates
    df = df.drop_duplicates()
    print(f"After drop_duplicates: {len(df)}")

    # ----------------------------
    # Standardize text columns
    # ----------------------------
    df["route_id"] = df["route_id"].astype(str).str.strip().str.upper()
    df["direction"] = df["direction"].astype(str).str.strip()
    df["vehicle_type"] = df["vehicle_type"].astype(str).str.strip()
    df["weather"] = df["weather"].astype(str).str.strip().str.title()
    df["is_holiday"] = df["is_holiday"].astype(str).str.strip().str.lower()

    # ----------------------------
    # Fix direction variants
    # ----------------------------
    direction_map = {
        "Inbound": "Inbound",
        "INBOUND": "Inbound",
        "inbound": "Inbound",
        "In": "Inbound",
        "Inbnd": "Inbound",
        "Outbound": "Outbound",
        "OUTBOUND": "Outbound",
        "outbound": "Outbound",
        "Out": "Outbound",
        "Outbnd": "Outbound",
    }
    df["direction"] = df["direction"].replace(direction_map)

    # ----------------------------
    # Fix vehicle type variants
    # ----------------------------
    vehicle_map = {
        "Minibus": "Minibus",
        "MINIBUS": "Minibus",
        "mini bus": "Minibus",
        "Standard Bus": "Standard Bus",
        "standard bus": "Standard Bus",
        "Std Bus": "Standard Bus",
        "std bus": "Standard Bus",
        "Articulated Bus": "Articulated Bus",
        "articulated": "Articulated Bus",
    }
    df["vehicle_type"] = df["vehicle_type"].replace(vehicle_map)

    # ----------------------------
    # Parse dates
    # ----------------------------
    try:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    except TypeError:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ----------------------------
    # Convert numerics
    # ----------------------------
    
    # Convert numerics
    numeric_cols = [
        "boarding_count",
        "alighting_count",
        "trip_duration_min",
        "temperature_c",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill supporting numeric columns with global median
    df["alighting_count"] = df["alighting_count"].fillna(df["alighting_count"].median())
    df["trip_duration_min"] = df["trip_duration_min"].fillna(df["trip_duration_min"].median())
    df["temperature_c"] = df["temperature_c"].fillna(df["temperature_c"].median())

    # Fill boarding_count using median within each route
    df["boarding_count"] = df.groupby("route_id")["boarding_count"].transform(
        lambda s: s.fillna(s.median())
    )

    # If any boarding_count values are still missing after route fill, use overall median
    df["boarding_count"] = df["boarding_count"].fillna(df["boarding_count"].median())

    # ----------------------------
    # Fill missing numeric values
    # ----------------------------
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    # ----------------------------
    # Standardize holiday values
    # ----------------------------
    holiday_map = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "1": True,
        "0": False,
    }
    df["is_holiday"] = df["is_holiday"].replace(holiday_map)

    # ----------------------------
    # Keep valid dates only
    # ----------------------------
    df = df[df["date"].notna()]
    df = df[df["date"].dt.year == 2024]
    print(f"After date cleaning: {len(df)}")

    # ----------------------------
    # Keep only valid categories
    # ----------------------------
    df = df[df["direction"].isin(["Inbound", "Outbound"])]
    df = df[df["vehicle_type"].isin(["Minibus", "Standard Bus", "Articulated Bus"])]
    df = df[df["weather"].isin(["Clear", "Overcast", "Rain", "Snow"])]
    print(f"After category cleaning: {len(df)}")

    # ----------------------------
    # Remove invalid route ids
    # ----------------------------
    valid_routes = [
        "R101", "R102", "R103", "R104", "R105", "R112",
        "R205", "R206", "R207", "R208",
        "R301", "R302"
    ]
    df = df[df["route_id"].isin(valid_routes)]
    print(f"After route filtering: {len(df)}")

    # ----------------------------
    # Remove impossible values
    # ----------------------------
    df = df[df["boarding_count"] >= 0]
    df = df[df["alighting_count"] >= 0]
    df = df[df["trip_duration_min"] >= 0]
    print(f"After removing invalid numerics: {len(df)}")

    return df

def generate_summary(df):
    """Generate the summary dictionary."""
    daily_totals = df.groupby("date")["boarding_count"].sum()

    route_totals = (
        df.groupby("route_id")["boarding_count"]
        .sum()
        .sort_values(ascending=False)
    )

    summary = {
        "total_trips": int(len(df)),
        "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
        "busiest_route": route_totals.idxmax(),
        "avg_daily_ridership": round(daily_totals.mean(), 1),
        "ridership_by_vehicle_type": {
            key: int(value)
            for key, value in df.groupby("vehicle_type")["boarding_count"].sum().to_dict().items()
        },
        "ridership_by_weather": {
            key: int(value)
            for key, value in df.groupby("weather")["boarding_count"].sum().to_dict().items()
        },
        "top_5_routes_by_boarding": [
            {"route": route, "total_boardings": int(total)}
            for route, total in route_totals.head(5).items()
        ],
    }

    return summary


def save_summary(summary, output_dir):
    """Save summary.json to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {output_path}")


def create_visualizations(df, output_dir):
    """Create and save the four expected charts."""
    os.makedirs(output_dir, exist_ok=True)

    plt.style.use("ggplot")

    # 1) Monthly Ridership
    monthly_ridership = df.groupby(df["date"].dt.to_period("M"))["boarding_count"].sum()
    monthly_ridership.index = monthly_ridership.index.astype(str)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly_ridership.index, monthly_ridership.values, marker="o", linewidth=2, color="#2E86AB")
    ax.set_title("Monthly Ridership (Total Boardings)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Boardings")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "monthly_ridership.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 2) Ridership by Route
    route_totals = df.groupby("route_id")["boarding_count"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(route_totals.index, route_totals.values, color="#F6C85F")
    ax.set_title("Total Boardings by Route")
    ax.set_xlabel("Total Boardings")
    ax.set_ylabel("Route")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "ridership_by_route.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 3) Vehicle Utilization
    vehicle_duration = df.groupby("vehicle_type")["trip_duration_min"].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    vehicle_colors = {
    "Minibus": "#2E86AB",
    "Standard Bus": "#F6C85F",
    "Articulated Bus": "#6F4E7C"
}

    colors = [vehicle_colors[v] for v in vehicle_duration.index]

    ax.bar(vehicle_duration.index, vehicle_duration.values, color=colors)
    ax.set_title("Average Trip Duration by Vehicle Type")
    ax.set_xlabel("Vehicle Type")
    ax.set_ylabel("Average Trip Duration (min)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "vehicle_utilization.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 4) Weather Impact
    weather_boardings = df.groupby("weather")["boarding_count"].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    weather_colors = {
    "Clear": "#FFD93D",
    "Rain": "#4D96FF",
    "Snow": "#A9A9A9",
    "Overcast": "#6C757D"
}

    colors = [weather_colors[w] for w in weather_boardings.index]

    ax.bar(weather_boardings.index, weather_boardings.values, color=colors)
    ax.set_title("Average Boardings by Weather Condition")
    ax.set_xlabel("Weather Condition")
    ax.set_ylabel("Average Boardings per Trip")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "weather_impact.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved charts to {output_dir}")


def main():
    df = load_data(DATA_PATH)
    df = clean_data(df)

    summary = generate_summary(df)
    save_summary(summary, OUTPUT_DIR)
    create_visualizations(df, OUTPUT_DIR)

    print(json.dumps(summary, indent=2))
    print("Pipeline complete.")


if __name__ == "__main__":
    main()