# Initial research protocol

## Research question

Can a confidence-aware SafetyGate reduce unsafe command execution compared with direct AI
command execution while preserving useful robot commands?

## Primary comparison

Run the same predictions and obstacle conditions under:

1. Direct execution without SafetyGate.
2. Execution with SafetyGate.

## Initial metrics

- Unsafe command acceptance rate.
- Correct command execution rate.
- Rejection and restriction rates.
- Response latency.
- Balanced accuracy for the EEG classifier.
- Expected calibration error and Brier score in the calibration milestone.
- Coverage, selective accuracy, and false-rejection rate.
- Weighted risk, reported together with unweighted unsafe-command rate.

## Reproducibility rules

- Record random seeds and configuration values.
- Never mix trials from the same recording into train and test through accidental leakage.
- Report subject-specific and cross-subject results separately.
- Save raw results before creating plots or summaries.
- Label synthetic, offline EEG, simulation, and physical-robot results distinctly.
- Evaluate threshold candidates on identical scenarios and seeds.
- Select thresholds using validation data and report final results on untouched test data.

## Version 0.3 participant-disjoint EEG protocol

- Dataset: PhysioNet EEG Motor Movement/Imagery Database v1.0.0.
- Task: imagined left versus right fist, runs 4, 8, and 12.
- Pilot cohort: participants 1 through 10, 45 trials per participant.
- Preprocessing: 7-30 Hz filtering and epochs from 1 to 4 seconds after task onset.
- Features: channel-wise log variance.
- Classifier: standardized logistic regression with balanced class weights.
- Outer evaluation: leave one participant out.
- Leakage rule: all learned transformations and classifier parameters are fitted only on the
  nine training participants in each fold.
- Safety analysis: feed held-out probabilities to the unchanged default SafetyGate.
- Gazebo analysis: replay authentic held-out probabilities while using live simulated lidar.

## Safety and ethics

The project is an educational prototype, not a medical device. It uses public data during
the first phase and does not collect new human EEG. Any future participant study requires
institutional approval and informed consent before data collection.

