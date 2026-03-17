import pandas as pd

DATA_PATH = "data/transit_ridership.csv"


def main():
    df = pd.read_csv(DATA_PATH)

    print("=== SHAPE ===")
    print(df.shape)
    print()

    print("=== COLUMNS ===")
    print(df.columns.tolist())
    print()

    print("=== HEAD ===")
    print(df.head(10))
    print()

    print("=== DTYPES ===")
    print(df.dtypes)
    print()

    print("=== MISSING VALUES ===")
    print(df.isna().sum())
    print()

    print("=== DUPLICATES ===")
    print(df.duplicated().sum())
    print()

    for col in ["route_id", "direction", "vehicle_type", "weather", "is_holiday"]:
        print(f"=== UNIQUE VALUES: {col} ===")
        print(sorted(df[col].astype(str).str.strip().unique()))
        print()

    print("=== SAMPLE BAD / MIXED DATES ===")
    print(df["date"].head(20).tolist())


if __name__ == "__main__":
    main()