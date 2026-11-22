from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from neurosafe.robot_simulator import run_robot_demo
from neurosafe.safety_gate import SafetyGate, SafetyGateConfig
from neurosafe.simulation import run_experiment, run_threshold_sweep

st.set_page_config(page_title="NeuroSafe SafetyGate", page_icon="🧠", layout="wide")


@st.cache_data(show_spinner=False)
def experiment_data(
    execute: float, restrict: float, obstacle: float, trials: int, seed: int
) -> tuple[pd.DataFrame, dict[str, float]]:
    config = SafetyGateConfig(
        execute_threshold=execute,
        restrict_threshold=restrict,
        minimum_obstacle_distance_m=obstacle,
    )
    records, metrics = run_experiment(SafetyGate(config), trials, seed)
    return pd.DataFrame(asdict(record) for record in records), metrics


@st.cache_data(show_spinner=False)
def threshold_data(trials: int, seed: int) -> pd.DataFrame:
    return pd.DataFrame(run_threshold_sweep(trials, seed))


st.title("NeuroSafe SafetyGate")
st.caption("Confidence-aware command filtering for assistive robot research")

with st.sidebar:
    st.header("Experiment controls")
    execute = st.slider("Execute threshold", 0.50, 0.99, 0.80, 0.01)
    restrict = st.slider("Restrict threshold", 0.20, execute, min(0.60, execute), 0.01)
    obstacle = st.slider("Minimum obstacle distance (m)", 0.10, 1.00, 0.35, 0.05)
    trials = st.slider("Simulation trials", 100, 5000, 1000, 100)
    seed = int(st.number_input("Random seed", value=42, step=1))
    st.divider()
    st.caption("Version 0.2 research prototype")

data, metrics = experiment_data(execute, restrict, obstacle, trials, seed)
overview, tradeoffs, robot, log = st.tabs(
    ["Safety overview", "Threshold trade-offs", "Robot demo", "Trial audit log"]
)

with overview:
    first = st.columns(4)
    first[0].metric("Direct unsafe rate", f"{metrics['direct_unsafe_rate']:.1%}")
    first[1].metric("SafetyGate unsafe rate", f"{metrics['gated_unsafe_rate']:.1%}")
    first[2].metric("Unsafe cases reduced", f"{metrics['unsafe_reduction_rate']:.1%}")
    first[3].metric("Coverage", f"{metrics['coverage']:.1%}")

    second = st.columns(4)
    second[0].metric("Selective accuracy", f"{metrics['selective_accuracy']:.1%}")
    second[1].metric("False rejection", f"{metrics['false_rejection_rate']:.1%}")
    second[2].metric("Calibration error", f"{metrics['expected_calibration_error']:.3f}")
    second[3].metric("Brier score", f"{metrics['multiclass_brier_score']:.3f}")

    left, right = st.columns(2)
    with left:
        st.subheader("Decision distribution")
        st.bar_chart(data["gate_decision"].value_counts())
    with right:
        st.subheader("Weighted risk")
        risk = pd.DataFrame(
            {
                "risk": [
                    metrics["direct_weighted_risk"],
                    metrics["gated_weighted_risk"],
                ]
            },
            index=["Direct control", "SafetyGate"],
        )
        st.bar_chart(risk)

with tradeoffs:
    st.subheader("Risk-coverage threshold study")
    sweep = threshold_data(trials, seed)
    st.line_chart(
        sweep.set_index("execute_threshold")[["coverage", "gated_unsafe_rate"]],
        x_label="Execute threshold",
        y_label="Rate",
    )
    st.dataframe(
        sweep[
            [
                "execute_threshold",
                "restrict_threshold",
                "coverage",
                "selective_accuracy",
                "gated_unsafe_rate",
                "false_rejection_rate",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Every threshold is evaluated on the same generated scenarios and random seed.")

with robot:
    st.subheader("Deterministic differential-drive demonstration")
    robot_data = pd.DataFrame(asdict(record) for record in run_robot_demo())
    st.line_chart(robot_data.set_index("step")[["x", "y"]])
    st.dataframe(robot_data, use_container_width=True, hide_index=True)
    st.caption(
        "This lightweight simulator validates command integration. Gazebo remains the target "
        "for higher-fidelity robot dynamics."
    )

with log:
    st.subheader("Trial-level audit log")
    selected_decisions = st.multiselect(
        "Decision filter",
        sorted(data["gate_decision"].unique()),
        default=sorted(data["gate_decision"].unique()),
    )
    filtered = data[data["gate_decision"].isin(selected_decisions)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download experiment CSV",
        data.to_csv(index=False),
        file_name="neurosafe_experiment.csv",
        mime="text/csv",
    )

st.warning(
    "Educational research prototype only. Synthetic and offline EEG results do not establish "
    "medical safety or real-world clinical performance."
)
