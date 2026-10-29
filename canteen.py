import csv
from datetime import date
from turtle import pd
with open('orders_sample.csv',mode='r', newline='', encoding='utf-8') as file:
    reader=csv.reader(file)
    header = next(reader) 
    
    for row in reader:
        print(row)
        date = row[0]
    if date=="01-09-2026":
        totalprice=0
        totalprice = totalprice + (int(row['quantity']) * float(row['price']))
        print(f"Total Price for Order ID {row[0]}: {totalprice}")
