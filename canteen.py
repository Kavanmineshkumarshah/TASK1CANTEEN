import csv
from collections import defaultdict
from datetime import datetime

totalprice1 = 0
totalprice2 = 0
totalprice3 = 0
subsidy = 60

valid_rows = []
daily_totals = defaultdict(float)
employee_final_totals = defaultdict(float)

with open('orders_sample.csv', mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader)  
    for row in reader:
        if len(row) < 5:
            print(f"incomplete row data: {row}")
            continue
            
        date_str = row[0].strip()
        product_id = row[1].strip()
        employee_id = row[2].strip()
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"invalid date error: {date_str} in row data")
            continue
            
        if product_id in ["E101", "E102", "E103"]:
            try:
                quantity = float(row[3].strip())
                price = float(row[4].strip())
                
                if quantity >= 5:
                    row_total = quantity * price * 0.90
                elif quantity < 0:
                    print(f"invalid quantity in row: {row}")
                    continue
                elif quantity < 5:
                    row_total = quantity * price
                
                valid_rows.append({
                    'date': date_str,
                    'employee_id': product_id,
                    'item': employee_id,
                    'quantity': quantity,
                    'price': price,
                    'row_total': row_total
                })
                
                group_key = (date_str, product_id)
                daily_totals[group_key] += row_total
                    
            except ValueError:
                print(f"invalid numeric data in row: {row}")
        else:
            print(f"row with unrecognized product ID: {row}")

processed_days = set()

for item_row in valid_rows:
    d = item_row['date']
    emp = item_row['employee_id']
    unique_day_key = (d, emp)
    
    gross_total = daily_totals[unique_day_key]
    is_subsidy_applicable = True
    
    date_obj = datetime.strptime(d, "%Y-%m-%d").date()
    if date_obj.weekday() in (5, 6):
        is_subsidy_applicable = False

    if not is_subsidy_applicable:
        final_bill = gross_total
    else:
        if gross_total < subsidy:
            final_bill = 0.0
        else:
            final_bill = gross_total - subsidy
            
    if unique_day_key not in processed_days:
        employee_final_totals[emp] += final_bill
        processed_days.add(unique_day_key)

totalprice1 = round(employee_final_totals["E101"], 0)
totalprice2 = round(employee_final_totals["E102"], 0)
totalprice3 = round(employee_final_totals["E103"], 0)
total = totalprice1 + totalprice2 + totalprice3

print(f" E101: {totalprice1:.2f}")
print(f" E102 : {totalprice2:.2f}")
print(f" E103: {totalprice3:.2f}")
print(f"Total: {total:.2f}")
