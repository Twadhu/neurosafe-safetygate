# Model card: synthetic generator and real EEG baseline

## Synthetic command generator

The committed version 0.2 results use a seeded synthetic generator. It produces three movement
classes and deliberately assigns different confidence ranges to correct and incorrect predictions.
Its purpose is to test SafetyGate behaviour, metrics, logging, and threshold trade-offs.

It does not represent a measured EEG distribution and must not be used to estimate clinical or
real-world performance.

## EEG baseline

The executed EEG pilot uses public PhysioNet EEG Motor Movement/Imagery recordings from subjects
1 through 10. Runs 4, 8, and 12 encode imagined left versus right fist. Each epoch is filtered
to 7-30 Hz and converted to channel-wise log-variance features. A standardized logistic regression
model is fitted on nine participants and tested exclusively on the tenth, repeated for every
participant.

The pilot contains 450 trials. Mean held-out balanced accuracy is 52.55%, ECE is 5.03%, and the
default SafetyGate coverage is 12.89%. These results do not support autonomous control claims.

## Intended use

- Education and research-method development.
- Reproducible comparison of direct command execution and selective rejection.
- Participant-disjoint EEG benchmarking and safe robot-simulation plumbing.

## Out-of-scope use

- Diagnosis, treatment, rehabilitation decisions, or medical claims.
- Unsupervised control of a physical assistive robot.
- Claims of cross-subject generalization from a subject-specific result.

## Known limitations

- The real-EEG pilot covers only 10 of the database's 109 participants.
- The lightweight robot simulator omits dynamics, sensor noise, localization, and actuator delay.
- Confidence thresholds require validation on representative data.
- Offline public EEG results do not establish real-time BCI performance.
- Prerecorded EEG is not contextually synchronized with the Gazebo environment.

