from __future__ import annotations

import json
from dataclasses import dataclass
from math import log
from pathlib import Path

from .models import Command, Decision, Prediction, RobotContext, SafetyResult


@dataclass(frozen=True)
class SafetyGateConfig:
    execute_threshold: float = 0.80
    restrict_threshold: float = 0.60
    maximum_entropy: float = 0.95
    command_timeout_ms: int = 500
    minimum_obstacle_distance_m: float = 0.35
    restricted_speed_scale: float = 0.35
    normal_speed_mps: float = 0.50

    @classmethod
    def from_json(cls, path: str | Path) -> SafetyGateConfig:
        with Path(path).open(encoding="utf-8") as handle:
            return cls(**json.load(handle))

    def validate(self) -> None:
        if not 0 <= self.restrict_threshold <= self.execute_threshold <= 1:
            raise ValueError("Thresholds must satisfy 0 <= restrict <= execute <= 1")
        if not 0 <= self.maximum_entropy <= 1:
            raise ValueError("maximum_entropy must be between 0 and 1")
        if not 0 <= self.restricted_speed_scale <= 1:
            raise ValueError("restricted_speed_scale must be between 0 and 1")


def normalized_entropy(probabilities: dict[Command, float]) -> float:
    values = [value for value in probabilities.values() if value > 0]
    if len(probabilities) <= 1:
        return 0.0
    entropy = -sum(value * log(value) for value in values)
    return entropy / log(len(probabilities))


class SafetyGate:
    """Convert uncertain AI predictions into safe robot commands.

    Safety constraints always override model confidence. A STOP command is always
    executable because it moves the system toward a safer state.
    """

    def __init__(self, config: SafetyGateConfig | None = None) -> None:
        self.config = config or SafetyGateConfig()
        self.config.validate()

    def evaluate(self, prediction: Prediction, context: RobotContext) -> SafetyResult:
        entropy = normalized_entropy(prediction.probabilities) if prediction.valid else 1.0
        hard_stop_reasons: list[str] = []

        if context.emergency_stop:
            hard_stop_reasons.append("emergency_stop_active")
        if not context.communication_ok:
            hard_stop_reasons.append("communication_failure")
        if (context.now - prediction.created_at) * 1000 > self.config.command_timeout_ms:
            hard_stop_reasons.append("stale_command")
        if not prediction.valid:
            hard_stop_reasons.append("invalid_probabilities")
        if (
            prediction.command != Command.STOP
            and context.obstacle_distance_m is not None
            and context.obstacle_distance_m < self.config.minimum_obstacle_distance_m
        ):
            hard_stop_reasons.append("obstacle_too_close")

        if hard_stop_reasons:
            return self._result(
                prediction, Decision.SAFE_STOP, Command.STOP, 0.0, entropy, hard_stop_reasons
            )

        if prediction.command == Command.STOP:
            return self._result(
                prediction, Decision.EXECUTE, Command.STOP, 0.0, entropy, ["stop_is_safe"]
            )

        if entropy > self.config.maximum_entropy:
            return self._result(
                prediction,
                Decision.SAFE_STOP,
                Command.STOP,
                0.0,
                entropy,
                ["uncertainty_too_high"],
            )

        if prediction.confidence >= self.config.execute_threshold:
            return self._result(
                prediction,
                Decision.EXECUTE,
                prediction.command,
                1.0,
                entropy,
                ["confidence_accepted"],
            )

        if prediction.confidence >= self.config.restrict_threshold:
            return self._result(
                prediction,
                Decision.RESTRICT,
                prediction.command,
                self.config.restricted_speed_scale,
                entropy,
                ["moderate_confidence"],
            )

        return self._result(
            prediction,
            Decision.SAFE_STOP,
            Command.STOP,
            0.0,
            entropy,
            ["confidence_too_low"],
        )

    @staticmethod
    def _result(
        prediction: Prediction,
        decision: Decision,
        output: Command,
        speed_scale: float,
        entropy: float,
        reasons: list[str],
    ) -> SafetyResult:
        return SafetyResult(
            requested_command=prediction.command,
            output_command=output,
            decision=decision,
            confidence=prediction.confidence,
            entropy=entropy,
            speed_scale=speed_scale,
            reasons=tuple(reasons),
        )
