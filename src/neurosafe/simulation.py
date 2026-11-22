from __future__ import annotations

import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time

from .models import Command, Decision, Prediction, RobotContext
from .safety_gate import SafetyGate


@dataclass
class TrialRecord:
    trial: int
    true_command: str
    predicted_command: str
    confidence: float
    obstacle_distance_m: float | None
    prediction_correct: bool
    direct_unsafe: bool
    gate_decision: str
    gate_output: str
    gate_unsafe: bool
    reasons: str


def _sample_prediction(rng: random.Random, true_command: Command) -> Prediction:
    commands = [Command.LEFT, Command.RIGHT, Command.FORWARD]
    correct = rng.random() < 0.72
    predicted = true_command if correct else rng.choice([c for c in commands if c != true_command])
    confidence = rng.uniform(0.72, 0.98) if correct else rng.uniform(0.42, 0.88)
    remaining = 1.0 - confidence
    other = [c for c in commands if c != predicted]
    probabilities = {predicted: confidence, other[0]: remaining * 0.55, other[1]: remaining * 0.45}
    return Prediction(command=predicted, probabilities=probabilities, created_at=time())


def run_experiment(
    gate: SafetyGate,
    trials: int = 500,
    seed: int = 42,
    output_csv: str | Path | None = None,
) -> tuple[list[TrialRecord], dict[str, float]]:
    rng = random.Random(seed)
    movement_commands = [Command.LEFT, Command.RIGHT, Command.FORWARD]
    records: list[TrialRecord] = []

    for index in range(1, trials + 1):
        true_command = rng.choice(movement_commands)
        prediction = _sample_prediction(rng, true_command)
        obstacle = rng.uniform(0.10, 1.50) if rng.random() < 0.30 else None
        context = RobotContext(obstacle_distance_m=obstacle, now=time())
        result = gate.evaluate(prediction, context)
        obstacle_hazard = (
            obstacle is not None and obstacle < gate.config.minimum_obstacle_distance_m
        )
        incorrect = prediction.command != true_command
        direct_unsafe = incorrect or obstacle_hazard
        gate_unsafe = result.decision != Decision.SAFE_STOP and direct_unsafe
        records.append(
            TrialRecord(
                trial=index,
                true_command=true_command.value,
                predicted_command=prediction.command.value,
                confidence=round(prediction.confidence, 6),
                obstacle_distance_m=None if obstacle is None else round(obstacle, 6),
                prediction_correct=not incorrect,
                direct_unsafe=direct_unsafe,
                gate_decision=result.decision.value,
                gate_output=result.output_command.value,
                gate_unsafe=gate_unsafe,
                reasons=";".join(result.reasons),
            )
        )

    if output_csv:
        path = Path(output_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=asdict(records[0]).keys())
            writer.writeheader()
            writer.writerows(asdict(record) for record in records)

    direct_unsafe_count = sum(record.direct_unsafe for record in records)
    gated_unsafe_count = sum(record.gate_unsafe for record in records)
    stopped = sum(record.gate_decision == Decision.SAFE_STOP.value for record in records)
    restricted = sum(record.gate_decision == Decision.RESTRICT.value for record in records)
    metrics = {
        "trials": float(trials),
        "direct_unsafe_rate": direct_unsafe_count / trials,
        "gated_unsafe_rate": gated_unsafe_count / trials,
        "unsafe_reduction_rate": (
            0.0
            if direct_unsafe_count == 0
            else (direct_unsafe_count - gated_unsafe_count) / direct_unsafe_count
        ),
        "safe_stop_rate": stopped / trials,
        "restrict_rate": restricted / trials,
    }
    return records, metrics
