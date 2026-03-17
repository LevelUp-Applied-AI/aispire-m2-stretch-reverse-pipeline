import json
import os

EXPECTED_PATH = "expected_output/summary.json"
ACTUAL_PATH = "output/summary.json"


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_dicts(expected, actual, prefix=""):
    all_keys = sorted(set(expected.keys()) | set(actual.keys()))

    for key in all_keys:
        current_key = f"{prefix}.{key}" if prefix else key

        if key not in expected:
            print(f"Extra key in actual: {current_key}")
            continue

        if key not in actual:
            print(f"Missing key in actual: {current_key}")
            continue

        if isinstance(expected[key], dict) and isinstance(actual[key], dict):
            compare_dicts(expected[key], actual[key], current_key)
        elif expected[key] != actual[key]:
            print(f"Mismatch at {current_key}")
            print(f"  expected: {expected[key]}")
            print(f"  actual:   {actual[key]}")


def main():
    if not os.path.exists(EXPECTED_PATH):
        print(f"Missing expected file: {EXPECTED_PATH}")
        return

    if not os.path.exists(ACTUAL_PATH):
        print(f"Missing actual file: {ACTUAL_PATH}")
        return

    expected = load_json(EXPECTED_PATH)
    actual = load_json(ACTUAL_PATH)

    print("=== COMPARING SUMMARY.JSON ===")
    compare_dicts(expected, actual)
    print("Done.")


if __name__ == "__main__":
    main()