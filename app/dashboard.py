from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from neurosafe.safety_gate import SafetyGate, SafetyGateConfig
from neurosafe.simulation import run_experiment

st.set_page_config(page_title="NeuroSafe SafetyGate", page_icon="🧠", layout="wide")
st.title("NeuroSafe SafetyGate")
st.caption("Confidence-aware command filtering for assistive robot research")

with st.sidebar:
    st.header("Safety thresholds")
    execute = st.slider("Execute threshold", 0.50, 0.99, 0.80, 0.01)
    restrict = st.slider("Restrict threshold", 0.20, execute, min(0.60, execute), 0.01)
    obstacle = st.slider("Minimum obstacle distance (m)", 0.10, 1.00, 0.35, 0.05)
    trials = st.slider("Simulation trials", 100, 5000, 500, 100)
    seed = st.number_input("Random seed", value=42, step=1)

config = SafetyGateConfig(
    execute_threshold=execute,
    restrict_threshold=restrict,
    minimum_obstacle_distance_m=obstacle,
)
output = Path("artifacts/dashboard_trials.csv")
records, metrics = run_experiment(SafetyGate(config), trials, int(seed), output)
data = pd.DataFrame(record.__dict__ for record in records)

columns = st.columns(4)
columns[0].metric("Direct unsafe rate", f"{metrics['direct_unsafe_rate']:.1%}")
columns[1].metric("SafetyGate unsafe rate", f"{metrics['gated_unsafe_rate']:.1%}")
columns[2].metric("Unsafe cases reduced", f"{metrics['unsafe_reduction_rate']:.1%}")
columns[3].metric("Safe-stop rate", f"{metrics['safe_stop_rate']:.1%}")

st.subheader("Decision distribution")
st.bar_chart(data["gate_decision"].value_counts())

st.subheader("Trial log")
st.dataframe(data, use_container_width=True, hide_index=True)
st.download_button(
    "Download experiment CSV",
    data.to_csv(index=False),
    file_name="neurosafe_experiment.csv",
    mime="text/csv",
)

st.info(
    "This is an educational research prototype. Synthetic simulation results do not "
    "establish medical safety or real-world clinical performance."
)
