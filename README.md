# NeuroSafe SafetyGate

NeuroSafe SafetyGate is a confidence-aware safety layer for AI-controlled assistive robots.
It sits between a command predictor and the robot, then returns one of three decisions:
`EXECUTE`, `RESTRICT`, or `SAFE_STOP`.

This repository is the first working stage of Abdullah Abbas's longer NeuroSafe research
plan. The current goal is a reproducible simulation and public-EEG research prototype. The
future goal is safe and adaptive shared control for assistive robots.

## What works in version 1.0

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
- PhysioNet left/right motor-imagery evaluation with participant-disjoint folds.
- Real EEG prediction replay through a ROS 2 SafetyGate node.
- Gazebo Harmonic differential-drive robot, lidar, obstacles, and ROS bridge.
- Validation-participant threshold selection without test-participant tuning.
- Direct comparison of log-variance logistic regression and CSP-LDA.
- Fail-closed lidar handling and a stale-prediction watchdog.
- Shared control combining EEG steering with autonomous safe forward motion.
- Real EEG metrics and participant tables in the dashboard.

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

## Reproducible synthetic version 0.2 baseline

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

## Real PhysioNet EEG baseline

Version 0.3 downloads public PhysioNet EEG Motor Movement/Imagery runs 4, 8, and 12. These are
the correct imagined left-versus-right fist runs. It evaluates a 7-30 Hz log-variance plus
logistic-regression baseline with leave-one-participant-out folds. CSP, scaling, or classifier
parameters are never fitted on a held-out participant.

```bash
pip install -e ".[eeg]"
neurosafe evaluate-eeg --subjects 1-10
neurosafe benchmark-eeg --subjects 1-10
```

The executed 10-participant baseline contains 450 real EEG trials. Mean balanced accuracy is
52.55% with a 7.65 percentage-point standard deviation across held-out participants. In version
1.0, each outer test participant has a separate validation participant for threshold selection.
The selected thresholds accept or restrict 6.89% of test commands and stop 93.11%. Selective
accuracy remains only 48.39%, showing that confidence itself does not transfer reliably between
participants. This is an important negative result and a direct target for the next research model.

The comparison baseline produced 52.55% mean balanced accuracy for log-variance logistic
regression and 51.88% for CSP plus shrinkage LDA on identical participant folds.

## ROS 2 and Gazebo

The ROS package in `ros2_ws/src/neurosafe_ros` replays real held-out predictions, re-evaluates
them through SafetyGate using live lidar context, and publishes safe `geometry_msgs/Twist`
commands. See [docs/ros2_gazebo.md](docs/ros2_gazebo.md) for Ubuntu 24.04, ROS 2 Jazzy, and
Gazebo Harmonic instructions.

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

The committed real-EEG result is a 10-participant pilot, not a final estimate across all 109
participants. The Gazebo integration is an open-loop replay: PhysioNet EEG was recorded in a
different task context and is not synchronized to the simulated world. It validates the software
and safety-control path, not a closed-loop BCI or medical device.

