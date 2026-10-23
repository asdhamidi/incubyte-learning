import duckdb

import pipeline


def main():
    con = duckdb.connect()
    print("UNION ALL vs UNION (row_count, total):", pipeline.union_counts(con))


if __name__ == "__main__":
    main()
