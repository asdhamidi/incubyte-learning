import duckdb
import numpy

def pretty_print(heading, data):
    if heading:
        print("-"*25 + heading + "-"*25)

    print(data)

    if heading:
        print("-"*75)

# raw_orders, stg_orders, int_valid_orders, daily_revenue
con = duckdb.connect("incident.duckdb")
pretty_print("daily_revenue", data=con.execute(query="SELECT * FROM daily_revenue").df())

pretty_print("int_valid_orders", data=con.execute(query="SELECT * FROM int_valid_orders").df())
pretty_print("int_valid_orders_date_count", data=con.execute(query="SELECT count(*), order_date FROM int_valid_orders group by 2").df())
pretty_print("stg_orders_date_count", data=con.execute(query="SELECT count(*), order_date FROM stg_orders group by 2").df())
pretty_print("stg_orders_status_count", data=con.execute(query="SELECT count(*), status FROM stg_orders group by 2").df())
pretty_print("stg_orders_date_status_count", data=con.execute(query="SELECT count(*), order_date, status FROM stg_orders group by 2,3 order by 2,3").df())
print("76 orders on 2026-10-27 had status marked to \"complete\" instead of \"completed\", hence the drop.")
print("Finding the problematic orders")
pretty_print("stg_orders_date_complete_status", data=con.execute(query="SELECT count(*) FROM stg_orders where status = 'complete'").df())
pretty_print("stg_orders_date_complete_status_count", data=con.execute(query="SELECT channel, sum(amount) FROM stg_orders where status = 'complete' group by 1").df())
pretty_print("stg_orders_date_invalid_orders", data=con.execute(query="SELECT distinct order_id FROM stg_orders where status = 'complete'").df())
