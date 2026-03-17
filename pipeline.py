import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# Configuration
INPUT_PATH = 'data/transit_ridership.csv'
OUTPUT_PATH = 'output'

def load_data(file_path):
    """Loads the transit ridership CSV data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found at {file_path}")
    df = pd.read_csv(file_path)
    print(f"Data loaded. Initial shape: {df.shape}")
    return df

def clean_data(df):
    """Handles duplicates, standardizes categorical values, and fixes outliers."""
    # 1. Drop Duplicates
    df = df.drop_duplicates().reset_index(drop=True)
    
    # 2. Clean Vehicle Type
    def clean_vehicle(val):
        val = str(val).lower().strip()
        if 'mini' in val: return 'Minibus'
        if 'articulated' in val: return 'Articulated Bus'
        if 'std' in val or 'standard' in val: return 'Standard Bus'
        return val.title()
    
    df['vehicle_type'] = df['vehicle_type'].apply(clean_vehicle)
    
    # 3. Clean Direction
    def clean_direction(val):
        val = str(val).lower()
        if 'in' in val: return 'Inbound'
        if 'out' in val: return 'Outbound'
        return val
    
    df['direction'] = df['direction'].apply(clean_direction)
    
    # 4. Clean Holiday (mapping various formats to boolean)
    holiday_map = {
        'false': False, 'False': False, '0': False, 'No': False,
        'true': True, 'True': True, '1': True, 'Yes': True
    }
    df['is_holiday'] = df['is_holiday'].map(holiday_map)
    
    # 5. Fix Trip Duration Outliers & Impute Missing
    median_dur = df['trip_duration_min'].median()
    df.loc[(df['trip_duration_min'] < 0) | (df['trip_duration_min'] > 120), 'trip_duration_min'] = median_dur
    
    numeric_cols = ['boarding_count', 'alighting_count', 'temperature_c', 'trip_duration_min']
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())
        
    # 6. Convert and Clean Dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']).reset_index(drop=True)
    
    print(f"Data cleaned. Cleaned shape: {df.shape}")
    return df

def add_features(df):
    """Adds derived features like total ridership and categorical month."""
    df['total_ridership'] = df['boarding_count'] + df['alighting_count']
    df['month'] = df['date'].dt.month_name()
    
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    df['month'] = pd.Categorical(df['month'], categories=month_order, ordered=True)
    
    return df

def generate_summary(df, output_dir):
    """Generates a summary JSON of transit statistics."""
    total_trips = len(df)
    date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"
    
    route_totals = df.groupby('route_id')['boarding_count'].sum().sort_values(ascending=False)
    busiest_route = route_totals.index[0]
    avg_daily_ridership = df.groupby('date')['boarding_count'].sum().mean()
    
    ridership_by_vehicle = df.groupby('vehicle_type')['boarding_count'].sum().to_dict()
    ridership_by_weather = df.groupby('weather')['boarding_count'].sum().to_dict()
    
    top_5_routes = [
        {"route": route, "total_boardings": float(total)} 
        for route, total in route_totals.head(5).items()
    ]
    
    summary_data = {
        "total_trips": int(total_trips),
        "date_range": date_range,
        "busiest_route": busiest_route,
        "avg_daily_ridership": round(float(avg_daily_ridership), 1),
        "ridership_by_vehicle_type": {k: float(v) for k, v in ridership_by_vehicle.items()},
        "ridership_by_weather": {k: float(v) for k, v in ridership_by_weather.items()},
        "top_5_routes_by_boarding": top_5_routes
    }
    
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'summary.json'), 'w') as f:
        json.dump(summary_data, f, indent=2)
    print("Summary JSON generated in output folder.")

def create_visualizations(df, output_dir):
    """Creates and saves all four EDA plots."""
    sns.set_theme(style="whitegrid")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Avg boarding by weather condition
    plt.figure(figsize=(10, 6))
    avg_boarding_weather = df.groupby('weather')['boarding_count'].mean().sort_values(ascending=False).reset_index()
    sns.barplot(data=avg_boarding_weather, x='weather', y='boarding_count', palette='Blues_d')
    plt.title('Average Boarding Count by Weather Condition')
    plt.ylabel('Average Boardings')
    plt.xlabel('Weather Condition')
    plt.savefig(os.path.join(output_dir, 'avg_boarding_weather.png'))
    plt.close()

    # 2. Avg trip duration by vehicle type
    plt.figure(figsize=(10, 6))
    avg_duration_vehicle = df.groupby('vehicle_type')['trip_duration_min'].mean().sort_values(ascending=False).reset_index()
    sns.barplot(data=avg_duration_vehicle, x='vehicle_type', y='trip_duration_min', palette='Oranges_d')
    plt.title('Average Trip Duration by Vehicle Type')
    plt.ylabel('Average Duration (min)')
    plt.xlabel('Vehicle Type')
    plt.savefig(os.path.join(output_dir, 'avg_duration_vehicle.png'))
    plt.close()

    # 3. Total boarding by route
    plt.figure(figsize=(10, 6))
    total_boarding_route = df.groupby('route_id')['boarding_count'].sum().sort_values(ascending=False).reset_index()
    sns.barplot(data=total_boarding_route, x='route_id', y='boarding_count', palette='Greens_d')
    plt.title('Total Boarding Count by Route')
    plt.ylabel('Total Boardings')
    plt.xlabel('Route ID')
    plt.savefig(os.path.join(output_dir, 'total_boarding_route.png'))
    plt.close()

    # 4. Monthly ridership (total boardings)
    plt.figure(figsize=(10, 6))
    # Using observed=True to handle Categorical data properly
    monthly_ridership = df.groupby('month', observed=True)['boarding_count'].sum().reset_index()
    sns.lineplot(data=monthly_ridership, x='month', y='boarding_count', marker='o', color='red', linewidth=2)
    plt.title('Monthly Ridership (Total Boardings)')
    plt.ylabel('Total Boardings')
    plt.xlabel('Month')
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(output_dir, 'monthly_ridership.png'))
    plt.close()
    
    print(f"All 4 visualizations saved successfully in: {output_dir}")

def main():
    df = load_data(INPUT_PATH)
    df = clean_data(df)
    df = add_features(df)
    generate_summary(df, OUTPUT_PATH)
    create_visualizations(df, OUTPUT_PATH)
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()