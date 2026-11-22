import pytest

from neurosafe.metrics import expected_calibration_error, multiclass_brier_score, percentile


def test_perfect_calibration_has_zero_error():
    assert expected_calibration_error([1.0, 1.0], [True, True]) == pytest.approx(0.0)


def test_calibration_rejects_mismatched_inputs():
    with pytest.raises(ValueError):
        expected_calibration_error([0.8], [True, False])


def test_multiclass_brier_score_is_zero_for_perfect_predictions():
    rows = [{"LEFT": 1.0, "RIGHT": 0.0}, {"LEFT": 0.0, "RIGHT": 1.0}]
    assert multiclass_brier_score(rows, ["LEFT", "RIGHT"], ["LEFT", "RIGHT"]) == 0.0


def test_percentile_interpolates():
    assert percentile([0.0, 10.0], 0.5) == pytest.approx(5.0)
