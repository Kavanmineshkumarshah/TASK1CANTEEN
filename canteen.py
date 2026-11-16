import csv
import sys
from collections import defaultdict
from datetime import datetime

EXPECTED_HEADER = ["date", "employee_id", "item", "quantity", "price"]
subsidy = 60
MONTHLY_MAX = 2500.0

valid_rows = []
daily_totals = defaultdict(float)
employee_final_totals = defaultdict(float)

try:
    with open('orders_sample.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader, None)
        
        if header is None:
            print("Error: The CSV file is completely empty.")
            sys.exit(1)
            
        actual_header = [col.strip().lower() for col in header]
        expected_header_lower = [col.lower() for col in EXPECTED_HEADER]
        
        # Validate if headers match the expected layout
        if actual_header != expected_header_lower:
            print("Header Mismatch Error!")
            print(f"Expected: {EXPECTED_HEADER}")
            print(f"Received: {header}")
            sys.exit(1)
            
        for row in reader:
            if len(row) < 5:
                print(f"incomplete row data: {row}")
                continue
                
            date_str = row[0].strip()
            product_id = row[1].strip()  # Holds employee_id (e.g., E101) per your CSV column order
            employee_id = row[2].strip()
            
            try:
                datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"line14:invalid date ")
                continue
                
            if product_id and str(product_id).strip():
                try:
                    quantity = float(row[3].strip())
                    price = float(row[4].strip())
                    
                    if quantity < 0:
                        print(f"line15:invalid quantity ")
                        continue
                    elif quantity >= 5:
                        row_total = quantity * price * 0.90
                    else:
                        row_total = quantity * price
                        
                    valid_rows.append({
                        'date': date_str,
                        'product_id': product_id,
                        'employee_id': employee_id,
                        'quantity': quantity,
                        'price': price,
                        'row_total': row_total
                    })
                    
                    group_key = (date_str, product_id)
                    daily_totals[group_key] += row_total
                    
                except ValueError:
                    print(f"line17:invalid price")
            else:
                print(f"line16:missing employee")

except FileNotFoundError:
    print("Error: 'orders_sample.csv' file not found.")
    sys.exit(1)

# Calculate daily bills after weekday subsidy
processed_days = set()
for item_row in valid_rows:
    d = item_row['date']
    emp = item_row['product_id']
    unique_day_key = (d, emp)
    
    gross_total = daily_totals[unique_day_key]
    date_obj = datetime.strptime(d, "%Y-%m-%d").date()
    is_subsidy_applicable = date_obj.weekday() not in (5, 6)
    
    if not is_subsidy_applicable:
        final_bill = gross_total
    else:
        final_bill = max(0.0, gross_total - subsidy)
        
    if unique_day_key not in processed_days:
        employee_final_totals[emp] += final_bill
        processed_days.add(unique_day_key)

# --- RULE 4: Apply ₹2,500 Monthly Maximum Cap ---
for emp in employee_final_totals:
    if employee_final_totals[emp] > MONTHLY_MAX:
        employee_final_totals[emp] = MONTHLY_MAX

# Final rounded totals
totalprice1 = round(employee_final_totals["E101"], 0)
totalprice2 = round(employee_final_totals["E102"], 0)
totalprice3 = round(employee_final_totals["E103"], 0)
total = totalprice1 + totalprice2 + totalprice3

print(f" E101: {totalprice1:.0f}")
print(f" E102: {totalprice2:.0f}")
print(f" E103: {totalprice3:.0f}")
print(f"Total: {total:.0f}")
