from __future__ import annotations

import argparse
import json
from pathlib import Path

from .eeg_pipeline import train_subject_model
from .safety_gate import SafetyGate, SafetyGateConfig
from .simulation import run_experiment


def _config(path: str) -> SafetyGateConfig:
    return SafetyGateConfig.from_json(path)


def main() -> None:
    parser = argparse.ArgumentParser(prog="neurosafe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="Compare direct control with SafetyGate")
    simulate.add_argument("--config", default="config/default.json")
    simulate.add_argument("--trials", type=int, default=500)
    simulate.add_argument("--seed", type=int, default=42)
    simulate.add_argument("--output", default="artifacts/simulation_trials.csv")

    eeg = subparsers.add_parser("train-eeg", help="Train the PhysioNet CSP + LDA baseline")
    eeg.add_argument("--subject", type=int, default=1)
    eeg.add_argument("--output", default="artifacts/eeg_subject_001.joblib")

    args = parser.parse_args()
    if args.command == "simulate":
        gate = SafetyGate(_config(args.config))
        _, metrics = run_experiment(gate, args.trials, args.seed, args.output)
        print(json.dumps(metrics, indent=2))
        print(f"Trial log: {Path(args.output).resolve()}")
    elif args.command == "train-eeg":
        result = train_subject_model(args.subject, args.output)
        print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
