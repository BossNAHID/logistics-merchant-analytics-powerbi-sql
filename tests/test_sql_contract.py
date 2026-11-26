from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SqlContractTests(unittest.TestCase):
    def test_order_delivery_days_column_accepts_generator_decimal_format(self) -> None:
        schema = (ROOT / "sql" / "01_schema.sql").read_text(encoding="utf-8")
        self.assertRegex(
            schema,
            re.compile(
                r"\bdelivery_days\s+numeric\s*\(\s*4\s*,\s*1\s*\)", re.IGNORECASE
            ),
        )

    def test_csv_load_is_atomic_when_a_copy_fails(self) -> None:
        load_script = (ROOT / "sql" / "02_load.sql").read_text(encoding="utf-8")
        self.assertRegex(load_script, re.compile(r"(?m)^BEGIN;\s*$"))
        self.assertRegex(load_script, re.compile(r"(?m)^COMMIT;\s*$"))


if __name__ == "__main__":
    unittest.main()
