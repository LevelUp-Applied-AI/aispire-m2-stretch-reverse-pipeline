import pandas as pd
import json

# 1️ load data 
df = pd.read_csv("data/transit_ridership.csv")

# 2️ clean data 
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date'])
df = df.drop_duplicates()

df['route_id'] = df['route_id'].str.strip()
df['vehicle_type'] = df['vehicle_type'].str.title().str.strip()
df['weather'] = df['weather'].str.title().str.strip()

df['boarding_count'] = pd.to_numeric(df['boarding_count'], errors='coerce')
df['alighting_count'] = pd.to_numeric(df['alighting_count'], errors='coerce')
df['trip_duration_min'] = pd.to_numeric(df['trip_duration_min'], errors='coerce')
df['temperature_c'] = pd.to_numeric(df['temperature_c'], errors='coerce')

df['is_holiday'] = df['is_holiday'].map({
    'Yes': True, 'No': False, 'True': True, 'False': False
})

# 3️ remove rows with missing values in important colums and invalid trip durations
df = df.dropna(subset=['boarding_count', 'alighting_count', 'trip_duration_min'])
df = df[df['trip_duration_min'] > 0]

# 4️ create summary directory
summary_dict = {}

#  Total trips
summary_dict['total_trips'] = len(df)

# Date range
summary_dict['date_range'] = f"{df['date'].min().date()} to {df['date'].max().date()}"

# Busiest route
route_boardings = df.groupby('route_id')['boarding_count'].sum()
summary_dict['busiest_route'] = route_boardings.idxmax()

# Average daily ridership
daily_boardings = df.groupby('date')['boarding_count'].sum()
summary_dict['avg_daily_ridership'] = round(daily_boardings.mean(), 1)

# Ridership by vehicle type
vehicle_boardings = df.groupby('vehicle_type')['boarding_count'].sum().to_dict()
summary_dict['ridership_by_vehicle_type'] = {k: int(v) for k, v in vehicle_boardings.items()}

# Ridership by weather
weather_boardings = df.groupby('weather')['boarding_count'].sum().to_dict()
summary_dict['ridership_by_weather'] = {k: int(v) for k, v in weather_boardings.items()}

# Top 5 routes by boarding
top_5_routes = route_boardings.sort_values(ascending=False).head(5)
summary_dict['top_5_routes_by_boarding'] = [
    {"route": idx, "total_boardings": int(val)} for idx, val in top_5_routes.items()
]

# 5️ summary in JSON
with open("summary_generated.json", "w") as f:
    json.dump(summary_dict, f, indent=2)

print(" summary_generated.json created successfully!")