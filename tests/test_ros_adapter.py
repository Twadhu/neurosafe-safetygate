import csv

import pytest

from neurosafe.models import Command
from neurosafe.ros_adapter import command_to_velocity, load_replay_rows, shared_control_velocity


@pytest.mark.parametrize(
    ("command", "linear", "angular"),
    [
        (Command.STOP, 0.0, 0.0),
        (Command.FORWARD, 0.25, 0.0),
        (Command.LEFT, 0.0, 0.6),
        (Command.RIGHT, 0.0, -0.6),
    ],
)
def test_command_to_velocity(command, linear, angular):
    velocity = command_to_velocity(command, 0.5)
    assert velocity.linear_x == pytest.approx(linear)
    assert velocity.angular_z == pytest.approx(angular)


def test_speed_scale_is_bounded():
    assert command_to_velocity(Command.FORWARD, 3.0).linear_x == 0.5
    assert command_to_velocity(Command.FORWARD, -1.0).linear_x == 0.0


def test_replay_rows_can_select_a_held_out_subject(tmp_path):
    path = tmp_path / "predictions.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["held_out_subject", "prediction"])
        writer.writeheader()
        writer.writerows(
            [
                {"held_out_subject": "1", "prediction": "LEFT"},
                {"held_out_subject": "2", "prediction": "RIGHT"},
            ]
        )
    assert load_replay_rows(path, 2)[0]["prediction"] == "RIGHT"


def test_replay_rows_rejects_empty_selection(tmp_path):
    path = tmp_path / "predictions.csv"
    path.write_text("held_out_subject,prediction\n1,LEFT\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_replay_rows(path, 9)


def test_shared_control_combines_steering_and_safe_forward_motion():
    velocity = shared_control_velocity(Command.LEFT, 1.0, obstacle_distance_m=2.0)
    assert velocity.linear_x == pytest.approx(0.225)
    assert velocity.angular_z == pytest.approx(1.2)


@pytest.mark.parametrize("distance", [None, 0.2])
def test_shared_control_fails_closed_without_clear_lidar(distance):
    assert shared_control_velocity(Command.RIGHT, 1.0, distance) == command_to_velocity(
        Command.STOP, 0.0
    )
