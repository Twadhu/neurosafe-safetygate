from glob import glob

from setuptools import find_packages, setup

package_name = "neurosafe_ros"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/worlds", glob("worlds/*.sdf")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Abdullah Faisal Abdo Othman Abbas",
    maintainer_email="b26dcdk900@stu.ptit.edu.vn",
    description="ROS 2 and Gazebo integration for NeuroSafe SafetyGate.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "eeg_replay = neurosafe_ros.eeg_replay_node:main",
            "safety_gate = neurosafe_ros.safety_gate_node:main",
        ],
    },
)
