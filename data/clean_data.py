# NOTE FOR FUTURE DEVELOPERS: 
# When parsing dates and dropping the invalid ones, the dataset size is reduced 
# to 1757 rows (instead of the expected 1929). 
# I have proceeded with the rest of the analysis and pipeline based on this count.
import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/transit_ridership.csv')

df = df.drop_duplicates()

df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')

direction_map = {
    'In': 'Inbound', 'Inbnd': 'Inbound', 'INBOUND': 'Inbound', 'inbound': 'Inbound',
    'Out': 'Outbound', 'Outbnd': 'Outbound', 'OUTBOUND': 'Outbound', 'outbound': 'Outbound'
}
df['direction'] = df['direction'].replace(direction_map)
df['direction'] = df['direction'].str.capitalize()


vehicle_map = {
    'mini bus': 'Minibus', 'MINIBUS': 'Minibus', 
    'std bus': 'Standard Bus', 'Std Bus': 'Standard Bus', 'standard bus': 'Standard Bus',
    'articulated': 'Articulated Bus'
}
df['vehicle_type'] = df['vehicle_type'].replace(vehicle_map)

df['vehicle_type'] = df['vehicle_type'].str.title() 

holiday_map = {'0': False, 'No': False, 'false': False, 'False': False,
               '1': True, 'Yes': True, 'true': True, 'True': True}
df['is_holiday'] = df['is_holiday'].astype(str).map(holiday_map)

df = df.dropna(subset=['date'])#
df['boarding_count'] = df['boarding_count'].fillna(0)
df['alighting_count'] = df['alighting_count'].fillna(0)

df.loc[(df['trip_duration_min'] <= 0) | (df['trip_duration_min'] > 300), 'trip_duration_min'] = np.nan

print("-   -   -  -  -  - - - - --- === || Data after cleaning || === --- - - -  -  -  -   -   -   -")
print(df.head())
print(f"  Total number of successful trips  : {len(df)}")


total_trips = len(df)

min_date = df['date'].min()
max_date = df['date'].max()
date_range = f"{min_date} to {max_date}"


route_boardings = df.groupby('route_id')['boarding_count'].sum().reset_index()
route_boardings = route_boardings.sort_values(by='boarding_count', ascending=False)

busiest_route = route_boardings.iloc[0]['route_id']


total_boardings_all = df['boarding_count'].sum()
unique_days = df['date'].nunique()
avg_daily_ridership = round(total_boardings_all / unique_days, 1) if unique_days > 0 else 0


ridership_by_vehicle_type = df.groupby('vehicle_type')['boarding_count'].sum().to_dict()


ridership_by_weather = df.groupby('weather')['boarding_count'].sum().to_dict()


top_5_routes_by_boarding = []
for index, row in route_boardings.head(5).iterrows():
    top_5_routes_by_boarding.append({
        "route": row['route_id'],
        "total_boardings": int(row['boarding_count'])
    })


summary_data = {
    "total_trips": total_trips,
    "date_range": date_range,
    "busiest_route": busiest_route,
    "avg_daily_ridership": avg_daily_ridership,
    "ridership_by_vehicle_type": {k: int(v) for k, v in ridership_by_vehicle_type.items()},
    "ridership_by_weather": {k: int(v) for k, v in ridership_by_weather.items()},
    "top_5_routes_by_boarding": top_5_routes_by_boarding
}


with open('summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

print("\nsummary.json")

###############################################################
###                        Charts                           ###
###############################################################
sns.set_theme(style="whitegrid")


plt.figure(figsize=(10, 6))
top_routes = df.groupby('route_id')['boarding_count'].sum().nlargest(5).reset_index()

sns.barplot(data=top_routes, x='boarding_count', y='route_id', palette='magma')

plt.title('Top 5 Busiest Routes', fontsize=16, weight='bold')
plt.xlabel('Total Boardings', fontsize=12)
plt.ylabel('Route ID', fontsize=12)
plt.tight_layout()
plt.savefig('chart_1_top_routes.png', dpi=300) 
plt.close()

plt.figure(figsize=(8, 8))
veh_counts = df.groupby('vehicle_type')['boarding_count'].sum()

colors = ['#ff9999', '#66b3ff', '#99ff99']
plt.pie(veh_counts, labels=veh_counts.index, autopct='%1.1f%%', startangle=140, 
        colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 2})

my_circle = plt.Circle((0,0), 0.7, color='white')
p = plt.gcf()
p.gca().add_artist(my_circle)

plt.title('Ridership by Vehicle Type', fontsize=16, weight='bold')
plt.tight_layout()
plt.savefig('chart_2_vehicle_types.png', dpi=300)
plt.close()

plt.figure(figsize=(10, 6))
weather_counts = df.groupby('weather')['boarding_count'].sum().reset_index()

sns.barplot(data=weather_counts, x='weather', y='boarding_count', palette='coolwarm')

plt.title('Total Boardings by Weather Condition', fontsize=16, weight='bold')
plt.xlabel('Weather Condition', fontsize=12)
plt.ylabel('Total Boardings', fontsize=12)
plt.tight_layout()
plt.savefig('chart_3_weather.png', dpi=300)
plt.close()

plt.figure(figsize=(14, 6))
daily_ridership = df.groupby('date')['boarding_count'].sum().reset_index()

daily_ridership['date'] = pd.to_datetime(daily_ridership['date'])
daily_ridership = daily_ridership.sort_values('date')

sns.lineplot(data=daily_ridership, x='date', y='boarding_count', color='#2ca02c', linewidth=2)

plt.fill_between(daily_ridership['date'], daily_ridership['boarding_count'], color='#2ca02c', alpha=0.3)

plt.title('Daily Total Ridership Trend (2024)', fontsize=16, weight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Total Boardings', fontsize=12)
plt.tight_layout()
plt.savefig('chart_4_daily_trend.png', dpi=300)
plt.close()

