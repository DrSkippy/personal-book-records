"""Remove test records from the book_collection database.

This script connects to the database using the project's configuration
and deletes all records created by the test suite (test_docker_api.py).
"""
import sys
import os

# Ensure booksdb package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pymysql
from booksdb.config import books_conf

CLEANUP_QUERIES = [
    ("tag_labels (deleteme)", "DELETE FROM tag_labels WHERE label = 'deleteme'"),
    ("tag_labels (delete_me)", "DELETE FROM tag_labels WHERE label = 'delete_me'"),
    ("images (test_%)", "DELETE FROM images WHERE Name LIKE 'test_%'"),
    ("images (custom_test%)", "DELETE FROM images WHERE Name LIKE 'custom_test%'"),
    ("books (Printerman)", "DELETE FROM books WHERE PublisherName = 'Printerman'"),
    ("books_read (1945-10-19)", "DELETE FROM books_read WHERE ReadDate = '1945-10-19'"),
    ("complete_date_estimates (15000)", "DELETE FROM complete_date_estimates WHERE LastReadablePage = 15000"),
]


def main() -> None:
    conn = pymysql.connect(**books_conf)
    try:
        with conn.cursor() as cursor:
            total = 0
            for label, sql in CLEANUP_QUERIES:
                cursor.execute(sql)
                count = cursor.rowcount
                total += count
                if count > 0:
                    print(f"  Deleted {count} row(s) from {label}")
            conn.commit()
        if total == 0:
            print("  No test records found.")
        else:
            print(f"  Total: {total} test record(s) removed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
