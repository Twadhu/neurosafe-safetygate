from __future__ import annotations

import csv
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time

from .metrics import expected_calibration_error, multiclass_brier_score
from .models import Command, Decision, Prediction, RobotContext
from .safety_gate import SafetyGate, SafetyGateConfig, normalized_entropy

MOVEMENT_COMMANDS = (Command.LEFT, Command.RIGHT, Command.FORWARD)


@dataclass(frozen=True)
class Scenario:
    scenario_id: int
    true_command: Command
    prediction: Prediction
    obstacle_distance_m: float | None


@dataclass(frozen=True)
class TrialRecord:
    trial: int
    true_command: str
    predicted_command: str
    confidence: float
    entropy: float
    probabilities: str
    obstacle_distance_m: float | None
    prediction_correct: bool
    direct_unsafe: bool
    direct_risk: float
    gate_decision: str
    gate_output: str
    speed_scale: float
    gate_unsafe: bool
    gated_risk: float
    reasons: str


def _sample_prediction(rng: random.Random, true_command: Command) -> Prediction:
    correct = rng.random() < 0.72
    predicted = (
        true_command
        if correct
        else rng.choice([item for item in MOVEMENT_COMMANDS if item != true_command])
    )
    confidence = rng.uniform(0.72, 0.98) if correct else rng.uniform(0.42, 0.88)
    remaining = 1.0 - confidence
    other = [item for item in MOVEMENT_COMMANDS if item != predicted]
    probabilities = {
        predicted: confidence,
        other[0]: remaining * 0.55,
        other[1]: remaining * 0.45,
    }
    return Prediction(command=predicted, probabilities=probabilities, created_at=time())


def generate_scenarios(trials: int = 500, seed: int = 42) -> list[Scenario]:
    if trials < 1:
        raise ValueError("trials must be at least 1")
    rng = random.Random(seed)
    scenarios: list[Scenario] = []
    for index in range(1, trials + 1):
        true_command = rng.choice(MOVEMENT_COMMANDS)
        prediction = _sample_prediction(rng, true_command)
        obstacle = rng.uniform(0.10, 1.50) if rng.random() < 0.30 else None
        scenarios.append(Scenario(index, true_command, prediction, obstacle))
    return scenarios


def evaluate_scenarios(gate: SafetyGate, scenarios: list[Scenario]) -> list[TrialRecord]:
    records: list[TrialRecord] = []
    for scenario in scenarios:
        context = RobotContext(
            obstacle_distance_m=scenario.obstacle_distance_m,
            now=scenario.prediction.created_at,
        )
        result = gate.evaluate(scenario.prediction, context)
        obstacle_hazard = (
            scenario.obstacle_distance_m is not None
            and scenario.obstacle_distance_m < gate.config.minimum_obstacle_distance_m
        )
        incorrect = scenario.prediction.command != scenario.true_command
        direct_unsafe = incorrect or obstacle_hazard
        gate_unsafe = result.decision != Decision.SAFE_STOP and direct_unsafe
        direct_risk = float(incorrect) + 2.0 * float(obstacle_hazard)
        gated_risk = direct_risk * result.speed_scale if gate_unsafe else 0.0
        probabilities = {
            command.value: round(value, 8)
            for command, value in scenario.prediction.probabilities.items()
        }
        records.append(
            TrialRecord(
                trial=scenario.scenario_id,
                true_command=scenario.true_command.value,
                predicted_command=scenario.prediction.command.value,
                confidence=round(scenario.prediction.confidence, 8),
                entropy=round(normalized_entropy(scenario.prediction.probabilities), 8),
                probabilities=json.dumps(probabilities, sort_keys=True),
                obstacle_distance_m=(
                    None
                    if scenario.obstacle_distance_m is None
                    else round(scenario.obstacle_distance_m, 8)
                ),
                prediction_correct=not incorrect,
                direct_unsafe=direct_unsafe,
                direct_risk=direct_risk,
                gate_decision=result.decision.value,
                gate_output=result.output_command.value,
                speed_scale=result.speed_scale,
                gate_unsafe=gate_unsafe,
                gated_risk=gated_risk,
                reasons=";".join(result.reasons),
            )
        )
    return records


def summarize_records(records: list[TrialRecord]) -> dict[str, float]:
    if not records:
        raise ValueError("records cannot be empty")
    trials = len(records)
    direct_unsafe = sum(record.direct_unsafe for record in records)
    gated_unsafe = sum(record.gate_unsafe for record in records)
    stopped = sum(record.gate_decision == Decision.SAFE_STOP.value for record in records)
    restricted = sum(record.gate_decision == Decision.RESTRICT.value for record in records)
    accepted = [record for record in records if record.gate_decision != Decision.SAFE_STOP.value]
    correct = sum(record.prediction_correct for record in records)
    false_rejections = sum(
        record.prediction_correct and record.gate_decision == Decision.SAFE_STOP.value
        for record in records
    )
    probabilities = [json.loads(record.probabilities) for record in records]
    classes = [command.value for command in MOVEMENT_COMMANDS]
    calibration_error = expected_calibration_error(
        [record.confidence for record in records],
        [record.prediction_correct for record in records],
    )
    return {
        "trials": float(trials),
        "prediction_accuracy": correct / trials,
        "direct_unsafe_rate": direct_unsafe / trials,
        "gated_unsafe_rate": gated_unsafe / trials,
        "unsafe_reduction_rate": (
            0.0 if direct_unsafe == 0 else (direct_unsafe - gated_unsafe) / direct_unsafe
        ),
        "coverage": len(accepted) / trials,
        "selective_accuracy": (
            0.0
            if not accepted
            else sum(record.prediction_correct for record in accepted) / len(accepted)
        ),
        "false_rejection_rate": 0.0 if correct == 0 else false_rejections / correct,
        "safe_stop_rate": stopped / trials,
        "restrict_rate": restricted / trials,
        "expected_calibration_error": calibration_error,
        "multiclass_brier_score": multiclass_brier_score(
            probabilities, [record.true_command for record in records], classes
        ),
        "direct_weighted_risk": sum(record.direct_risk for record in records),
        "gated_weighted_risk": sum(record.gated_risk for record in records),
    }


def run_experiment(
    gate: SafetyGate,
    trials: int = 500,
    seed: int = 42,
    output_csv: str | Path | None = None,
    summary_json: str | Path | None = None,
) -> tuple[list[TrialRecord], dict[str, float]]:
    scenarios = generate_scenarios(trials, seed)
    records = evaluate_scenarios(gate, scenarios)
    metrics = summarize_records(records)
    if output_csv:
        _write_csv(output_csv, records)
    if summary_json:
        path = Path(summary_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"data_source": "synthetic", "seed": seed, **metrics}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return records, metrics


def run_threshold_sweep(
    trials: int = 1000,
    seed: int = 42,
    output_csv: str | Path | None = None,
) -> list[dict[str, float]]:
    scenarios = generate_scenarios(trials, seed)
    rows: list[dict[str, float]] = []
    for execute_threshold in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
        restrict_threshold = round(max(0.40, execute_threshold - 0.20), 2)
        gate = SafetyGate(
            SafetyGateConfig(
                execute_threshold=execute_threshold,
                restrict_threshold=restrict_threshold,
            )
        )
        metrics = summarize_records(evaluate_scenarios(gate, scenarios))
        rows.append(
            {
                "execute_threshold": execute_threshold,
                "restrict_threshold": restrict_threshold,
                **metrics,
            }
        )
    if output_csv:
        _write_dict_csv(output_csv, rows)
    return rows


def _write_csv(path_value: str | Path, records: list[TrialRecord]) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=asdict(records[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def _write_dict_csv(path_value: str | Path, rows: list[dict[str, float]]) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
