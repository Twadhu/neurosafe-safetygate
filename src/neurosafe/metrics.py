from __future__ import annotations

from collections.abc import Iterable, Sequence


def expected_calibration_error(
    confidences: Sequence[float], correctness: Sequence[bool], bins: int = 10
) -> float:
    """Return equal-width expected calibration error."""
    if len(confidences) != len(correctness):
        raise ValueError("confidences and correctness must have equal length")
    if not confidences:
        return 0.0
    if bins < 1:
        raise ValueError("bins must be at least 1")
    if any(value < 0 or value > 1 for value in confidences):
        raise ValueError("confidence values must be between 0 and 1")

    total = len(confidences)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = [
            sample
            for sample, confidence in enumerate(confidences)
            if lower <= confidence < upper or (index == bins - 1 and confidence == 1.0)
        ]
        if not selected:
            continue
        mean_confidence = sum(confidences[sample] for sample in selected) / len(selected)
        mean_accuracy = sum(bool(correctness[sample]) for sample in selected) / len(selected)
        error += (len(selected) / total) * abs(mean_accuracy - mean_confidence)
    return error


def multiclass_brier_score(
    probabilities: Iterable[dict[str, float]], truths: Sequence[str], classes: Sequence[str]
) -> float:
    """Return mean multiclass Brier score, where lower is better."""
    probability_rows = list(probabilities)
    if len(probability_rows) != len(truths):
        raise ValueError("probabilities and truths must have equal length")
    if not probability_rows:
        return 0.0
    if not classes:
        raise ValueError("classes cannot be empty")

    total = 0.0
    for row, truth in zip(probability_rows, truths, strict=True):
        if truth not in classes:
            raise ValueError(f"Unknown truth label: {truth}")
        total += sum((row.get(label, 0.0) - float(label == truth)) ** 2 for label in classes)
    return total / len(probability_rows)


def percentile(values: Sequence[float], quantile: float) -> float:
    """Return a linearly interpolated percentile without an external dependency."""
    if not values:
        return 0.0
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
