import sys


def check_environment():
    try:
        import pandas
        import matplotlib
        import pytest
        import numpy
        import seaborn
        print(f"pandas: {pandas.__version__}")
        print(f"matplotlib: {matplotlib.__version__}")
        print(f"pytest: {pytest.__version__}")
        print(f"numpy: {numpy.__version__}")
        print(f"seaborn: {seaborn.__version__}")
        print("Environment OK")
    except ImportError as e:
        print(f"ImportError: {e}", file=sys.stderr)
        print(
            "\nYour environment is missing a required package.",
            file=sys.stderr,
        )
        print(
            "Confirm your venv is active ((.venv) prefix in prompt), then run:",
            file=sys.stderr,
        )
        print("    pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_environment()
