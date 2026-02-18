"""
Trajectory recording helpers for imitation learning.
"""

from datetime import datetime
import json
import os
from typing import Dict, Optional


class TrajectoryRecorder:
    """
    Writes scheduling decisions as NDJSON.

    Each line is one decision step to keep files append-friendly and easy to stream.
    """

    def __init__(self, output_path: str, run_metadata: Optional[Dict] = None):
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._fh = open(output_path, "w", encoding="utf-8")
        self._step = 0
        self._write(
            {
                "record_type": "run_header",
                "created_at_utc": datetime.utcnow().isoformat(),
                "run_metadata": run_metadata or {},
            }
        )

    def record_decision(self, decision_payload: Dict):
        payload = dict(decision_payload)
        payload["record_type"] = "decision"
        payload["step"] = self._step
        self._step += 1
        self._write(payload)

    def record_run_summary(self, summary: Dict):
        self._write(
            {
                "record_type": "run_summary",
                "created_at_utc": datetime.utcnow().isoformat(),
                **summary,
            }
        )

    def _write(self, payload: Dict):
        self._fh.write(json.dumps(payload) + "\n")
        self._fh.flush()

    def close(self):
        if not self._fh.closed:
            self._fh.close()

