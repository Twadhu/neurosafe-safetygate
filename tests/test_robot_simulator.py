import pytest

from neurosafe.models import Command
from neurosafe.robot_simulator import CircleObstacle, DifferentialDriveSimulator, RobotState


def test_forward_command_moves_robot():
    simulator = DifferentialDriveSimulator()
    collision = simulator.step(Command.FORWARD, dt_s=1.0)
    assert not collision
    assert simulator.state.x == pytest.approx(0.5)
    assert simulator.state.y == pytest.approx(0.0)


def test_stop_does_not_move_robot():
    simulator = DifferentialDriveSimulator()
    simulator.step(Command.STOP, dt_s=1.0)
    assert simulator.state == RobotState()


def test_collision_does_not_advance_pose():
    simulator = DifferentialDriveSimulator(obstacles=[CircleObstacle(x=0.5, y=0.0, radius=0.20)])
    collision = simulator.step(Command.FORWARD, dt_s=1.0)
    assert collision
    assert simulator.state.x == 0.0
    assert simulator.state.collisions == 1


def test_invalid_speed_scale_is_rejected():
    simulator = DifferentialDriveSimulator()
    with pytest.raises(ValueError):
        simulator.step(Command.FORWARD, speed_scale=1.5)
