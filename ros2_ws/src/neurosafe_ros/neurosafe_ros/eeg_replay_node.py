from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class EEGReplayNode(Node):
    """Replay participant-disjoint PhysioNet predictions as live messages."""

    def __init__(self) -> None:
        super().__init__("neurosafe_eeg_replay")
        self.declare_parameter("predictions_csv", "")
        self.declare_parameter("held_out_subject", 1)
        self.declare_parameter("period_seconds", 2.0)
        path = Path(str(self.get_parameter("predictions_csv").value))
        subject = int(self.get_parameter("held_out_subject").value)
        if not path.is_file():
            raise FileNotFoundError(f"Prediction CSV not found: {path}")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.rows = [row for row in rows if int(row["held_out_subject"]) == subject]
        if not self.rows:
            raise ValueError(f"No rows found for held-out subject {subject}")
        self.index = 0
        self.publisher = self.create_publisher(String, "/neurosafe/eeg_prediction", 10)
        period = float(self.get_parameter("period_seconds").value)
        self.timer = self.create_timer(period, self.publish_next)
        self.get_logger().info(
            f"Loaded {len(self.rows)} real-EEG predictions for subject {subject}"
        )

    def publish_next(self) -> None:
        row = self.rows[self.index]
        payload = {
            "held_out_subject": int(row["held_out_subject"]),
            "trial": int(row["trial"]),
            "truth": row["truth"],
            "command": row["prediction"],
            "probabilities": {
                "LEFT": float(row["left_probability"]),
                "RIGHT": float(row["right_probability"]),
            },
            "created_at": time.time(),
        }
        message = String()
        message.data = json.dumps(payload)
        self.publisher.publish(message)
        self.get_logger().info(
            f"trial={payload['trial']} truth={payload['truth']} command={payload['command']}"
        )
        self.index = (self.index + 1) % len(self.rows)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EEGReplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
