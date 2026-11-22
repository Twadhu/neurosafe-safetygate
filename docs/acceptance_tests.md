# Version 1.0 acceptance tests

## Automated software gates

- All unit tests pass.
- Core Python coverage remains at or above 85%.
- Ruff lint and formatting checks pass.
- ROS Python sources compile.
- `package.xml` and the Gazebo SDF world parse as valid XML.
- Participant train and test identities never overlap.

## Robot safety scenarios

| Scenario | Required response |
|---|---|
| No EEG message after startup | Publish zero velocity |
| EEG stream exceeds the timeout | Publish zero velocity |
| Missing lidar | Fail closed and publish zero velocity |
| Obstacle inside the configured distance | SafetyGate outputs `SAFE_STOP` |
| Emergency-stop topic is true | Immediate zero velocity |
| Malformed prediction JSON | Reject message and publish zero velocity |
| Low confidence | Stop |
| Moderate confidence with clear lidar | Restricted shared-control motion |
| High confidence with clear lidar | Normal shared-control motion |
| ROS node shutdown | Publish zero velocity before exit |

## Research acceptance criteria

- Publish participant-level results, not only an overall mean.
- Compare at least two declared baselines on identical folds.
- Select confidence thresholds on validation participants, never on the test participant.
- Preserve raw trial predictions for audit and robot replay.
- Label prerecorded EEG plus Gazebo as open-loop software validation.
- Do not claim medical, clinical, or physical-robot safety.

## Work remaining outside this repository

The Gazebo graphical acceptance run requires Ubuntu 24.04, ROS 2 Jazzy, and Gazebo Harmonic.
A closed-loop EEG experiment requires live hardware, synchronized task design, informed consent,
institutional ethics approval, and supervised risk controls.
