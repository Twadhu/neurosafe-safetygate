import pytest

from neurosafe.selective import select_confidence_threshold


def test_threshold_selection_penalizes_confident_errors():
    result = select_confidence_threshold(
        [0.95, 0.82, 0.60, 0.55],
        [True, False, True, False],
        candidates=[0.5, 0.7, 0.9],
    )
    assert result.threshold == 0.9
    assert result.coverage == pytest.approx(0.25)
    assert result.selective_accuracy == 1.0


def test_threshold_selection_prefers_coverage_when_losses_tie():
    result = select_confidence_threshold([0.9, 0.8], [True, True], candidates=[0.5, 0.9])
    assert result.threshold == 0.5
    assert result.coverage == 1.0


@pytest.mark.parametrize(
    ("confidences", "correctness"),
    [([], []), ([0.8], []), ([0.8], [True, False])],
)
def test_threshold_selection_rejects_invalid_inputs(confidences, correctness):
    with pytest.raises(ValueError):
        select_confidence_threshold(confidences, correctness)


def test_threshold_selection_validates_costs_and_grid():
    with pytest.raises(ValueError):
        select_confidence_threshold([0.8], [True], wrong_accept_cost=0)
    with pytest.raises(ValueError):
        select_confidence_threshold([0.8], [True], candidates=[0.4])
