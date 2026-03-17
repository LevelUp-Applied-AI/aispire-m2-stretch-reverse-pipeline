import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
DATA_PATH = 'data/transit_ridership.csv'
OUTPUT_DIR = 'output'
TARGET_YEAR = 2024

# ------------------------------------------------------------
# 1. Load CSV with BOM handling and whitespace cleanup
# ------------------------------------------------------------
def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    df = pd.read_csv(filepath, encoding='utf-8-sig', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    print(f"Loaded {len(df)} records from {filepath}")
    return df

# ------------------------------------------------------------
# 2. Parse dates safely
# ------------------------------------------------------------
def parse_date(val):
    try:
        return pd.to_datetime(val, errors='coerce')
    except:
        return pd.NaT

# ------------------------------------------------------------
# 3. Clean categorical fields
# ------------------------------------------------------------
def clean_direction(val):
    if pd.isna(val):
        return np.nan
    s = str(val).lower().strip()
    if s.startswith('in'):
        return 'Inbound'
    elif s.startswith('out'):
        return 'Outbound'
    return np.nan

def clean_vehicle(val):
    if pd.isna(val):
        return np.nan
    s = str(val).lower().strip()
    if 'articulated' in s:
        return 'Articulated Bus'
    elif 'mini' in s:
        return 'Minibus'
    elif 'standard' in s or 'std' in s:
        return 'Standard Bus'
    return np.nan

def clean_weather(val):
    if pd.isna(val):
        return np.nan
    s = str(val).lower().strip()
    if 'clear' in s:
        return 'Clear'
    elif 'overcast' in s:
        return 'Overcast'
    elif 'rain' in s:
        return 'Rain'
    elif 'snow' in s:
        return 'Snow'
    return np.nan

# ------------------------------------------------------------
# 4. Clean numeric fields
# ------------------------------------------------------------
def clean_numeric(df, col):
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].fillna(0)
    df[col] = df[col].clip(lower=0)
    return df

# ------------------------------------------------------------
# 5. Clean entire DataFrame
# ------------------------------------------------------------
def clean_data(df):
    df = df.copy()

    # Strip and standardize route_id
    df['route_id'] = df['route_id'].astype(str).str.strip().str.upper()

    # Parse dates and filter by TARGET_YEAR
    df['date_parsed'] = df['date'].apply(parse_date)
    df = df[df['date_parsed'].dt.year == TARGET_YEAR]

    # Clean categorical columns
    df['direction_clean'] = df['direction'].apply(clean_direction)
    df['vehicle_type_clean'] = df['vehicle_type'].apply(clean_vehicle)
    df['weather_clean'] = df['weather'].apply(clean_weather)

    # Additional mapping to unify vehicle types
    df['vehicle_type_clean'] = df['vehicle_type_clean'].replace({
        'MINI BUS':'Minibus',
        'MINIBUS':'Minibus',
        'STD BUS':'Standard Bus',
        'STANDARD BUS':'Standard Bus',
        'ARTICULATED':'Articulated Bus'
    })

    # Additional mapping to unify weather
    df['weather_clean'] = df['weather_clean'].replace({
        'CLEAR SKY':'Clear',
        'OVERCAST SKY':'Overcast',
        'RAINY':'Rain',
        'SNOWY':'Snow'
    })

    # Clean numeric columns
    df = clean_numeric(df, 'boarding_count')
    df = clean_numeric(df, 'alighting_count')

    # Drop rows with missing essential categories
    df = df.dropna(subset=['route_id','direction_clean','vehicle_type_clean','weather_clean'])

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove negative counts
    df = df[(df['boarding_count'] >= 0) & (df['alighting_count'] >= 0)]

    # Compute total passengers
    df['total_passengers'] = df['boarding_count'] + df['alighting_count']

    print(f"Cleaned data: {len(df)} records")
    return df

# ------------------------------------------------------------
# 6. Generate summary statistics
# ------------------------------------------------------------
def generate_summary(df):
    total_trips = len(df)
    min_date = df['date_parsed'].min().strftime('%Y-%m-%d')
    max_date = df['date_parsed'].max().strftime('%Y-%m-%d')
    date_range = f"{min_date} to {max_date}"

    route_boardings = df.groupby('route_id')['boarding_count'].sum()
    busiest_route = route_boardings.idxmax()

    top_5_routes = [
        {'route': r, 'total_boardings': int(v)}
        for r, v in route_boardings.sort_values(ascending=False).head(5).items()
    ]

    avg_daily_ridership = round(df['total_passengers'].sum() / 365, 1)

    vehicle_ridership = {k: int(v) for k, v in df.groupby('vehicle_type_clean')['total_passengers'].sum().items()}
    weather_ridership = {k: int(v) for k, v in df.groupby('weather_clean')['total_passengers'].sum().items()}

    summary = {
        "total_trips": total_trips,
        "date_range": date_range,
        "busiest_route": busiest_route,
        "avg_daily_ridership": avg_daily_ridership,
        "ridership_by_vehicle_type": vehicle_ridership,
        "ridership_by_weather": weather_ridership,
        "top_5_routes_by_boarding": top_5_routes
    }
    return summary

# ------------------------------------------------------------
# 7. Create visualizations
# ------------------------------------------------------------
def create_visualizations(df, output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')

    # Daily ridership
    daily = df.groupby(df['date_parsed'].dt.date)['total_passengers'].sum()
    plt.figure(figsize=(12, 5))
    plt.plot(daily.index, daily.values, color='steelblue')
    plt.title('Daily Total Ridership')
    plt.xlabel('Date')
    plt.ylabel('Passengers')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/daily_ridership.png', dpi=150)
    plt.close()

    # Ridership by vehicle type
    vehicle_ridership = df.groupby('vehicle_type_clean')['total_passengers'].sum()
    plt.figure(figsize=(8, 5))
    plt.bar(vehicle_ridership.index, vehicle_ridership.values, color=['#4c72b0', '#55a868', '#c44e52'])
    plt.title('Total Ridership by Vehicle Type')
    plt.ylabel('Total Passengers')
    for i, v in enumerate(vehicle_ridership.values):
        plt.text(i, v + 5000, f'{v:,}', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/ridership_by_vehicle.png', dpi=150)
    plt.close()

    # Ridership by weather
    weather_ridership = df.groupby('weather_clean')['total_passengers'].sum()
    plt.figure(figsize=(8, 5))
    plt.bar(weather_ridership.index, weather_ridership.values, color=['#ffb84d', '#7f8c8d', '#5dade2', '#a569bd'])
    plt.title('Total Ridership by Weather')
    plt.ylabel('Total Passengers')
    for i, v in enumerate(weather_ridership.values):
        plt.text(i, v + 5000, f'{v:,}', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/ridership_by_weather.png', dpi=150)
    plt.close()

    # Top 5 routes by boardings
    top_routes = df.groupby('route_id')['boarding_count'].sum().sort_values(ascending=False).head(5)
    plt.figure(figsize=(8, 5))
    plt.bar(top_routes.index, top_routes.values, color='#2ecc71')
    plt.title('Top 5 Routes by Total Boardings')
    plt.ylabel('Boardings')
    for i, v in enumerate(top_routes.values):
        plt.text(i, v + 2000, f'{v:,}', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_routes.png', dpi=150)
    plt.close()

# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------
def main():
    df = load_data(DATA_PATH)
    df = clean_data(df)
    summary = generate_summary(df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f'{OUTPUT_DIR}/summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))

    create_visualizations(df)
    print("\nPipeline completed successfully!")
    print(f"Generated files in '{OUTPUT_DIR}' directory.")

# ------------------------------------------------------------
if __name__ == '__main__':
    main()