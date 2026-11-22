from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("neurosafe_ros")
    world = PathJoinSubstitution([package_share, "worlds", "neurosafe_world.sdf"])
    predictions_csv = LaunchConfiguration("predictions_csv")
    held_out_subject = LaunchConfiguration("held_out_subject")
    config_path = LaunchConfiguration("config_path")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": ["-r -v 3 ", world]}.items(),
    )
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ],
        output="screen",
    )
    safety_gate = Node(
        package="neurosafe_ros",
        executable="safety_gate",
        parameters=[{"config_path": config_path}],
        output="screen",
    )
    replay = TimerAction(
        period=4.0,
        actions=[
            Node(
                package="neurosafe_ros",
                executable="eeg_replay",
                parameters=[
                    {
                        "predictions_csv": predictions_csv,
                        "held_out_subject": held_out_subject,
                        "period_seconds": 2.0,
                    }
                ],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("predictions_csv"),
            DeclareLaunchArgument("held_out_subject", default_value="1"),
            DeclareLaunchArgument("config_path", default_value="config/default.json"),
            gazebo,
            bridge,
            safety_gate,
            replay,
        ]
    )
