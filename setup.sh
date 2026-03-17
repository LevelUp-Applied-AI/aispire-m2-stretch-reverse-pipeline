#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python test_environment.py
echo "Setup complete."