"""
Lab 2 — Data Pipeline: Retail Sales Analysis
Module 2 — Programming for AI & Data Science

Complete each function below. Remove the TODO: comments and pass statements
as you implement each function. Do not change the function signatures.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json



# ─── Configuration ────────────────────────────────────────────────────────────

DATA_PATH = 'data/transit_ridership.csv'
OUTPUT_DIR = 'expected_output/'


# ─── Pipeline Functions ───────────────────────────────────────────────────────

def load_data(filepath):
  
 data=pd.read_csv(filepath)
 print(f"loaded: {len(data)}  records from: {filepath}")
 return data




def clean_data(df):
 
    df=df.copy()
    df['direction'] = df['direction'].str.capitalize()
    df['is_holiday'] = df['is_holiday'].astype(str).str.lower()
    df['is_holiday'] = df['is_holiday'].replace({
    'false': False,
    '0': False,
    'no': False,
    'true': True,
    '1': True,
    'yes': True
       })

    df['is_holiday'] = df['is_holiday'].astype(bool)

    df['boarding_count'].fillna(df['boarding_count'].median(), inplace=True)
    df['trip_duration_min'].fillna(df['trip_duration_min'].median(), inplace=True)
    df = df.drop_duplicates()
    
    # Parse 'date' to datetime using pd.to_datetime with errors='coerce'
    df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
    
    # Handle NaT values explicitly (drop rows with invalid dates)
    df = df.dropna(subset=['date'])
    
    # Drop rows where BOTH boarding_count , lighting_count and is_holiday  are still missing after fill
    df = df.dropna(subset=['direction','boarding_count','trip_duration_min','is_holiday'], how='all')
    
    # Print: "Cleaned data: N records"
    print(f"Cleaned data: {len(df)} records")
    
    # Return the cleaned DataFrame
    return df



    


def generate_summary(df):
  summary = {
    "rows": len(df),
    "columns": len(df.columns),
    "missing_values": df.isna().sum().to_dict()
    }
  with open("expected_output/summary.json", "w") as f:
     json.dump(summary, f, indent=4)
      


def create_visualizations(df,output_dir=OUTPUT_DIR):
            
 """Create and save 4 charts as PNG files """
 os.makedirs(output_dir, exist_ok=True)

 df.groupby("route_id")["boarding_count"].sum().plot(kind="bar")
 plt.title("Boarding by Route")
 plt.savefig("expected_output/chart1.png")
 plt.clf()

 # vehicle_type
 df.groupby("vehicle_type")["trip_duration_min"].mean().plot(kind="bar")
 plt.title("Avg Trip Duration")
 plt.savefig("expected_output/chart2.png")
 plt.clf()


 df["weather"].value_counts().plot(kind="pie", autopct="%1.1f%%")
 plt.title("Weather Distribution")
 plt.savefig("expected_output/chart3.png")
 plt.clf()


 plt.scatter(df["temperature_c"], df["boarding_count"])
 plt.xlabel("Temperature")
 plt.ylabel("Boarding Count")
 plt.title("Temperature vs Boarding")
 plt.savefig("expected_output/chart4.png")
 plt.clf()


def main():
    """Run the full data pipeline end-to-end."""
   
    df = load_data(DATA_PATH)
    cleaned_data = clean_data(df)
    summary = generate_summary(cleaned_data)
      

    create_visualizations(df)
    print("Pipeline complete.")
    


if __name__ == "__main__":
    main()
   