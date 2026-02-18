"""
Train policy model from collected imitation trajectories.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from imitation_learning.config import DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH  # noqa: E402
from imitation_learning.train_model import train_linear_policy  # noqa: E402


def main():
    result = train_linear_policy(DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH)
    print("Training complete")
    print(f"  model={DEFAULT_MODEL_PATH}")
    print(f"  rows={result['train_rows']}, decisions={result['train_decisions']}")
    print(f"  train_mse={result['train_mse']:.6f}")


if __name__ == "__main__":
    main()

