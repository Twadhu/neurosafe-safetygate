from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from time import time


class Command(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FORWARD = "FORWARD"
    STOP = "STOP"


class Decision(str, Enum):
    EXECUTE = "EXECUTE"
    RESTRICT = "RESTRICT"
    SAFE_STOP = "SAFE_STOP"


@dataclass(frozen=True)
class Prediction:
    command: Command
    probabilities: dict[Command, float]
    created_at: float = field(default_factory=time)

    @property
    def confidence(self) -> float:
        return float(self.probabilities.get(self.command, 0.0))

    @property
    def valid(self) -> bool:
        if not self.probabilities:
            return False
        values = list(self.probabilities.values())
        if any(not isfinite(value) or value < 0 or value > 1 for value in values):
            return False
        return abs(sum(values) - 1.0) <= 1e-6 and self.command in self.probabilities


@dataclass(frozen=True)
class RobotContext:
    obstacle_distance_m: float | None = None
    emergency_stop: bool = False
    communication_ok: bool = True
    now: float = field(default_factory=time)


@dataclass(frozen=True)
class SafetyResult:
    requested_command: Command
    output_command: Command
    decision: Decision
    confidence: float
    entropy: float
    speed_scale: float
    reasons: tuple[str, ...]

    @property
    def stopped(self) -> bool:
        return self.output_command == Command.STOP
