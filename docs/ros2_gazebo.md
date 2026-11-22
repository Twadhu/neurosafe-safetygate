# ROS 2 and Gazebo integration

This integration replays predictions produced by the participant-disjoint
PhysioNet evaluation. It does not pretend that prerecorded EEG was recorded in
the simulated environment. The replay evaluates the downstream safety and
control path using authentic model outputs, while Gazebo supplies the current
robot context through lidar.

Version 1.0 fails closed when lidar is unavailable and publishes zero velocity
when the EEG prediction stream exceeds its timeout. LEFT and RIGHT are treated
as steering intent; cautious forward motion is supplied by shared control only
while lidar reports sufficient clearance.

## Supported stack

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic
- `ros_gz_sim` and `ros_gz_bridge`

## Build

Run the EEG evaluation first from the repository root:

```bash
pip install -e ".[eeg]"
neurosafe evaluate-eeg --subjects 1-10
```

Then build the ROS workspace. The main Python package must be available in the
same environment so the ROS node can import `neurosafe`.

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Launch

Use an absolute prediction path and an actually evaluated subject ID:

```bash
ros2 launch neurosafe_ros neurosafe_gazebo.launch.py \
  predictions_csv:=$(realpath ../artifacts/physionet_cross_subject/predictions.csv) \
  held_out_subject:=1 \
  config_path:=$(realpath ../config/default.json)
```

Important topics:

| Topic | Type | Purpose |
|---|---|---|
| `/neurosafe/eeg_prediction` | `std_msgs/String` | Real EEG model probabilities as JSON |
| `/scan` | `sensor_msgs/LaserScan` | Gazebo lidar context |
| `/neurosafe/emergency_stop` | `std_msgs/Bool` | Manual hard stop |
| `/neurosafe/status` | `std_msgs/String` | Auditable SafetyGate result |
| `/cmd_vel` | `geometry_msgs/Twist` | Safe robot velocity |

## Scientific boundary

PhysioNet trials encode left or right motor imagery in the original BCI task.
They do not encode a user's reaction to this Gazebo scene. The integration is a
reproducible open-loop replay for validating software plumbing, confidence
gating, obstacle overrides, and safe stopping. A later closed-loop experiment
requires live synchronized EEG and ethics approval.
