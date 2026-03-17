# Stretch 2 — Reverse-Engineered Transit Data Pipeline

This project builds a complete data pipeline to clean and analyze a messy public transit ridership dataset and reproduce expected outputs.

## Objective
Given:
- A messy dataset (`data/transit_ridership.csv`)
- Expected outputs (`expected_output/`)

The goal is to:
- Clean and standardize the data
- Generate accurate summary statistics
- Produce visualizations that match expected results

---


---

## Pipeline Steps

### 1. Load Data
- Read CSV using pandas

### 2. Clean Data
- Remove duplicates
- Standardize text fields (route_id, direction, vehicle_type, weather)
- Fix inconsistent categories and typos
- Parse mixed date formats
- Convert numeric columns safely

### 3. Handle Missing Values
- Fill:
  - `alighting_count`
  - `trip_duration_min`
  - `temperature_c`
- Fill `boarding_count` using:
  - median per `route_id`
  - fallback to global median

### 4. Filter Invalid Data
- Keep only valid routes
- Remove negative values
- Ensure valid categories

### 5. Generate Summary
- Total trips
- Date range
- Busiest route
- Average daily ridership
- Ridership by vehicle type
- Ridership by weather
- Top 5 routes

### 6. Create Visualizations
- Monthly ridership trend
- Ridership by route
- Vehicle utilization
- Weather impact

---

## How to Run

Activate virtual environment:

```bash
source .venv/Scripts/activate
```

Run pipeline:
```bash
python pipeline.py
```

Optional:
1. explore_data.py
Helps you:
    understand messy data and find bugs faster

2. compare_outputs.py
Helps you:
    check differences between your summary and expected summary
```bash
python explore_data.py
python compare_outputs.py
```

## Output
    Results are saved in:
    output/
    summary.json
    4 visualization charts (PNG)