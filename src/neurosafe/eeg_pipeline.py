from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EEGResult:
    subject: int
    trials: int
    balanced_accuracy: float
    expected_calibration_error: float
    brier_score: float
    output_model: str


def train_subject_model(subject: int, output_model: str | Path) -> EEGResult:
    """Train a reproducible CSP + LDA baseline on imagined left/right fist EEG.

    This is a subject-specific educational baseline. It is not evidence of
    cross-subject generalization and must not be presented as a medical system.
    """
    try:
        import joblib
        import mne
        from mne.datasets import eegbci
        from mne.decoding import CSP
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import balanced_accuracy_score, brier_score_loss
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError("EEG dependencies are missing. Run: pip install -e '.[eeg]'") from exc

    mne.set_log_level("WARNING")
    runs = [6, 10, 14]
    files = eegbci.load_data(subject, runs, update_path=False)
    raw = mne.concatenate_raws([mne.io.read_raw_edf(path, preload=True) for path in files])
    eegbci.standardize(raw)
    raw.set_montage("standard_1005", on_missing="ignore")
    raw.filter(7.0, 30.0, fir_design="firwin", skip_by_annotation="edge")

    events, event_id = mne.events_from_annotations(raw, event_id={"T1": 1, "T2": 2})
    picks = mne.pick_types(raw.info, meg=False, eeg=True, stim=False, eog=False)
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=1.0,
        tmax=4.0,
        proj=True,
        picks=picks,
        baseline=None,
        preload=True,
    )
    x = epochs.get_data(copy=True)
    y = epochs.events[:, -1]
    base_pipeline = Pipeline(
        [
            ("csp", CSP(n_components=6, reg="ledoit_wolf", log=True, norm_trace=False)),
            ("lda", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
        ]
    )
    pipeline = CalibratedClassifierCV(base_pipeline, method="sigmoid", cv=3)
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    predictions = cross_val_predict(pipeline, x, y, cv=folds)
    probabilities = cross_val_predict(pipeline, x, y, cv=folds, method="predict_proba")
    score = balanced_accuracy_score(y, predictions)
    class_order = sorted(set(y))
    positive_class = class_order[-1]
    positive_index = class_order.index(positive_class)
    binary_truth = (y == positive_class).astype(int)
    brier = brier_score_loss(binary_truth, probabilities[:, positive_index])
    from .metrics import expected_calibration_error

    confidence = probabilities.max(axis=1).tolist()
    correctness = (predictions == y).tolist()
    calibration_error = expected_calibration_error(confidence, correctness)
    pipeline.fit(x, y)

    model_path = Path(output_model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "classes": {1: "LEFT", 2: "RIGHT"},
            "subject": subject,
            "runs": runs,
            "band_hz": [7.0, 30.0],
            "epoch_seconds": [1.0, 4.0],
            "balanced_accuracy_cv": score,
            "expected_calibration_error_cv": calibration_error,
            "brier_score_cv": brier,
            "evaluation_note": "Nested calibrated subject-specific cross-validation",
        },
        model_path,
    )
    return EEGResult(
        subject,
        len(y),
        float(score),
        float(calibration_error),
        float(brier),
        str(model_path),
    )
