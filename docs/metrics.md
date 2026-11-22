# Metrics and interpretation

## Safety metrics

| Metric | Meaning | Direction |
|---|---|---|
| Direct unsafe rate | Fraction of predictions that would be wrong or violate the obstacle constraint if executed directly | Lower |
| Gated unsafe rate | Fraction still executed or restricted after SafetyGate despite being unsafe | Lower |
| Unsafe reduction | Relative decrease from direct unsafe cases | Higher |
| Weighted risk | Wrong commands receive weight 1 and obstacle hazards receive additional weight 2; restricted motion scales severity by speed | Lower |

## Utility metrics

| Metric | Meaning | Direction |
|---|---|---|
| Coverage | Fraction of commands not rejected with SAFE_STOP | Context-dependent |
| Selective accuracy | Prediction accuracy among commands not rejected | Higher |
| False rejection rate | Correct predictions rejected by SAFE_STOP | Lower |

## Calibration metrics

| Metric | Meaning | Direction |
|---|---|---|
| Expected calibration error | Difference between confidence and observed correctness across confidence bins | Lower |
| Multiclass Brier score | Mean squared probability error across classes | Lower |

No single metric is sufficient. A threshold can improve safety by rejecting nearly every command,
which would make the robot unusable. Report risk and coverage together and select thresholds on a
validation set, never on the final test set.

