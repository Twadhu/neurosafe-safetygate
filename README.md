# NeuroSafe SafetyGate

NeuroSafe SafetyGate is a confidence-aware safety layer for AI-controlled assistive robots.
It sits between a command predictor and the robot, then returns one of three decisions:
`EXECUTE`, `RESTRICT`, or `SAFE_STOP`.

This repository is the first working stage of Abdullah Abbas's longer NeuroSafe research
plan. The current goal is a reproducible simulation and public-EEG research prototype. The
future goal is safe and adaptive shared control for assistive robots.

## What works in version 0.1

- Configurable SafetyGate decision engine.
- Checks for confidence, uncertainty, obstacles, stale messages, invalid probabilities,
  communication failure, and emergency stop.
- Reproducible synthetic experiment comparing direct control with SafetyGate.
- CSV experiment logs and quantitative summary metrics.
- Automated unit tests.
- Optional Streamlit monitoring dashboard.
- Optional PhysioNet motor-imagery EEG baseline using CSP + LDA.

## Quick start

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

### Linux or macOS

```bash
python -m venv .venv
source .venv/bin/activate     # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
neurosafe simulate
pytest -q
```

The simulation writes trial-level results to `artifacts/simulation_trials.csv`.

## Dashboard

```bash
pip install -e ".[dashboard]"
streamlit run app/dashboard.py
```

## Public EEG baseline

The first EEG experiment downloads public PhysioNet EEG Motor Movement/Imagery data. It uses
imagined left and right fist runs and trains a subject-specific CSP + LDA baseline.

```bash
pip install -e ".[eeg]"
neurosafe train-eeg --subject 1
```

The first run downloads data. Do not claim cross-subject generalization from this baseline.

## Repository map

```text
app/                    Monitoring dashboard
config/                 Safety thresholds
docs/                   Architecture, protocol, and roadmap
src/neurosafe/          Core package, EEG baseline, and experiments
tests/                  Automated safety and reproducibility tests
artifacts/              Generated models, CSV logs, and figures
```

## Research integrity

This software is an educational research prototype. It is not a medical device and must not
be used to control equipment around people without independent safety engineering, formal
risk assessment, institutional approval, and supervised testing.

