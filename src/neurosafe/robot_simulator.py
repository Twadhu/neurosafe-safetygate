from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from math import cos, pi, sin, sqrt
from pathlib import Path

from .models import Command


@dataclass(frozen=True)
class CircleObstacle:
    x: float
    y: float
    radius: float


@dataclass
class RobotState:
    x: float = 0.0
    y: float = 0.0
    heading_rad: float = 0.0
    collisions: int = 0
    distance_m: float = 0.0


@dataclass(frozen=True)
class RobotStep:
    step: int
    command: str
    speed_scale: float
    x: float
    y: float
    heading_rad: float
    collision: bool


class DifferentialDriveSimulator:
    """Deterministic 2D simulator for SafetyGate integration tests."""

    def __init__(
        self,
        obstacles: list[CircleObstacle] | None = None,
        robot_radius_m: float = 0.16,
        linear_speed_mps: float = 0.50,
        angular_speed_rad_s: float = pi / 2,
    ) -> None:
        self.obstacles = obstacles or []
        self.robot_radius_m = robot_radius_m
        self.linear_speed_mps = linear_speed_mps
        self.angular_speed_rad_s = angular_speed_rad_s
        self.state = RobotState()

    def reset(self, state: RobotState | None = None) -> RobotState:
        self.state = state or RobotState()
        return self.state

    def step(self, command: Command, speed_scale: float = 1.0, dt_s: float = 0.25) -> bool:
        if not 0 <= speed_scale <= 1:
            raise ValueError("speed_scale must be between 0 and 1")
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        if command == Command.STOP:
            return False
        if command == Command.LEFT:
            self.state.heading_rad += self.angular_speed_rad_s * speed_scale * dt_s
            return False
        if command == Command.RIGHT:
            self.state.heading_rad -= self.angular_speed_rad_s * speed_scale * dt_s
            return False

        distance = self.linear_speed_mps * speed_scale * dt_s
        next_x = self.state.x + cos(self.state.heading_rad) * distance
        next_y = self.state.y + sin(self.state.heading_rad) * distance
        collision = self._collides(next_x, next_y)
        if collision:
            self.state.collisions += 1
            return True
        self.state.x = next_x
        self.state.y = next_y
        self.state.distance_m += distance
        return False

    def nearest_obstacle_distance(self) -> float | None:
        if not self.obstacles:
            return None
        return min(
            max(
                0.0,
                sqrt((item.x - self.state.x) ** 2 + (item.y - self.state.y) ** 2)
                - item.radius
                - self.robot_radius_m,
            )
            for item in self.obstacles
        )

    def _collides(self, x: float, y: float) -> bool:
        return any(
            sqrt((item.x - x) ** 2 + (item.y - y) ** 2) <= item.radius + self.robot_radius_m
            for item in self.obstacles
        )


def run_robot_demo(output_csv: str | Path | None = None) -> list[RobotStep]:
    simulator = DifferentialDriveSimulator(
        obstacles=[CircleObstacle(1.25, 0.0, 0.20), CircleObstacle(0.65, 0.90, 0.20)]
    )
    commands = [
        Command.FORWARD,
        Command.FORWARD,
        Command.LEFT,
        Command.FORWARD,
        Command.FORWARD,
        Command.RIGHT,
        Command.FORWARD,
        Command.STOP,
    ]
    records: list[RobotStep] = []
    for index, command in enumerate(commands, start=1):
        collision = simulator.step(command, speed_scale=1.0, dt_s=0.5)
        records.append(
            RobotStep(
                step=index,
                command=command.value,
                speed_scale=1.0,
                x=round(simulator.state.x, 6),
                y=round(simulator.state.y, 6),
                heading_rad=round(simulator.state.heading_rad, 6),
                collision=collision,
            )
        )
    if output_csv:
        path = Path(output_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=asdict(records[0]).keys())
            writer.writeheader()
            writer.writerows(asdict(record) for record in records)
    return records
