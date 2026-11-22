#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev,dashboard]'
.venv/bin/pytest -q
.venv/bin/neurosafe simulate --trials 1000 --seed 42

echo "Setup complete. Start the dashboard with:"
echo ".venv/bin/streamlit run app/dashboard.py"

