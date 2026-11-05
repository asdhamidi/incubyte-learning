"""Daily sales report.

Loads sales_raw.csv into DuckDB, removes unusable rows, converts amounts with fixed
rates and writes the top products for REPORT_DATE to top_products.csv.
"""

import csv
import sys

import duckdb

DB_PATH = ":memory:"
INPUT = "sales_raw.csv"
OUTPUT = "top_products.csv"
TOP_N = 10  # number of products written. FIXME: the old docs said 5; confirm with the report's readers
MIN_ORDER_VALUE = (
    5.0  # orders below this are dropped. FIXME: an old comment said 10; confirm
)
REPORT_DATE = (
    "2026-11-03"  # fixed date. FIXME: a nightly run should use yesterday (UTC)
)

# multipliers per currency, fixed per quarter by finance (FIN-88). USD is 1.00, so converted
# amounts are in USD. The quarter these rates belong to is not recorded here.
RATES = {"USD": 1.00, "EUR": 1.08, "GBP": 1.27}


def send_alert(message):
    print(f"ALERT: {message}")


def load(con):
    # remove exact duplicate rows (the source can redeliver an order); no other cleaning here
    con.execute(
        f"CREATE OR REPLACE TABLE sales AS SELECT DISTINCT * FROM read_csv_auto('{INPUT}')"
    )


def clean(con):
    # drop cancelled or refunded orders
    con.execute("DELETE FROM sales WHERE status IN ('cancelled', 'refunded')")
    # free samples have no amount, so drop them
    con.execute("DELETE FROM sales WHERE amount IS NULL")
    # drop orders below the minimum value; this also removes negative amounts
    con.execute("DELETE FROM sales WHERE amount < ?", [MIN_ORDER_VALUE])


def convert(con):
    # multiply each amount by its currency rate from RATES, which gives USD
    case = " ".join(
        f"WHEN currency = '{c}' THEN amount * {r}" for c, r in RATES.items()
    )
    con.execute("ALTER TABLE sales ADD COLUMN amount_converted DOUBLE")
    con.execute(f"UPDATE sales SET amount_converted = CASE {case} END")


def report(con):
    # only orders on REPORT_DATE; the end of the day is exclusive
    sql = f"""
        SELECT product_id, SUM(amount_converted) AS revenue, SUM(units) AS units
        FROM sales
        WHERE order_ts >= TIMESTAMP '{REPORT_DATE} 00:00:00'
          AND order_ts <  TIMESTAMP '{REPORT_DATE} 00:00:00' + INTERVAL 1 DAY
        GROUP BY product_id
        ORDER BY units DESC  -- ranked by units sold. FIXME: the old docs said revenue
        LIMIT {TOP_N}
    """
    return con.execute(sql).fetchall()


def write(rows):
    # write a semicolon-separated file. FIXME: confirm the reader expects ';' (the name says csv)
    n = 0
    with open(OUTPUT, "w", newline="") as f:
        out = csv.writer(f, delimiter=";")
        out.writerow(["product_id", "revenue", "units"])
        for row in rows:
            out.writerow(row)
            n += 1
    return n


def main():
    con = duckdb.connect(DB_PATH)
    # try loading twice; there is no wait between attempts. FIXME: the old comment said 3 tries
    for attempt in range(2):
        try:
            load(con)
            break
        except duckdb.IOException:
            print(f"input missing, attempt {attempt + 1}")
    else:
        send_alert("input file missing")
        sys.exit(1)

    clean(con)
    convert(con)
    rows = report(con)
    if not rows:
        # an empty report exits with code 0, so the scheduler sees success and no alert is sent.
        # FIXME: decide whether an empty day is an error, and if so call send_alert and exit non-zero
        print("no rows to report")
        sys.exit(0)

    written = write(rows)
    print(f"wrote {written} products")


if __name__ == "__main__":
    main()
