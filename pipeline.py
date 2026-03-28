import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

DATA_PATH = 'data\transit_ridership.csv'
OUTPUT_DIR = 'output'

def load_data(filepath):
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} records from {filepath}")
    return df

def clean_data(df):
    df['boarding_count'] = df['boarding_count'].fillna(df['boarding_count'].median())
    df['alighting_count'] = df['alighting_count'].fillna(df['alighting_count'].median())
    df['trip_duration_min'] = df['trip_duration_min'].fillna(df['trip_duration_min'].median())
    df['temperature_c'] = df['temperature_c'].fillna(df['temperature_c'].median())

    df['date'] = df['date'].astype(str)
    date1 = pd.to_datetime(df['date'], errors='coerce')
    date2 = pd.to_datetime(df['date'], errors='coerce', format='%m/%d/%Y')
    df['date'] = date1.fillna(date2)
    df = df.dropna(subset=['date'])
    
    df = df[df['route_id'] != 'R999']

    holiday_map = {
        'False': False, 'No': False, '0': False, 'false': False,
        'True': True, 'Yes': True, '1': True, 'true':True
    }
    df['is_holiday'] = df['is_holiday'].map(holiday_map)

    df['direction'] = df['direction'].str.lower().str.strip()

    df['direction'] = df['direction'].replace({
        'in' : 'inbound',
        'inbnd' : 'inbound',
        'outbnd' : 'outbound',
        'out' : 'outbound' 
    })

    df.loc[df['trip_duration_min'] < 0, 'trip_duration_min'] = np.nan

    df['trip_duration_min'] = df['trip_duration_min'].fillna(
        df['trip_duration_min'].median
    )

    df['trip_duration_min'] = pd.to_numeric(df['trip_duration_min'], errors='coerce')


    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['boarding_count'].sum().sort_index()


# summary 
def create_summary(df):
    df['boarding_count'] = pd.to_numeric(df['boarding_count'], errors='coerce').fillna(0)
    
    summary = {}
    summary['total_trips'] = len(df)
    summary['date_range'] = f"{df['date'].min().date()} to {df['date'].max().date()}"
    route_sum = df.groupby('route_id')['boarding_count'].sum()
    summary['busiest_route'] = route_sum.idxmax()
    daily = df.groupby('date')['boarding_count'].sum()
    summary['avg_daily_ridership'] = round(daily.mean(), 1)
    summary['ridership_by_vehicle_type'] = df.groupby('vehicle_type')['boarding_count'].sum().to_dict()
    summary['ridership_by_weather'] = df.groupby('weather')['boarding_count'].sum().to_dict()
    top_routes = route_sum.sort_values(ascending=False).head(5)
    summary['top_5_routes_by_boarding'] = [
        {"route": route, "total_boardings": int(value)}
        for route, value in top_routes.items()
    ]

    return summary



# visualizations
def save_outputs(df_clean, summary, monthly, top_routes):
    os.makedirs("output", exist_ok=True)

    with open("output/summary.json", "w") as f:
        json.dump(summary, f, indent=4)
    

    # 3.1: Monthly Ridership (Line Chart)
    plt.figure()
    monthly.plot(marker='o', color='tab:blue')
    plt.title("Monthly Ridership (Total Boardings)")
    plt.xlabel("Month")
    plt.ylabel("Total Boardings")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("output/monthly_ridership.png")
    plt.close()

    # 4.2: Top Routes (Horizontal Bar)
    plt.figure()
    top_routes.plot(kind='barh', color='tab:orange')
    plt.title("Top Routes by Boardings")
    plt.xlabel("Total Boardings")
    plt.tight_layout()
    plt.savefig("output/top_routes.png")
    plt.close()

    # 5.3: Avg Duration (Bar Chart)
    plt.figure()
    avg_duration = df_clean.groupby('vehicle_type')['trip_duration_min'].mean()
    avg_duration.plot(kind='bar', color='tab:green')
    plt.title("Average Trip Duration by Vehicle Type")
    plt.ylabel("Minutes")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/avg_duration_vehicle.png")
    plt.close()

    # 6.4: Avg Boardings by Weather (Bar Chart)
    plt.figure()
    avg_boardings_weather = df_clean.groupby('weather')['boarding_count'].mean()
    avg_boardings_weather.plot(kind='bar', color='tab:red')
    plt.title("Average Boardings per Trip by Weather")
    plt.ylabel("Boardings")
    plt.xticks(rotation=0) 
    plt.tight_layout()
    plt.savefig("output/avg_boardings_weather.png")
    plt.close()
    
    print("📊 تم حفظ جميع الرسوم البيانية في مجلد output.")




def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        print("⏳ جاري تحميل البيانات...")
        df = load_data(DATA_PATH)
        
        print("Data cleaning and outlier handling are underway...")
        df_clean = clean_data(df)

        print("Final statistics are being calculated...")
        summary = create_summary(df_clean)
        
        create_summary(summary, OUTPUT_DIR)
        
        print("The graphs are being drawn...")
        save_outputs(df_clean, OUTPUT_DIR)

        print("The process was completed successfully! Summary of results:")
        print(json.dumps(summary, indent=2))
        print(f"\n All outputs were saved in a folder: {OUTPUT_DIR}")

    except Exception as e:
        print(f"An error occurred while running the Pipeline: {e}")

if __name__ == "__main__":
    main()

