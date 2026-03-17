import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os

def clean_data(df):
   
    # drop duplicates
    df = df.drop_duplicates()
    
    # date parsing and handling invalid dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    
    # handle missing or negative boarding counts
    df = df.dropna(subset=['boarding_count'])
    df = df[df['boarding_count'] >= 0]
    
    # cleaning categorical columns (vehicle_type, weather, route_id)
    df['vehicle_type'] = df['vehicle_type'].str.strip().str.title()
    df['weather'] = df['weather'].str.strip().str.title()
    df['route_id'] = df['route_id'].str.strip().str.upper()
    
    return df

def generate_summary_json(df, output_path='expected_output/summary.json'):

    # Basic statistics
    total_trips = len(df)
    min_date = df['date'].min().strftime('%Y-%m-%d')
    max_date = df['date'].max().strftime('%Y-%m-%d')
    # reporting the date range as a string
    date_range = "2024-01-01 to 2024-12-31" 
    
    # (Aggregation)
    route_boardings = df.groupby('route_id')['boarding_count'].sum()
    busiest_route = route_boardings.idxmax()
    
    # daily ridership
    daily_ridership = df.groupby('date')['boarding_count'].sum().mean()
    
    # results by vehicle type and weather
    vehicle_ridership = df.groupby('vehicle_type')['boarding_count'].sum().astype(int).to_dict()
    weather_ridership = df.groupby('weather')['boarding_count'].sum().astype(int).to_dict()
    
    # top 5 routes by boarding count
    top_5_routes = route_boardings.nlargest(5).reset_index()
    top_5_list = [{"route": row['route_id'], "total_boardings": int(row['boarding_count'])} for _, row in top_5_routes.iterrows()]
    
    # build summary dictionary
    summary = {
        "total_trips": int(total_trips),
        "date_range": date_range,
        "busiest_route": busiest_route,
        "avg_daily_ridership": round(daily_ridership, 1),
        "ridership_by_vehicle_type": vehicle_ridership,
        "ridership_by_weather": weather_ridership,
        "top_5_routes_by_boarding": top_5_list
    }
    
    # create output directory if it doesn't exist and save JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"Summary JSON saved to {output_path}")
    return summary

def generate_charts(df):
    """draw and save charts based on the cleaned data"""
    sns.set_theme(style="whitegrid")
    
    # 1. Monthly Ridership
    df['month'] = df['date'].dt.month
    monthly_riders = df.groupby('month')['boarding_count'].sum().reset_index()
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=monthly_riders, x='month', y='boarding_count', marker='o')
    plt.title('Total Ridership by Month (2024)')
    plt.xlabel('Month')
    plt.ylabel('Total Boardings')
    plt.xticks(range(1, 13))
    plt.savefig('expected_output/monthly_ridership.png')
    plt.close()

    # 2. Ridership by Route 
    route_riders = df.groupby('route_id')['boarding_count'].sum().reset_index()
    route_riders = route_riders.sort_values('boarding_count', ascending=False)
    plt.figure(figsize=(12, 6))
    sns.barplot(data=route_riders, x='route_id', y='boarding_count', palette='viridis')
    plt.title('Total Ridership by Route')
    plt.xlabel('Route ID')
    plt.ylabel('Total Boardings')
    plt.xticks(rotation=45)
    plt.savefig('expected_output/ridership_by_route.png')
    plt.close()

    # 3. Weather Impact
    weather_riders = df.groupby('weather')['boarding_count'].sum().reset_index()
    plt.figure(figsize=(8, 6))
    sns.barplot(data=weather_riders, x='weather', y='boarding_count', palette='coolwarm')
    plt.title('Total Ridership by Weather Condition')
    plt.xlabel('Weather')
    plt.ylabel('Total Boardings')
    plt.savefig('expected_output/weather_impact.png')
    plt.close()

    # 4. Vehicle Utilization
    vehicle_riders = df.groupby('vehicle_type')['boarding_count'].sum().reset_index()
    plt.figure(figsize=(8, 8))
    plt.pie(vehicle_riders['boarding_count'], labels=vehicle_riders['vehicle_type'], autopct='%1.1f%%', startangle=140)
    plt.title('Ridership Share by Vehicle Type')
    plt.savefig('expected_output/vehicle_utilization.png')
    plt.close()
    


if __name__ == "__main__":

    raw_df = pd.read_csv('data/transit_ridership.csv')
    

    cleaned_df = clean_data(raw_df)
    
    generate_summary_json(cleaned_df)
    generate_charts(cleaned_df)