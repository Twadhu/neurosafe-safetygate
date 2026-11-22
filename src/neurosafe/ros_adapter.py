from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .models import Command


@dataclass(frozen=True)
class VelocityCommand:
    linear_x: float
    angular_z: float


def command_to_velocity(
    command: Command,
    speed_scale: float,
    normal_speed_mps: float = 0.5,
    turning_speed_radps: float = 1.2,
) -> VelocityCommand:
    """Map a SafetyGate output to a differential-drive velocity command."""
    bounded_scale = min(1.0, max(0.0, float(speed_scale)))
    if command == Command.STOP:
        return VelocityCommand(0.0, 0.0)
    if command == Command.FORWARD:
        return VelocityCommand(normal_speed_mps * bounded_scale, 0.0)
    if command == Command.LEFT:
        return VelocityCommand(0.0, turning_speed_radps * bounded_scale)
    if command == Command.RIGHT:
        return VelocityCommand(0.0, -turning_speed_radps * bounded_scale)
    raise ValueError(f"Unsupported command: {command}")


def load_replay_rows(
    path: str | Path,
    held_out_subject: int | None = None,
) -> list[dict[str, str]]:
    """Load real-EEG cross-subject predictions for deterministic ROS replay."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if held_out_subject is not None:
        rows = [row for row in rows if int(row["held_out_subject"]) == held_out_subject]
    if not rows:
        raise ValueError("No EEG prediction rows matched the replay request")
    return rows
