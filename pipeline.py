import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json

DATA_PATH = 'data/transit_ridership.csv'
OUTPUT_DIR = 'output'


def load_data(filepath):
    df=pd.read_csv(filepath)
    print(f"Loaded {len(df)} records from {filepath}")
    return df 

def clean_data(df):
   df_clean = df.copy()
   df_clean = df_clean.drop_duplicates()
   df_clean = df_clean[df_clean['route_id'] != 'R999'] 
   df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
   df_clean.loc[(df_clean['trip_duration_min'] > 200) | (df_clean['trip_duration_min'] <= 0), 'trip_duration_min'] = None
   boarding_median = df_clean['boarding_count'].median()
   df_clean['boarding_count'] = df_clean['boarding_count'].fillna(boarding_median)
   alighting_median = df_clean['alighting_count'].median()
   df_clean['alighting_count'] = df_clean['alighting_count'].fillna(alighting_median)
   trip_duration_median = df_clean['trip_duration_min'].median()
   df_clean['trip_duration_min'] = df_clean['trip_duration_min'].fillna(trip_duration_median)
   temperature_median = df_clean['temperature_c'].median()
   df_clean['temperature_c'] = df_clean['temperature_c'].fillna(temperature_median)
    
   df_clean['vehicle_type'] = df_clean['vehicle_type'].str.strip().str.title()
   mapping = {
        'Mini Bus': 'Minibus', 
        'Std Bus': 'Standard Bus', 
        'Standardbus': 'Standard Bus',
        'Articulated': 'Articulated Bus', 
        'Articulatedbus': 'Articulated Bus'
    }
   df_clean['vehicle_type'] = df_clean['vehicle_type'].replace(mapping)
   
   df_clean = df_clean.dropna(subset=['route_id'])
  

   
   
   df_clean = df_clean.drop_duplicates()
   return df_clean


def add_features(df):
   df_eniched =df.copy()
   df_eniched['date'] = pd.to_datetime(df_eniched['date'],errors='coerce')
   df_eniched['month'] = df_eniched['date'].dt.to_period('M')
   df_eniched['day_name'] = df_eniched['date'].dt.day_name()
   df_eniched['is_weekend'] = df_eniched['date'].dt.dayofweek.isin([5, 6])
   df_eniched['total_ridership'] = df_eniched['boarding_count'] + df_eniched['alighting_count']

   return df_eniched


def generate_summary(df):
    if df.empty:
        return {'total_boardings': 0, 'avg_trip_duration': 0, 'top_route': "N/A", 'record_count': 0}
    total_boardings = df['boarding_count'].sum()
    
    
    avg_duration = df['trip_duration_min'].mean()
    
    
    top_route = df.groupby('route_id')['boarding_count'].sum().idxmax()
    count = len(df)
    return {
        'total_boardings': total_boardings,
        'avg_trip_duration': avg_duration,
        'top_route': top_route,
        'record_count': count
    }



def create_visualizations(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
  #chart 1
    monthly_data = df.groupby(df['date'].dt.to_period('M'))['boarding_count'].sum()
    plt.figure(figsize=(10, 5))
    plt.plot(monthly_data.index.astype(str), monthly_data.values, marker='o', color='#1f6df1', linewidth=2)
    plt.title('Monthly Ridership (Total Boardings)')
    plt.xticks(rotation=45)
    plt.savefig(f'{output_dir}/monthly_ridership.png', bbox_inches='tight')
    plt.close()

    #chart 2
    route_data = df.groupby('route_id')['boarding_count'].sum().sort_values(ascending=False)
    plt.figure(figsize=(10, 8))
    sns.barplot(x=route_data.values, y=route_data.index, color='#009661') 
    plt.title('Total Boardings by Route')
    plt.savefig(f'{output_dir}/boardings_by_route.png', bbox_inches='tight')
    plt.close()

    #chart 3
    
    vt_data = df.groupby('vehicle_type')['trip_duration_min'].mean()
    plt.figure(figsize=(8, 5))
    colors = ['#e32424', '#2463e3', '#24bd4d']
    plt.bar(vt_data.index, vt_data.values, color=colors)
    plt.title('Average Trip Duration by Vehicle Type')
    plt.ylabel('Average Trip Duration (min)')
    plt.savefig(f'{output_dir}/duration_by_vehicle.png')
    plt.close()

    print(f"✅ All visualizations successfully saved to: {output_dir}")
    


def main ():

    df =load_data(DATA_PATH)
    print(f"Loaded {len(df)} records.")
    df_cleaned = clean_data(df)
    print(f" Cleaning complete. Size: {len(df_cleaned)}")
    df_final = add_features(df_cleaned)
    print(" Features added.")
    summary = generate_summary(df_final)
    print("\n--- Summary Statistics ---")
    print(summary)
    print("--------------------------\n")
    create_visualizations(df_final,OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True) # تأكدي إن المجلد موجود
    with open(f'{OUTPUT_DIR}/summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
    print(f"✅ Summary saved to {OUTPUT_DIR}/summary.json")

if __name__ == "__main__":
   
   main()