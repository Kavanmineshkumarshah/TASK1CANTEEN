import csv
import os
import tempfile
import unittest
import canteen
from collections import defaultdict
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

# Change 'canteen' below if your main script has a different filename
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import canteen


class TestCanteenBilling(unittest.TestCase):

    def create_temp_csv(self, rows):
        """Helper method to create a temporary CSV file for testing."""
        temp = tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8")
        writer = csv.writer(temp)
        writer.writerows(rows)
        temp.close()
        return temp.name

    # Test 1: Date validation
    def test_01_valid_and_invalid_dates(self):
        self.assertTrue(canteen.is_valid_date("2026-11-19"))
        self.assertFalse(canteen.is_valid_date("19-11-2026"))  # Wrong format
        self.assertFalse(canteen.is_valid_date("2026-02-30"))  # Non-existent date
        self.assertFalse(canteen.is_valid_date("invalid"))

    # Test 2: Decimal parsing
    def test_02_parse_positive_decimal(self):
        self.assertEqual(canteen.parse_positive_decimal("45.50"), Decimal("45.50"))
        self.assertEqual(canteen.parse_positive_decimal("0"), Decimal("0"))
        self.assertIsNone(canteen.parse_positive_decimal("-10"))    # Negative
        self.assertIsNone(canteen.parse_positive_decimal("NaN"))    # Non-finite
        self.assertIsNone(canteen.parse_positive_decimal("abc"))    # Non-numeric

    # Test 3: Row total calculation (with and without 10% bulk discount)
    def test_03_calculate_row_total(self):
        # Quantity < 5 (No discount)
        self.assertEqual(canteen.calculate_row_total(Decimal("4"), Decimal("50")), Decimal("200"))
        # Quantity == 5 (10% discount)
        self.assertEqual(canteen.calculate_row_total(Decimal("5"), Decimal("50")), Decimal("225.00"))
        # Quantity > 5 (10% discount)
        self.assertEqual(canteen.calculate_row_total(Decimal("10"), Decimal("20")), Decimal("180.00"))

    # Test 4: Header validation (valid & mismatch)
    def test_04_validate_header(self):
        # Case-insensitive and whitespace-tolerant valid header
        canteen.validate_header([" Date ", "EMPLOYEE_ID", "item", "Quantity", "PRICE"])

        # Mismatched header should trigger SystemExit
        with self.assertRaises(SystemExit):
            canteen.validate_header(["date", "emp_id", "item", "qty", "cost"])

    # Test 5: Row validation (valid row vs missing/corrupt fields)
    def test_05_validate_and_parse_row(self):
        valid = canteen.validate_and_parse_row(2, ["2026-11-19", "E101", "Lunch", "2", "100"])
        self.assertIsNotNone(valid)
        self.assertEqual(valid["row_total"], Decimal("200"))

        # Empty row, incomplete row, and invalid price
        self.assertIsNone(canteen.validate_and_parse_row(3, ["", "", ""]))
        self.assertIsNone(canteen.validate_and_parse_row(4, ["2026-11-19", "E101"]))
        self.assertIsNone(canteen.validate_and_parse_row(5, ["2026-11-19", "E101", "Tea", "1", "-5"]))

    # Test 6: Weekday subsidy deduction (2026-11-19 is a Thursday)
    def test_06_weekday_subsidy_applied(self):
        valid_rows = [{"date": "2026-11-19", "employee_id": "E101"}]
        daily_totals = defaultdict(Decimal, {("2026-11-19", "E101"): Decimal("150")})

        totals = canteen.calculate_employee_totals(valid_rows, daily_totals)
        # 150 - 60 subsidy = 90
        self.assertEqual(totals["E101"], Decimal("90"))

    # Test 7: Weekday subsidy floor (bill shouldn't go below 0)
    def test_07_weekday_subsidy_floor_at_zero(self):
        valid_rows = [{"date": "2026-11-19", "employee_id": "E101"}]
        daily_totals = defaultdict(Decimal, {("2026-11-19", "E101"): Decimal("40")})

        totals = canteen.calculate_employee_totals(valid_rows, daily_totals)
        # 40 - 60 subsidy = clamped at 0
        self.assertEqual(totals["E101"], Decimal("0"))

    # Test 8: Weekend no subsidy (2026-11-21 is a Saturday)
    def test_08_weekend_no_subsidy(self):
        valid_rows = [{"date": "2026-11-21", "employee_id": "E102"}]
        daily_totals = defaultdict(Decimal, {("2026-11-21", "E102"): Decimal("150")})

        totals = canteen.calculate_employee_totals(valid_rows, daily_totals)
        # Full 150 charged on weekends
        self.assertEqual(totals["E102"], Decimal("150"))

    # Test 9: Monthly cap of 2500 per employee
    def test_09_monthly_max_cap(self):
        valid_rows = [{"date": "2026-11-21", "employee_id": "E103"}]
        daily_totals = defaultdict(Decimal, {("2026-11-21", "E103"): Decimal("3200")})

        totals = canteen.calculate_employee_totals(valid_rows, daily_totals)
        self.assertEqual(totals["E103"], Decimal("2500"))

    # Test 10: End-to-end CSV processing & summary output
    def test_10_end_to_end_csv_and_summary(self):
        csv_data = [
            ["date", "employee_id", "item", "quantity", "price"],
            ["2026-11-19", "E101", "Thali", "2", "100"],     # Weekday: 200 - 60 = 140
            ["2026-11-21", "E102", "Snacks", "5", "40"],     # Weekend + Bulk: (200 * 0.9) = 180
            ["bad-date", "E103", "Coffee", "1", "30"],       # Rejected row
        ]
        temp_path = self.create_temp_csv(csv_data)

        try:
            valid_rows, rejected_rows, daily_totals = canteen.read_and_process_csv(temp_path)
            employee_totals = canteen.calculate_employee_totals(valid_rows, daily_totals)

            with patch("sys.stdout", new=StringIO()) as fake_out:
                canteen.print_summary(employee_totals, len(rejected_rows))
                output = fake_out.getvalue().strip().splitlines()

            self.assertEqual(output, [
                "E101: 140",
                "E102: 180",
                "E103: 0",
                "Total: 320",
                "Rejected: 1"
            ])
        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
