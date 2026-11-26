from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generator" / "generate_data.py"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class GeneratorTests(unittest.TestCase):
    def generate(self, output_dir: Path) -> None:
        subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--output-dir",
                str(output_dir),
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

    def test_same_seed_produces_identical_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first"
            second = Path(temp_dir) / "second"
            self.generate(first)
            self.generate(second)

            for name in (
                "kams.csv",
                "merchants.csv",
                "hubs.csv",
                "orders.csv",
                "issues.csv",
            ):
                with self.subTest(file=name):
                    self.assertEqual(sha256(first / name), sha256(second / name))

    def test_generated_files_have_valid_references_and_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "data"
            self.generate(output)

            kams = csv_rows(output / "kams.csv")
            merchants = csv_rows(output / "merchants.csv")
            hubs = csv_rows(output / "hubs.csv")
            orders = csv_rows(output / "orders.csv")
            issues = csv_rows(output / "issues.csv")

            self.assertEqual(len(kams), 8)
            self.assertEqual(len(hubs), 12)
            self.assertEqual(len(merchants), 300)
            self.assertGreater(len(orders), 3_800)
            self.assertLess(len(orders), 5_200)
            self.assertTrue(
                {row["kam_id"] for row in merchants} <= {row["kam_id"] for row in kams}
            )
            self.assertTrue(
                {row["merchant_id"] for row in orders}
                <= {row["merchant_id"] for row in merchants}
            )
            onboarded_on = {
                row["merchant_id"]: row["onboarding_date"] for row in merchants
            }
            self.assertTrue(
                all(
                    row["order_date"] >= onboarded_on[row["merchant_id"]]
                    for row in orders
                ),
                "a merchant should not have orders dated before onboarding",
            )
            self.assertTrue(
                {row["hub_id"] for row in orders} <= {row["hub_id"] for row in hubs}
            )
            self.assertTrue(
                {row["order_id"] for row in issues}
                <= {row["order_id"] for row in orders}
            )
            self.assertTrue(
                {row["status"] for row in orders}
                <= {"Delivered", "Returned", "Failed", "Cancelled"}
            )
            self.assertTrue({row["status"] for row in issues} <= {"Open", "Resolved"})
            self.assertTrue(
                all(row["resolved_at"] for row in issues if row["status"] == "Resolved")
            )
            self.assertTrue(
                all(not row["resolved_at"] for row in issues if row["status"] == "Open")
            )


if __name__ == "__main__":
    unittest.main()
