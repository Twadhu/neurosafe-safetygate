from __future__ import annotations

import argparse
import json
from pathlib import Path

from .eeg_pipeline import train_subject_model
from .robot_simulator import run_robot_demo
from .safety_gate import SafetyGate, SafetyGateConfig
from .simulation import run_experiment, run_threshold_sweep


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
    simulate.add_argument("--summary", default="artifacts/simulation_summary.json")

    sweep = subparsers.add_parser("sweep", help="Evaluate safety threshold trade-offs")
    sweep.add_argument("--trials", type=int, default=1000)
    sweep.add_argument("--seed", type=int, default=42)
    sweep.add_argument("--output", default="artifacts/threshold_sweep.csv")

    robot = subparsers.add_parser("robot-demo", help="Run the deterministic 2D robot demo")
    robot.add_argument("--output", default="artifacts/robot_demo.csv")

    eeg = subparsers.add_parser("train-eeg", help="Train the PhysioNet CSP + LDA baseline")
    eeg.add_argument("--subject", type=int, default=1)
    eeg.add_argument("--output", default="artifacts/eeg_subject_001.joblib")

    args = parser.parse_args()
    if args.command == "simulate":
        gate = SafetyGate(_config(args.config))
        _, metrics = run_experiment(
            gate,
            args.trials,
            args.seed,
            args.output,
            args.summary,
        )
        print(json.dumps(metrics, indent=2))
        print(f"Trial log: {Path(args.output).resolve()}")
        print(f"Summary: {Path(args.summary).resolve()}")
    elif args.command == "sweep":
        rows = run_threshold_sweep(args.trials, args.seed, args.output)
        print(json.dumps(rows, indent=2))
        print(f"Threshold study: {Path(args.output).resolve()}")
    elif args.command == "robot-demo":
        records = run_robot_demo(args.output)
        print(json.dumps([record.__dict__ for record in records], indent=2))
        print(f"Robot path: {Path(args.output).resolve()}")
    elif args.command == "train-eeg":
        result = train_subject_model(args.subject, args.output)
        print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
