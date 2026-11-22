from time import time

import pytest

from neurosafe.models import Command, Decision, Prediction, RobotContext
from neurosafe.safety_gate import SafetyGate, SafetyGateConfig


def prediction(command=Command.LEFT, confidence=0.90, created_at=None):
    remainder = 1.0 - confidence
    return Prediction(
        command=command,
        probabilities={command: confidence, Command.RIGHT: remainder},
        created_at=time() if created_at is None else created_at,
    )


def test_high_confidence_command_executes():
    result = SafetyGate().evaluate(prediction(), RobotContext())
    assert result.decision == Decision.EXECUTE
    assert result.output_command == Command.LEFT


def test_moderate_confidence_is_restricted():
    result = SafetyGate().evaluate(prediction(confidence=0.70), RobotContext())
    assert result.decision == Decision.RESTRICT
    assert result.speed_scale == pytest.approx(0.35)


def test_low_confidence_stops():
    result = SafetyGate().evaluate(prediction(confidence=0.55), RobotContext())
    assert result.decision == Decision.SAFE_STOP
    assert result.output_command == Command.STOP


def test_obstacle_overrides_high_confidence():
    context = RobotContext(obstacle_distance_m=0.20)
    result = SafetyGate().evaluate(prediction(confidence=0.99), context)
    assert result.decision == Decision.SAFE_STOP
    assert "obstacle_too_close" in result.reasons


def test_emergency_stop_overrides_everything():
    result = SafetyGate().evaluate(prediction(), RobotContext(emergency_stop=True))
    assert result.decision == Decision.SAFE_STOP
    assert "emergency_stop_active" in result.reasons


def test_communication_failure_stops():
    result = SafetyGate().evaluate(prediction(), RobotContext(communication_ok=False))
    assert result.decision == Decision.SAFE_STOP
    assert "communication_failure" in result.reasons


def test_stale_command_stops():
    old = time() - 2
    result = SafetyGate().evaluate(prediction(created_at=old), RobotContext())
    assert result.decision == Decision.SAFE_STOP
    assert "stale_command" in result.reasons


def test_invalid_probabilities_stop():
    invalid = Prediction(Command.LEFT, {Command.LEFT: 0.8, Command.RIGHT: 0.8})
    result = SafetyGate().evaluate(invalid, RobotContext())
    assert result.decision == Decision.SAFE_STOP
    assert "invalid_probabilities" in result.reasons


def test_bad_threshold_order_is_rejected():
    with pytest.raises(ValueError):
        SafetyGate(SafetyGateConfig(execute_threshold=0.5, restrict_threshold=0.7))
