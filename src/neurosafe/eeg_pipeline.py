from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EEGResult:
    subject: int
    trials: int
    balanced_accuracy: float
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
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.metrics import balanced_accuracy_score
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
    pipeline = Pipeline(
        [
            ("csp", CSP(n_components=6, reg="ledoit_wolf", log=True, norm_trace=False)),
            ("lda", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
        ]
    )
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    predictions = cross_val_predict(pipeline, x, y, cv=folds)
    score = balanced_accuracy_score(y, predictions)
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
        },
        model_path,
    )
    return EEGResult(subject, len(y), float(score), str(model_path))
