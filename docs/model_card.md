# Model card: synthetic command generator and EEG baseline

## Synthetic command generator

The committed version 0.2 results use a seeded synthetic generator. It produces three movement
classes and deliberately assigns different confidence ranges to correct and incorrect predictions.
Its purpose is to test SafetyGate behaviour, metrics, logging, and threshold trade-offs.

It does not represent a measured EEG distribution and must not be used to estimate clinical or
real-world performance.

## EEG baseline

The optional EEG module is designed for public PhysioNet EEG Motor Movement/Imagery recordings.
It uses runs 6, 10, and 14 for imagined left versus right fist, 7-30 Hz filtering, CSP features,
LDA classification, sigmoid calibration, and nested cross-validation.

## Intended use

- Education and research-method development.
- Reproducible comparison of direct command execution and selective rejection.
- Preparation for later subject-disjoint EEG evaluation and robot simulation.

## Out-of-scope use

- Diagnosis, treatment, rehabilitation decisions, or medical claims.
- Unsupervised control of a physical assistive robot.
- Claims of cross-subject generalization from a subject-specific result.

## Known limitations

- The current committed numerical baseline is synthetic.
- The lightweight robot simulator omits dynamics, sensor noise, localization, and actuator delay.
- Confidence thresholds require validation on representative data.
- Offline public EEG results do not establish real-time BCI performance.

