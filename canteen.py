import csv
import math

totalprice1 = 0
totalprice2 = 0
totalprice3 = 0
subsidy = 60

with open('orders_sample.csv', mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader)  
    for row in reader:
        if len(row) < 5:
            print(f"incomplete row data: {row}")
            continue
            
        product_id = row[1]
        employee_id = row[2]
        if product_id in ["E101", "E102", "E103"]:
            try:
                quantity = float(row[3])
                price = float(row[4])
                
                if quantity > 5:
                    discounted_quantity = quantity - 5
                    row_total = (5 * price) + (discounted_quantity * price * 0.90)
                elif quantity <0:
                    print(f"invalid quantity in row: {row}")
                    continue
                else:
                    row_total = quantity * price
                
                
                if product_id == "E101":
                    totalprice1 += row_total
                elif product_id == "E102":
                    totalprice2 += row_total
                elif product_id == "E103":
                    totalprice3 += row_total
                    
            except ValueError:
                # Safely handle headers or corrupted rows that aren't numbers
                print(f"invalid numeric data in row: {row}")
        else:
            print(f"row with unrecognized product ID: {row}")

totalprice1 = round(max(0, totalprice1 - subsidy), 0)
totalprice2 = round(max(0, totalprice2 - subsidy), 0)
totalprice3 = round(max(0, totalprice3 - subsidy), 0)
total=totalprice1 + totalprice2 + totalprice3

# Print final results
print(f" E101: {totalprice1:.2f}")
print(f" E102 : {totalprice2:.2f}")
print(f" E103: {totalprice3:.2f}")
print(f"Total: {total:.2f}")
