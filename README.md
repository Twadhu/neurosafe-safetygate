# NeuroSafe SafetyGate

NeuroSafe SafetyGate is a confidence-aware safety layer for AI-controlled assistive robots.
It sits between a command predictor and the robot, then returns one of three decisions:
`EXECUTE`, `RESTRICT`, or `SAFE_STOP`.

This repository is the first working stage of Abdullah Abbas's longer NeuroSafe research
plan. The current goal is a reproducible simulation and public-EEG research prototype. The
future goal is safe and adaptive shared control for assistive robots.

## What works in version 0.2

- Configurable SafetyGate decision engine.
- Checks for confidence, uncertainty, obstacles, stale messages, invalid probabilities,
  communication failure, and emergency stop.
- Reproducible synthetic experiment comparing direct control with SafetyGate.
- Risk-coverage threshold sweeps evaluated on identical scenarios.
- ECE, Brier score, selective accuracy, coverage, false rejection, and weighted risk.
- Deterministic 2D differential-drive robot simulation with collision handling.
- CSV trial logs, CSV threshold studies, and JSON summaries.
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
neurosafe simulate --trials 2000 --seed 42
neurosafe sweep --trials 2000 --seed 42
neurosafe robot-demo
pytest -q
```

The simulation writes trial-level results to `artifacts/simulation_trials.csv`.

## Reproducible version 0.2 baseline

Using 2,000 seeded synthetic scenarios with the default thresholds:

| Metric | Result |
|---|---:|
| Prediction accuracy | 72.2% |
| Direct unsafe rate | 31.6% |
| SafetyGate unsafe rate | 15.25% |
| Relative unsafe reduction | 51.74% |
| Coverage | 83.65% |
| Selective accuracy | 81.77% |
| False rejection rate | 5.26% |

These numbers validate software behaviour under a declared synthetic generator. They are not EEG,
clinical, hardware, or real-world safety results.

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
docs/                   Architecture, metrics, protocol, and roadmap
reports/                Versioned, reproducible baseline summaries
src/neurosafe/          Core package, EEG baseline, and experiments
tests/                  Automated safety and reproducibility tests
artifacts/              Generated models, CSV logs, and figures
```

## Research integrity

This software is an educational research prototype. It is not a medical device and must not
be used to control equipment around people without independent safety engineering, formal
risk assessment, institutional approval, and supervised testing.

## Current scientific boundary

The committed EEG module is ready to download public PhysioNet data and run a calibrated,
subject-specific CSP + LDA baseline. It has not yet produced a committed EEG result. Cross-subject
generalization and Gazebo integration remain future milestones.

