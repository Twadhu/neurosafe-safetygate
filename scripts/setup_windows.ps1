$ErrorActionPreference = "Stop"

Write-Host "Creating the NeuroSafe Python environment..."
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e ".[dev,dashboard]"

Write-Host "Running automated tests..."
& .\.venv\Scripts\pytest.exe -q

Write-Host "Running the first reproducible experiment..."
& .\.venv\Scripts\neurosafe.exe simulate --trials 1000 --seed 42
& .\.venv\Scripts\neurosafe.exe sweep --trials 1000 --seed 42
& .\.venv\Scripts\neurosafe.exe robot-demo

Write-Host "Setup complete. Start the dashboard with:"
Write-Host ".\.venv\Scripts\streamlit.exe run app\dashboard.py"

