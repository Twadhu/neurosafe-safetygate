from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .metrics import expected_calibration_error
from .models import Command, Prediction, RobotContext
from .safety_gate import SafetyGate, SafetyGateConfig

MOTOR_IMAGERY_RUNS = (4, 8, 12)


@dataclass(frozen=True)
class EEGResult:
    subject: int
    trials: int
    balanced_accuracy: float
    expected_calibration_error: float
    brier_score: float
    output_model: str


@dataclass(frozen=True)
class ParticipantResult:
    held_out_subject: int
    train_subjects: int
    train_trials: int
    test_trials: int
    balanced_accuracy: float
    accuracy: float
    expected_calibration_error: float
    brier_score: float
    coverage: float
    selective_accuracy: float
    safe_stop_rate: float


@dataclass(frozen=True)
class CrossSubjectResult:
    dataset: str
    subjects: tuple[int, ...]
    runs: tuple[int, ...]
    total_trials: int
    evaluation: str
    model: str
    balanced_accuracy_mean: float
    balanced_accuracy_std: float
    accuracy: float
    expected_calibration_error: float
    brier_score: float
    coverage: float
    selective_accuracy: float
    safe_stop_rate: float
    participant_results_csv: str
    predictions_csv: str
    summary_json: str
    output_model: str


def _dependencies():
    try:
        import joblib
        import mne
        from mne.datasets import eegbci
        from mne.decoding import CSP
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import balanced_accuracy_score, brier_score_loss
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError("EEG dependencies are missing. Run: pip install -e '.[eeg]'") from exc
    return {
        "joblib": joblib,
        "mne": mne,
        "eegbci": eegbci,
        "CSP": CSP,
        "LDA": LinearDiscriminantAnalysis,
        "LogisticRegression": LogisticRegression,
        "balanced_accuracy_score": balanced_accuracy_score,
        "brier_score_loss": brier_score_loss,
        "Pipeline": Pipeline,
        "StandardScaler": StandardScaler,
    }


class LogVarianceTransformer:
    """Convert each band-passed epoch into channel-wise log-variance features."""

    def fit(self, x, y=None):
        return self

    def transform(self, x):
        return np.log(np.var(x, axis=2) + 1e-12)

    def get_params(self, deep=True):
        return {}

    def set_params(self, **params):
        return self


def _new_csp_pipeline(deps):
    return deps["Pipeline"](
        [
            (
                "csp",
                deps["CSP"](
                    n_components=6,
                    reg="ledoit_wolf",
                    log=True,
                    norm_trace=False,
                ),
            ),
            (
                "lda",
                deps["LDA"](solver="lsqr", shrinkage="auto"),
            ),
        ]
    )


def _new_cross_subject_pipeline(deps):
    """A participant-robust baseline without subject-specific spatial filters."""
    return deps["Pipeline"](
        [
            ("log_variance", LogVarianceTransformer()),
            ("standardize", deps["StandardScaler"]()),
            (
                "classifier",
                deps["LogisticRegression"](
                    C=0.1,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def load_physionet_epochs(
    subjects: Iterable[int],
    data_dir: str | Path,
    runs: tuple[int, ...] = MOTOR_IMAGERY_RUNS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Download and preprocess left/right motor-imagery epochs.

    Filtering and epoching are performed independently for every participant.
    The returned groups array preserves participant identity for leakage-free
    outer evaluation.
    """
    deps = _dependencies()
    mne = deps["mne"]
    eegbci = deps["eegbci"]
    mne.set_log_level("WARNING")
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    all_x: list[np.ndarray] = []
    all_y: list[np.ndarray] = []
    all_groups: list[np.ndarray] = []
    expected_channels: tuple[str, ...] | None = None

    for subject in subjects:
        files = eegbci.load_data(
            int(subject),
            list(runs),
            path=data_path,
            update_path=False,
            verbose=False,
        )
        raw = mne.concatenate_raws(
            [mne.io.read_raw_edf(path, preload=True, verbose=False) for path in files]
        )
        eegbci.standardize(raw)
        raw.set_montage("colin27_1005", on_missing="ignore")
        raw.filter(7.0, 30.0, fir_design="firwin", skip_by_annotation="edge", verbose=False)
        events, event_id = mne.events_from_annotations(
            raw,
            event_id={"T1": 0, "T2": 1},
            verbose=False,
        )
        epochs = mne.Epochs(
            raw,
            events,
            event_id=event_id,
            tmin=1.0,
            tmax=4.0,
            proj=True,
            baseline=None,
            preload=True,
            picks="eeg",
            verbose=False,
        )
        channel_names = tuple(epochs.ch_names)
        if expected_channels is None:
            expected_channels = channel_names
        elif channel_names != expected_channels:
            raise ValueError(f"Channel mismatch for subject {subject}")

        x_subject = epochs.get_data(copy=True)
        y_subject = epochs.events[:, -1].astype(int)
        all_x.append(x_subject)
        all_y.append(y_subject)
        all_groups.append(np.full(len(y_subject), int(subject), dtype=int))

    return np.concatenate(all_x), np.concatenate(all_y), np.concatenate(all_groups)


def participant_splits(groups: np.ndarray) -> list[tuple[np.ndarray, np.ndarray, int]]:
    """Return leave-one-participant-out splits and assert zero identity overlap."""
    splits: list[tuple[np.ndarray, np.ndarray, int]] = []
    for held_out in sorted(int(value) for value in np.unique(groups)):
        test = np.flatnonzero(groups == held_out)
        train = np.flatnonzero(groups != held_out)
        train_ids = {int(value) for value in groups[train]}
        test_ids = {int(value) for value in groups[test]}
        if train_ids & test_ids:
            raise AssertionError("Participant leakage detected")
        splits.append((train, test, held_out))
    return splits


def _gate_prediction(
    left_probability: float,
    right_probability: float,
    gate: SafetyGate,
):
    predicted = Command.LEFT if left_probability >= right_probability else Command.RIGHT
    prediction = Prediction(
        command=predicted,
        probabilities={Command.LEFT: left_probability, Command.RIGHT: right_probability},
    )
    result = gate.evaluate(prediction, RobotContext(now=prediction.created_at))
    return predicted, result


def run_cross_subject_evaluation(
    subjects: Iterable[int],
    data_dir: str | Path = ".cache/mne",
    output_dir: str | Path = "artifacts/physionet_cross_subject",
    config: SafetyGateConfig | None = None,
) -> CrossSubjectResult:
    """Run leave-one-participant-out motor-imagery evaluation.

    No trial from a held-out participant is used to fit CSP or LDA. This is a
    cross-participant baseline, not a clinical validation.
    """
    deps = _dependencies()
    subject_tuple = tuple(sorted({int(subject) for subject in subjects}))
    if len(subject_tuple) < 3:
        raise ValueError("Cross-subject evaluation requires at least three participants")

    x, y, groups = load_physionet_epochs(subject_tuple, data_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    predictions_path = output / "predictions.csv"
    participants_path = output / "participant_results.csv"
    summary_path = output / "summary.json"
    model_path = output / "logvar_logreg_all_subjects.joblib"
    gate = SafetyGate(config)

    all_truth: list[int] = []
    all_predictions: list[int] = []
    all_right_probabilities: list[float] = []
    all_confidence: list[float] = []
    all_correctness: list[bool] = []
    all_accepted_correctness: list[bool] = []
    participant_rows: list[ParticipantResult] = []
    prediction_rows: list[dict[str, object]] = []

    for train, test, held_out in participant_splits(groups):
        pipeline = _new_cross_subject_pipeline(deps)
        pipeline.fit(x[train], y[train])
        predicted = pipeline.predict(x[test]).astype(int)
        probabilities = pipeline.predict_proba(x[test])
        class_indices = {int(label): index for index, label in enumerate(pipeline.classes_)}
        left = probabilities[:, class_indices[0]]
        right = probabilities[:, class_indices[1]]
        truth = y[test]

        fold_confidence: list[float] = []
        fold_correctness: list[bool] = []
        fold_accepted: list[bool] = []
        fold_accepted_correctness: list[bool] = []
        for trial_number, (truth_value, pred_value, left_p, right_p) in enumerate(
            zip(truth, predicted, left, right, strict=True),
            start=1,
        ):
            command, safety = _gate_prediction(float(left_p), float(right_p), gate)
            correct = bool(pred_value == truth_value)
            accepted = not safety.stopped
            confidence = float(max(left_p, right_p))
            fold_confidence.append(confidence)
            fold_correctness.append(correct)
            fold_accepted.append(accepted)
            if accepted:
                fold_accepted_correctness.append(correct)
                all_accepted_correctness.append(correct)
            prediction_rows.append(
                {
                    "held_out_subject": held_out,
                    "trial": trial_number,
                    "truth": "LEFT" if truth_value == 0 else "RIGHT",
                    "prediction": command.value,
                    "left_probability": float(left_p),
                    "right_probability": float(right_p),
                    "confidence": confidence,
                    "safety_decision": safety.decision.value,
                    "output_command": safety.output_command.value,
                    "speed_scale": safety.speed_scale,
                    "safety_reasons": ";".join(safety.reasons),
                }
            )

        fold_accuracy = float(np.mean(predicted == truth))
        fold_balanced = float(deps["balanced_accuracy_score"](truth, predicted))
        fold_ece = expected_calibration_error(fold_confidence, fold_correctness)
        fold_brier = float(deps["brier_score_loss"](truth, right))
        coverage = float(np.mean(fold_accepted))
        selective_accuracy = (
            float(np.mean(fold_accepted_correctness)) if fold_accepted_correctness else 0.0
        )
        participant_rows.append(
            ParticipantResult(
                held_out_subject=held_out,
                train_subjects=len(subject_tuple) - 1,
                train_trials=len(train),
                test_trials=len(test),
                balanced_accuracy=fold_balanced,
                accuracy=fold_accuracy,
                expected_calibration_error=fold_ece,
                brier_score=fold_brier,
                coverage=coverage,
                selective_accuracy=selective_accuracy,
                safe_stop_rate=1.0 - coverage,
            )
        )
        all_truth.extend(int(value) for value in truth)
        all_predictions.extend(int(value) for value in predicted)
        all_right_probabilities.extend(float(value) for value in right)
        all_confidence.extend(fold_confidence)
        all_correctness.extend(fold_correctness)

    _write_rows(predictions_path, prediction_rows)
    _write_rows(participants_path, [asdict(row) for row in participant_rows])

    final_pipeline = _new_cross_subject_pipeline(deps)
    final_pipeline.fit(x, y)
    deps["joblib"].dump(
        {
            "pipeline": final_pipeline,
            "subjects": subject_tuple,
            "runs": MOTOR_IMAGERY_RUNS,
            "classes": {0: "LEFT", 1: "RIGHT"},
            "band_hz": [7.0, 30.0],
            "epoch_seconds": [1.0, 4.0],
            "model": "7-30 Hz log-variance + StandardScaler + logistic regression",
            "evaluation": "Leave-one-participant-out; all learned steps refit inside every fold",
        },
        model_path,
    )

    balanced_scores = np.array([row.balanced_accuracy for row in participant_rows])
    accepted = [row["output_command"] != "STOP" for row in prediction_rows]
    result = CrossSubjectResult(
        dataset="PhysioNet EEG Motor Movement/Imagery Database v1.0.0",
        subjects=subject_tuple,
        runs=MOTOR_IMAGERY_RUNS,
        total_trials=len(y),
        evaluation="Leave-one-participant-out with no participant overlap",
        model="7-30 Hz log-variance + standardized logistic regression",
        balanced_accuracy_mean=float(balanced_scores.mean()),
        balanced_accuracy_std=float(balanced_scores.std(ddof=1)),
        accuracy=float(np.mean(np.array(all_predictions) == np.array(all_truth))),
        expected_calibration_error=expected_calibration_error(all_confidence, all_correctness),
        brier_score=float(deps["brier_score_loss"](all_truth, all_right_probabilities)),
        coverage=float(np.mean(accepted)),
        selective_accuracy=(
            float(np.mean(all_accepted_correctness)) if all_accepted_correctness else 0.0
        ),
        safe_stop_rate=1.0 - float(np.mean(accepted)),
        participant_results_csv=str(participants_path),
        predictions_csv=str(predictions_path),
        summary_json=str(summary_path),
        output_model=str(model_path),
    )
    summary_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    return result


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty result table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def train_subject_model(subject: int, output_model: str | Path) -> EEGResult:
    """Train a subject-specific CSP + LDA diagnostic baseline.

    This command remains for comparison with earlier releases. New research
    claims should use ``run_cross_subject_evaluation``.
    """
    deps = _dependencies()
    x, y, _ = load_physionet_epochs([subject], Path(output_model).parent / "data")
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pipeline = _new_csp_pipeline(deps)
    predictions = cross_val_predict(pipeline, x, y, cv=folds)
    probabilities = cross_val_predict(pipeline, x, y, cv=folds, method="predict_proba")
    score = deps["balanced_accuracy_score"](y, predictions)
    brier = deps["brier_score_loss"](y, probabilities[:, 1])
    confidence = probabilities.max(axis=1).tolist()
    correctness = (predictions == y).tolist()
    calibration_error = expected_calibration_error(confidence, correctness)
    pipeline.fit(x, y)
    model_path = Path(output_model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    deps["joblib"].dump({"pipeline": pipeline, "subject": subject}, model_path)
    return EEGResult(
        subject,
        len(y),
        float(score),
        float(calibration_error),
        float(brier),
        str(model_path),
    )
