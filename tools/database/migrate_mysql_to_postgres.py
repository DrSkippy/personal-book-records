#!/usr/bin/env python3
"""
Migrate book_collection from MySQL to PostgreSQL.

Usage:
    python migrate_mysql_to_postgres.py <mysql_config.json> <pg_config.json>

Each config file must have keys: username, password, database, host, port
(same format as the app's configuration.json)
"""

import json
import sys

import pymysql
import psycopg2

# Tables in FK-safe insertion order
TABLES = [
    "books",
    "tag_labels",
    "books_read",
    "books_tags",
    "complete_date_estimates",
    "daily_page_records",
    "images",
]

# Tables with SERIAL (auto-increment) primary keys — sequences need resetting
SEQUENCES = [
    ("books",                   "bookid"),
    ("tag_labels",              "tagid"),
    ("complete_date_estimates", "recordid"),
    ("images",                  "imageid"),
]


def load_config(path):
    with open(path) as f:
        return json.load(f)


def mysql_connect(cfg):
    return pymysql.connect(
        user=cfg["username"],
        passwd=cfg["password"],
        db=cfg["database"],
        host=cfg["host"],
        port=int(cfg["port"]),
    )


def pg_connect(cfg):
    return psycopg2.connect(
        user=cfg["username"],
        password=cfg["password"],
        dbname=cfg["database"],
        host=cfg["host"],
        port=int(cfg["port"]),
    )


def fetch_table(mysql_cur, table):
    mysql_cur.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in mysql_cur.description]
    rows = mysql_cur.fetchall()
    return cols, rows


def insert_rows(pg_cur, table, cols, rows):
    if not rows:
        return 0
    col_list = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    query = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    pg_cur.executemany(query, rows)
    return len(rows)


def reset_sequences(pg_cur):
    for table, col in SEQUENCES:
        pg_cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
            f"COALESCE(MAX({col}), 1)) FROM {table}"
        )


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <mysql_config.json> <pg_config.json>")
        sys.exit(1)

    mysql_cfg = load_config(sys.argv[1])
    pg_cfg = load_config(sys.argv[2])

    print(f"Source (MySQL): {mysql_cfg['host']}:{mysql_cfg['port']}/{mysql_cfg['database']}")
    print(f"Target (Postgres): {pg_cfg['host']}:{pg_cfg['port']}/{pg_cfg['database']}")
    print()

    mysql = mysql_connect(mysql_cfg)
    pg = pg_connect(pg_cfg)

    mysql_cur = mysql.cursor()
    pg_cur = pg.cursor()

    print(f"{'Table':<35} {'MySQL rows':>12} {'PG rows':>10}")
    print("-" * 60)

    try:
        for table in TABLES:
            cols, rows = fetch_table(mysql_cur, table)
            insert_rows(pg_cur, table, cols, rows)

            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cur.fetchone()[0]
            print(f"{table:<35} {len(rows):>12} {pg_count:>10}")

        reset_sequences(pg_cur)
        pg.commit()
        print()
        print("Migration complete. Sequences reset.")

    except Exception as e:
        pg.rollback()
        print(f"\nError during migration: {e}", file=sys.stderr)
        raise
    finally:
        mysql_cur.close()
        mysql.close()
        pg_cur.close()
        pg.close()


if __name__ == "__main__":
    main()
