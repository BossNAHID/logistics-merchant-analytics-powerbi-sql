from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generator" / "generate_data.py"
ANALYSIS = ROOT / "analysis" / "analyze_delivery.py"


class AnalysisTests(unittest.TestCase):
    def test_analysis_writes_a_transparent_regression_and_three_month_forecast(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            data_dir = temp / "data"
            results_dir = temp / "results"
            subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--output-dir",
                    str(data_dir),
                    "--seed",
                    "731",
                    "--target-orders",
                    "4500",
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ANALYSIS),
                    "--data-dir",
                    str(data_dir),
                    "--output-dir",
                    str(results_dir),
                ],
                check=True,
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            summary = json.loads(
                (results_dir / "analysis_summary.json").read_text(encoding="utf-8")
            )
            with (results_dir / "monthly_forecast.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                forecast = list(csv.DictReader(handle))
            with (results_dir / "hub_delivery_return.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                hub_rows = list(csv.DictReader(handle))

            self.assertEqual(len(forecast), 3)
            self.assertEqual(len(hub_rows), 12)
            self.assertEqual(summary["forecast_method"], "flat 3-month moving average")
            self.assertIn("not a causal estimate", summary["regression_caveat"])
            self.assertTrue(all(float(row["forecast_orders"]) > 0 for row in forecast))
            self.assertLessEqual(abs(float(summary["hub_correlation"])), 1)
            self.assertGreater(float(summary["hub_slope_return_rate_per_day"]), 0)


if __name__ == "__main__":
    unittest.main()
