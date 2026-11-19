from collections import defaultdict
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sys

EXPECTED_HEADER = ["date", "employee_id", "item", "quantity", "price"]
SUBSIDY = Decimal("60")
MONTHLY_MAX = Decimal("2500")


def parse_cli_args():
    """Validate and return the CSV file path from command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_file>")
        sys.exit(1)
    return sys.argv[1]


def validate_header(header):
    """Check if the CSV header is present and matches the expected columns."""
    if header is None:
        print("Error: The CSV file is completely empty.")
        sys.exit(1)

    actual_header = [col.strip().lower() for col in header]
    expected_header_lower = [col.lower() for col in EXPECTED_HEADER]

    if actual_header != expected_header_lower:
        print("Header Mismatch Error!")
        print(f"Expected: {EXPECTED_HEADER}")
        print(f"Received: {header}")
        sys.exit(1)


def is_valid_date(date_str):
    """Return True if date_str matches YYYY-MM-DD format, otherwise False."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d").date()
        return True
    except ValueError:
        return False


def parse_positive_decimal(val_str):
    """Parse a string as a non-negative finite Decimal, or return None if invalid."""
    try:
        value = Decimal(val_str)
        if not value.is_finite() or value < Decimal("0"):
            return None
        return value
    except InvalidOperation:
        return None


def calculate_row_total(quantity, price):
    """Calculate item total with a 10% bulk discount for quantities of 5 or more."""
    if quantity >= Decimal("5"):
        return quantity * price * Decimal("0.90")
    return quantity * price


def validate_and_parse_row(line_num, row):
    """Validate a single CSV row and return a parsed dictionary, or None if invalid."""
    if not row or all(not cell.strip() for cell in row):
        print(f"line{line_num}:empty row")
        return None

    if len(row) < 5:
        print(f"line{line_num}:incomplete row data")
        return None

    date_str = row[0].strip()
    employee_id = row[1].strip()
    item = row[2].strip()
    qty_str = row[3].strip()
    price_str = row[4].strip()

    if not is_valid_date(date_str):
        print(f"line{line_num}:invalid date")
        return None

    if not employee_id:
        print(f"line{line_num}:missing employee")
        return None

    if not item:
        print(f"line{line_num}:missing item")
        return None

    quantity = parse_positive_decimal(qty_str)
    if quantity is None:
        print(f"line{line_num}:invalid quantity")
        return None

    price = parse_positive_decimal(price_str)
    if price is None:
        print(f"line{line_num}:invalid price")
        return None

    return {
        "date": date_str,
        "employee_id": employee_id,
        "item": item,
        "quantity": quantity,
        "price": price,
        "row_total": calculate_row_total(quantity, price),
    }


def read_and_process_csv(file_name):
    """Read the CSV file, validate rows, and group valid totals by date and employee."""
    valid_rows = []
    rejected_rows = []
    daily_totals = defaultdict(Decimal)

    try:
        with open(file_name, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            validate_header(next(reader, None))

            for line_num, row in enumerate(reader, start=2):
                parsed_row = validate_and_parse_row(line_num, row)
                if parsed_row is None:
                    rejected_rows.append(row)
                    continue

                valid_rows.append(parsed_row)
                group_key = (parsed_row["date"], parsed_row["employee_id"])
                daily_totals[group_key] += parsed_row["row_total"]

    except FileNotFoundError:
        print(f"Error: {file_name} file not found.")
        sys.exit(1)

    return valid_rows, rejected_rows, daily_totals


def calculate_employee_totals(valid_rows, daily_totals):
    """Apply weekday subsidies and the ₹2,500 monthly cap per employee."""
    employee_final_totals = defaultdict(Decimal)
    processed_days = set()

    for item_row in valid_rows:
        d = item_row["date"]
        emp = item_row["employee_id"]
        unique_day_key = (d, emp)

        if unique_day_key in processed_days:
            continue

        gross_total = daily_totals[unique_day_key]
        date_obj = datetime.strptime(d, "%Y-%m-%d").date()
        is_subsidy_applicable = date_obj.weekday() not in (5, 6)

        if not is_subsidy_applicable:
            final_bill = gross_total
        else:
            final_bill = max(Decimal("0"), gross_total - SUBSIDY)

        employee_final_totals[emp] += final_bill
        processed_days.add(unique_day_key)

    for emp in employee_final_totals:
        if employee_final_totals[emp] > MONTHLY_MAX:
            employee_final_totals[emp] = MONTHLY_MAX

    return employee_final_totals


def print_summary(employee_final_totals, rejected_count):
    """Print the final rounded totals for E101, E102, E103, overall total, and rejected count."""
    employees = ["E101", "E102", "E103"]
    bills = {
        emp: employee_final_totals[emp].quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        for emp in employees
    }
    total = sum(bills.values(), Decimal("0"))

    for emp in employees:
        print(f"{emp}: {bills[emp]}")
    print(f"Total: {total}")
    print(f"Rejected: {rejected_count}")


if __name__ == "__main__":
    csv_file = parse_cli_args()
    valid_rows, rejected_rows, daily_totals = read_and_process_csv(csv_file)
    employee_totals = calculate_employee_totals(valid_rows, daily_totals)
    print_summary(employee_totals, len(rejected_rows))
