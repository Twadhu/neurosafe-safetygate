from neurosafe.safety_gate import SafetyGate
from neurosafe.simulation import run_experiment


def test_simulation_is_reproducible_and_gate_reduces_unsafe_execution(tmp_path):
    first, metrics_a = run_experiment(SafetyGate(), 200, 42, tmp_path / "trials.csv")
    second, metrics_b = run_experiment(SafetyGate(), 200, 42)
    assert first == second
    assert metrics_a == metrics_b
    assert metrics_a["gated_unsafe_rate"] <= metrics_a["direct_unsafe_rate"]
    assert (tmp_path / "trials.csv").exists()
