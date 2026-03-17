import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
df = pd.read_csv("data/transit_ridership.csv")
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
    'Yes': True,
    'No': False,
    'True': True,
    'False': False
})
# Delete rows with missing values ​​in important columns

df = df.dropna(subset=['boarding_count', 'alighting_count', 'trip_duration_min'])

# remove rows with invalid trip durations

df = df[df['trip_duration_min'] > 0]

# Display the first 5 rows
print(df.head())

# Information about columns and number of empty values
print(df.info())

# Number of empty values ​​in each column
print(df.isna().sum())

print(len(df))

print(df[df['boarding_count'] < 0])
print(df[df['trip_duration_min'] <= 0])

# Boardings per vehicle type
vehicle_boardings = df.groupby('vehicle_type')['boarding_count'].sum()
vehicle_boardings.plot(kind='bar')
plt.ylabel('Total Boardings')
plt.title('Boardings by Vehicle Type')
plt.savefig('vehicle_type_boardings.png')
plt.close()

# Boardings per weather
weather_boardings = df.groupby('weather')['boarding_count'].sum()
weather_boardings.plot(kind='bar')
plt.ylabel('Total Boardings')
plt.title('Boardings by Weather')
plt.savefig('weather_boardings.png')
plt.close()

# Top 5 busiest routes
top_routes = df.groupby('route_id')['boarding_count'].sum().sort_values(ascending=False).head(5)
top_routes.plot(kind='bar')
plt.ylabel('Total Boardings')
plt.title('Top 5 Routes by Boarding')
plt.savefig('top5_routes_boardings.png')
plt.close()

# Daily ridership trend
daily_boardings = df.groupby('date')['boarding_count'].sum()
daily_boardings.plot(kind='line')
plt.ylabel('Total Boardings')
plt.title('Daily Ridership Trend')
plt.savefig('daily_ridership.png')
plt.close()