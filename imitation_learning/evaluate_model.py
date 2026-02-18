"""
Quick evaluator for a trained imitation policy.
"""

import argparse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from examples.example_vehicle_testing import main as run_vehicle_example  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run vehicle example with ML policy enabled.")
    parser.add_argument("--model-path", default="artifacts/policy/linear_policy.json")
    args = parser.parse_args()

    os.environ["SCHED_USE_ML_POLICY"] = "1"
    os.environ["SCHED_ML_MODEL_PATH"] = args.model_path
    run_vehicle_example()


if __name__ == "__main__":
    main()

