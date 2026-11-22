from __future__ import annotations

import json
from math import isfinite

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String

from neurosafe.models import Command, Prediction, RobotContext
from neurosafe.ros_adapter import command_to_velocity
from neurosafe.safety_gate import SafetyGate, SafetyGateConfig


class SafetyGateNode(Node):
    """Apply SafetyGate to EEG predictions and publish safe robot velocity."""

    def __init__(self) -> None:
        super().__init__("neurosafe_safety_gate")
        self.declare_parameter("config_path", "config/default.json")
        config_path = str(self.get_parameter("config_path").value)
        try:
            config = SafetyGateConfig.from_json(config_path)
        except FileNotFoundError:
            self.get_logger().warning("Config not found; using built-in safe defaults")
            config = SafetyGateConfig()
        self.gate = SafetyGate(config)
        self.closest_obstacle: float | None = None
        self.emergency_stop = False
        self.velocity_publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.status_publisher = self.create_publisher(String, "/neurosafe/status", 10)
        self.create_subscription(String, "/neurosafe/eeg_prediction", self.on_prediction, 10)
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Bool, "/neurosafe/emergency_stop", self.on_emergency, 10)

    def on_scan(self, message: LaserScan) -> None:
        valid = [distance for distance in message.ranges if isfinite(distance) and distance > 0]
        self.closest_obstacle = min(valid) if valid else None

    def on_emergency(self, message: Bool) -> None:
        self.emergency_stop = bool(message.data)
        if self.emergency_stop:
            self.publish_stop()

    def on_prediction(self, message: String) -> None:
        try:
            payload = json.loads(message.data)
            probabilities = {
                Command(name): float(value) for name, value in payload["probabilities"].items()
            }
            prediction = Prediction(
                command=Command(payload["command"]),
                probabilities=probabilities,
                created_at=float(payload["created_at"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.get_logger().error(f"Rejected malformed prediction: {exc}")
            self.publish_stop()
            return

        result = self.gate.evaluate(
            prediction,
            RobotContext(
                obstacle_distance_m=self.closest_obstacle,
                emergency_stop=self.emergency_stop,
            ),
        )
        velocity = command_to_velocity(
            result.output_command,
            result.speed_scale,
            normal_speed_mps=self.gate.config.normal_speed_mps,
        )
        twist = Twist()
        twist.linear.x = velocity.linear_x
        twist.angular.z = velocity.angular_z
        self.velocity_publisher.publish(twist)
        status = String()
        status.data = json.dumps(
            {
                "requested_command": result.requested_command.value,
                "output_command": result.output_command.value,
                "decision": result.decision.value,
                "confidence": result.confidence,
                "entropy": result.entropy,
                "speed_scale": result.speed_scale,
                "closest_obstacle_m": self.closest_obstacle,
                "reasons": list(result.reasons),
            }
        )
        self.status_publisher.publish(status)

    def publish_stop(self) -> None:
        self.velocity_publisher.publish(Twist())


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetyGateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()
