"""NeuroSafe SafetyGate research prototype."""

from .models import Command, Decision, Prediction, RobotContext, SafetyResult
from .robot_simulator import CircleObstacle, DifferentialDriveSimulator, RobotState
from .safety_gate import SafetyGate, SafetyGateConfig

__all__ = [
    "CircleObstacle",
    "Command",
    "Decision",
    "DifferentialDriveSimulator",
    "Prediction",
    "RobotContext",
    "RobotState",
    "SafetyGate",
    "SafetyGateConfig",
    "SafetyResult",
]

__version__ = "1.0.0"
