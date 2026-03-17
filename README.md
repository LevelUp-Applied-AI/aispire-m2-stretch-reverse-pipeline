# Stretch 2: Reverse-Engineer the Pipeline

## Overview

This project is a reverse-engineered data pipeline built to clean and analyze a messy public transit dataset.

The dataset contains multiple issues such as:
- Inconsistent date formats
- Typos in categories
- Missing values
- Duplicates
- Invalid and extreme values

The goal was to transform the raw data into a clean dataset and reproduce the expected outputs.

---

## What the Pipeline Does

The pipeline:

1. Loads the raw CSV dataset
2. Cleans and standardizes:
   - Dates
   - Route IDs
   - Direction values
   - Vehicle types
   - Weather categories
3. Handles missing values using median/mode
4. Removes duplicates and invalid records
5. Generates:
   - Summary statistics (`summary.json`)
   - 4 analytical charts

---

## Results

The pipeline successfully produces clean outputs and meaningful analysis.

The results are **very close to the expected output**, with only minor differences due to interpretation of certain cleaning rules (e.g. handling edge cases and extreme values).

---

## How to Run

```bash
pip install -r requirements.txt
python pipeline.py