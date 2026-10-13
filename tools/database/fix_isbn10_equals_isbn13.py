#!/usr/bin/env python3
"""
One-off repair: books added via ISBN lookup stored the ISBN-13 in IsbnNumber
(isbndb's "isbn" field often holds the 13-digit form). For rows where
IsbnNumber == IsbnNumber13, set IsbnNumber to the derived ISBN-10, or NULL when
there is none (979 prefix / not a valid 13-digit value).

Usage (from tools/ directory):
    BOOKDB_CONFIG=book_service/config/configuration.json \
        poetry run python database/fix_isbn10_equals_isbn13.py           # dry run
    poetry run python database/fix_isbn10_equals_isbn13.py --apply   # write changes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

import psycopg2
from booksdb.config import books_conf
from books.isbn_com import Endpoint


def main():
    parser = argparse.ArgumentParser(description="Repair IsbnNumber values that duplicate IsbnNumber13.")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is a dry run)")
    args = parser.parse_args()

    db = psycopg2.connect(**books_conf)
    try:
        with db.cursor() as c:
            c.execute("SELECT BookId, Title, IsbnNumber FROM books "
                      "WHERE IsbnNumber = IsbnNumber13 AND length(IsbnNumber) = 13 ORDER BY BookId")
            rows = c.fetchall()
            if args.apply:
                # Data repair, not a user edit: keep trg_books_update from bumping LastUpdate,
                # which would flood "recently edited". DDL is transactional, so a failure re-enables it.
                c.execute("ALTER TABLE books DISABLE TRIGGER trg_books_update")
            for book_id, title, isbn in rows:
                isbn10 = Endpoint.isbn13_to_isbn10(isbn)
                print(f"{book_id:>6}  {isbn} -> {isbn10 or 'NULL':<10}  {title[:60]}")
                if args.apply:
                    c.execute("UPDATE books SET IsbnNumber = %s WHERE BookId = %s", (isbn10, book_id))
            if args.apply:
                c.execute("ALTER TABLE books ENABLE TRIGGER trg_books_update")
        if args.apply:
            db.commit()
            print(f"Updated {len(rows)} rows.")
        else:
            print(f"Dry run: {len(rows)} rows would be updated. Re-run with --apply to write.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
