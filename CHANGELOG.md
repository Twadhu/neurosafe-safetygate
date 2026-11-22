# Changelog

## 1.0.0

- Added nested participant isolation for confidence-threshold selection.
- Added a reproducible comparison of log-variance logistic regression and CSP-LDA.
- Added a real-EEG results view to the Streamlit dashboard.
- Added shared control that blends EEG steering with lidar-gated forward motion.
- Added a fail-closed lidar rule and prediction-stream watchdog to the ROS node.
- Added an auditable experiment manifest and formal acceptance-test document.
- Expanded the automated suite to 36 tests while retaining the coverage gate.
- Promoted the project to a complete research-software prototype.

## 0.3.0

- Corrected left/right motor-imagery runs from 6, 10, 14 to 4, 8, 12.
- Downloaded and evaluated 450 real PhysioNet trials from 10 participants.
- Added leave-one-participant-out evaluation with explicit identity isolation.
- Added participant-level accuracy, calibration, coverage, and safe-stop reports.
- Added real-EEG prediction replay for ROS 2.
- Added a live lidar-aware SafetyGate ROS node publishing safe velocity commands.
- Added a Gazebo Harmonic differential-drive world with lidar and obstacles.
- Added ROS-independent command mapping tests and expanded the suite to 27 tests.

## 0.2.0

- Added reproducible scenario generation separated from evaluation.
- Added risk-coverage threshold sweeps on identical scenarios.
- Added expected calibration error and multiclass Brier score.
- Added coverage, selective accuracy, false-rejection, and weighted-risk metrics.
- Added a deterministic differential-drive robot simulator with collision handling.
- Added calibrated CSP + LDA EEG evaluation fields.
- Expanded the dashboard into safety, threshold, robot, and audit views.
- Expanded automated tests and added a coverage quality gate.
- Added machine-readable CSV and JSON research outputs.

## 0.1.0

- Added the three-state SafetyGate decision engine.
- Added synthetic direct-control versus SafetyGate comparison.
- Added a subject-specific PhysioNet CSP + LDA baseline.
- Added the first Streamlit dashboard and automated tests.

