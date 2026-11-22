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


def shared_control_velocity(
    command: Command,
    speed_scale: float,
    obstacle_distance_m: float | None,
    normal_speed_mps: float = 0.5,
    turning_speed_radps: float = 1.2,
    minimum_obstacle_distance_m: float = 0.35,
) -> VelocityCommand:
    """Blend EEG steering with cautious autonomous forward motion.

    LEFT and RIGHT express steering intent. Forward motion is supplied by the
    shared controller only while lidar reports sufficient clearance.
    """
    if obstacle_distance_m is None or obstacle_distance_m < minimum_obstacle_distance_m:
        return VelocityCommand(0.0, 0.0)
    if command == Command.STOP:
        return VelocityCommand(0.0, 0.0)
    bounded_scale = min(1.0, max(0.0, float(speed_scale)))
    forward = normal_speed_mps * 0.45 * bounded_scale
    if command == Command.LEFT:
        return VelocityCommand(forward, turning_speed_radps * bounded_scale)
    if command == Command.RIGHT:
        return VelocityCommand(forward, -turning_speed_radps * bounded_scale)
    return VelocityCommand(normal_speed_mps * bounded_scale, 0.0)


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
