# Build roadmap

## Milestone 1: Core SafetyGate

- Status: implemented and expanded in version 0.2.
- Deterministic three-state decision logic.
- Hard checks for obstacles, timeout, invalid probabilities, communication, and emergency stop.
- Automated tests and synthetic comparison experiment.
- Calibration, selective prediction, risk-coverage, and threshold-sweep metrics.
- Lightweight 2D differential-drive command simulator.

## Milestone 2: Public EEG baseline

- Status: 10-participant pilot implemented in version 0.3.
- Downloaded correct left/right imagery runs 4, 8, and 12.
- Evaluated 450 trials with leave-one-participant-out isolation.
- Archived participant-level and aggregate results.
- Next: scale to all valid participants and compare stronger transfer-learning baselines.

## Milestone 3: Robot simulation

- Status: integration code implemented in version 0.3.
- Added EEG prediction, safety status, emergency-stop, lidar, and velocity topics.
- Connected SafetyGate to a differential-drive Gazebo robot.
- Added lidar obstacle overrides and a reproducible real-prediction replay node.
- Next: execute acceptance tests on an Ubuntu 24.04 ROS 2 Jazzy workstation.

## Version 1.0 software-completion status

- Implemented two participant-disjoint EEG baselines on identical folds.
- Implemented validation-only confidence-threshold selection.
- Implemented shared control, lidar fail-closed behavior, and a prediction watchdog.
- Implemented a real-EEG dashboard and machine-readable reports.
- Published explicit acceptance criteria and reproducibility configuration.

Version 1.0 is the completed research-software prototype. It is not the end of the scientific
project. The next meaningful research upgrade is a stronger representation-learning or domain-
generalization model evaluated on a larger participant cohort, followed by live closed-loop EEG.

## Milestone 4: Research evaluation

- Compare direct execution with SafetyGate under identical trials.
- Tune thresholds on validation data only.
- Add cross-session and cross-subject evaluation.
- Produce figures, ablation tables, report, poster, and demonstration video.

## Milestone 5: Optional physical prototype

- Start only after simulation acceptance tests pass.
- Use a local microcontroller emergency stop and obstacle stop independent of the AI model.
- Document wiring, power limits, failure modes, and reset procedure.

