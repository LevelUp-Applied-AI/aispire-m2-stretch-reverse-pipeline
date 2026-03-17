import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import json
from pipeline import load_data, clean_data, add_features, generate_summary


INPUT_FILE = 'data/transit_ridership.csv'
OUTPUT_DIR = 'output'

# ─── Test 1: Load ────────────────────────────────────────────────────────────

def test_load_data_returns_dataframe():
    """load_data should return a DataFrame with expected columns and rows."""
    
    result = load_data(INPUT_FILE)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    
    expected_columns = [
        'date', 'route_id', 'vehicle_type', 'boarding_count', 
        'alighting_count', 'trip_duration_min', 'is_holiday'
    ]
    
    for col in expected_columns:
        assert col in result.columns

# ─── Test 2: Clean ───────────────────────────────────────────────────────────

def test_clean_data_logic():
    """clean_data should remove duplicates and normalize categorical values."""
    raw_df = pd.read_csv(INPUT_FILE)
    cleaned_df = clean_data(raw_df)
    
    # 1. Check for duplicate removal
    assert len(cleaned_df) <= len(raw_df)
    
    # 2. Check Direction normalization
    allowed_directions = ['Inbound', 'Outbound']
    for val in cleaned_df['direction'].unique():
        assert val in allowed_directions
        
    # 3. Check Holiday boolean conversion
    assert cleaned_df['is_holiday'].dtype == 'bool'

# ─── Test 3: Add Features ────────────────────────────────────────────────────

def test_add_features_creation():
    """add_features should add total_ridership and month columns."""
    df = load_data(INPUT_FILE)
    df = clean_data(df)
    result = add_features(df)
    
    assert 'total_ridership' in result.columns
    assert 'month' in result.columns
    
    # Verify math: total = boarding + alighting
    first_row = result.iloc[0]
    expected_total = first_row['boarding_count'] + first_row['alighting_count']
    assert first_row['total_ridership'] == expected_total

# ─── Test 4: Summarize ───────────────────────────────────────────────────────

def test_generate_summary_writes_file():
    """generate_summary should export a JSON file with correct transit stats."""
    df = load_data(INPUT_FILE)
    df = clean_data(df)
    df = add_features(df)
    
    generate_summary(df, OUTPUT_DIR)
    
    json_path = os.path.join(OUTPUT_DIR, 'summary.json')
    assert os.path.exists(json_path)
    
    with open(json_path, 'r') as f:
        summary = json.load(f)
        
    assert "total_trips" in summary
    assert "busiest_route" in summary
    assert isinstance(summary['top_5_routes_by_boarding'], list)

# ─── Test 5: Validation (Visualizations) ─────────────────────────────────────

def test_visualizations_exist():
    """Validation: create_visualizations should generate four specific PNG files."""
    # This acts as the final validation step of the pipeline output
    expected_files = [
        'avg_boarding_weather.png',
        'avg_duration_vehicle.png',
        'total_boarding_route.png',
        'monthly_ridership.png'
    ]
    
    for file_name in expected_files:
        file_path = os.path.join(OUTPUT_DIR, file_name)
        # Check if they were created by the most recent pipeline run
        assert os.path.exists(file_path), f"Missing visualization: {file_name}"