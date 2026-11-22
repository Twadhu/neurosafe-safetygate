from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdSelection:
    threshold: float
    validation_loss: float
    coverage: float
    selective_accuracy: float


def select_confidence_threshold(
    confidences: Sequence[float],
    correctness: Sequence[bool],
    candidates: Iterable[float] | None = None,
    wrong_accept_cost: float = 4.0,
    correct_reject_cost: float = 1.0,
) -> ThresholdSelection:
    """Select a rejection threshold using validation data only.

    Wrong accepted commands are penalized more strongly than correctly rejected
    commands. Ties prefer the lower threshold, preserving more useful commands.
    """
    if len(confidences) != len(correctness) or not confidences:
        raise ValueError("Confidences and correctness must be non-empty and aligned")
    if wrong_accept_cost <= 0 or correct_reject_cost < 0:
        raise ValueError("Costs must be non-negative and wrong_accept_cost must be positive")
    grid = tuple(candidates or (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90))
    if not grid or any(not 0.5 <= value <= 1.0 for value in grid):
        raise ValueError("Threshold candidates must be between 0.5 and 1.0")

    best: ThresholdSelection | None = None
    for threshold in sorted({float(value) for value in grid}):
        accepted = [confidence >= threshold for confidence in confidences]
        wrong_accepted = sum(a and not c for a, c in zip(accepted, correctness, strict=True))
        correct_rejected = sum(not a and c for a, c in zip(accepted, correctness, strict=True))
        loss = (wrong_accept_cost * wrong_accepted + correct_reject_cost * correct_rejected) / len(
            correctness
        )
        accepted_correctness = [
            correct for accept, correct in zip(accepted, correctness, strict=True) if accept
        ]
        candidate = ThresholdSelection(
            threshold=threshold,
            validation_loss=loss,
            coverage=sum(accepted) / len(accepted),
            selective_accuracy=(
                sum(accepted_correctness) / len(accepted_correctness)
                if accepted_correctness
                else 0.0
            ),
        )
        if best is None or (candidate.validation_loss, candidate.threshold) < (
            best.validation_loss,
            best.threshold,
        ):
            best = candidate
    assert best is not None
    return best
