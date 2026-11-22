# Build roadmap

## Milestone 1: Core SafetyGate

- Status: implemented and expanded in version 0.2.
- Deterministic three-state decision logic.
- Hard checks for obstacles, timeout, invalid probabilities, communication, and emergency stop.
- Automated tests and synthetic comparison experiment.
- Calibration, selective prediction, risk-coverage, and threshold-sweep metrics.
- Lightweight 2D differential-drive command simulator.

## Milestone 2: Public EEG baseline

- Install EEG dependencies.
- Download PhysioNet EEG Motor Movement/Imagery runs 6, 10, and 14.
- Train and evaluate CSP + LDA for imagined left versus right fist.
- Run and archive the calibrated CSP + LDA baseline on public data.
- Add subject-disjoint evaluation after the single-subject baseline is verified.

## Milestone 3: Robot simulation

- Define ROS2 messages for prediction, safety state, and velocity command.
- Connect SafetyGate to a differential-drive robot in Gazebo.
- Create obstacle, stale-command, and communication-failure scenarios.

## Milestone 4: Research evaluation

- Compare direct execution with SafetyGate under identical trials.
- Tune thresholds on validation data only.
- Add cross-session and cross-subject evaluation.
- Produce figures, ablation tables, report, poster, and demonstration video.

## Milestone 5: Optional physical prototype

- Start only after simulation acceptance tests pass.
- Use a local microcontroller emergency stop and obstacle stop independent of the AI model.
- Document wiring, power limits, failure modes, and reset procedure.

