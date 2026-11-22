from neurosafe.safety_gate import SafetyGate
from neurosafe.simulation import run_experiment, run_threshold_sweep


def test_simulation_is_reproducible_and_gate_reduces_unsafe_execution(tmp_path):
    first, metrics_a = run_experiment(SafetyGate(), 200, 42, tmp_path / "trials.csv")
    second, metrics_b = run_experiment(SafetyGate(), 200, 42)
    assert first == second
    assert metrics_a == metrics_b
    assert metrics_a["gated_unsafe_rate"] <= metrics_a["direct_unsafe_rate"]
    assert metrics_a["gated_weighted_risk"] <= metrics_a["direct_weighted_risk"]
    assert 0 <= metrics_a["coverage"] <= 1
    assert 0 <= metrics_a["selective_accuracy"] <= 1
    assert (tmp_path / "trials.csv").exists()


def test_threshold_sweep_reuses_scenarios_and_is_reproducible(tmp_path):
    first = run_threshold_sweep(300, 7, tmp_path / "sweep.csv")
    second = run_threshold_sweep(300, 7)
    assert first == second
    assert len(first) == 6
    assert (tmp_path / "sweep.csv").exists()


def test_experiment_writes_machine_readable_summary(tmp_path):
    summary = tmp_path / "summary.json"
    run_experiment(SafetyGate(), 50, 4, summary_json=summary)
    content = summary.read_text(encoding="utf-8")
    assert '"expected_calibration_error"' in content
