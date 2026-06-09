#!/usr/bin/env python3
"""
Batch indexing script: generate and store pgvector embeddings for book/read notes.

Usage (from tools/ directory):
    poetry run python database/index_notes.py            # skip already-indexed rows
    poetry run python database/index_notes.py --rebuild  # re-embed everything
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

import psycopg2
from booksdb.config import books_conf, EMBED_HOST, EMBED_MODEL
from booksdb.api_util import upsert_book_note_embedding, upsert_read_note_embedding


def main():
    parser = argparse.ArgumentParser(description="Index book and read notes into pgvector.")
    parser.add_argument("--rebuild", action="store_true", help="Re-embed already-indexed rows")
    args = parser.parse_args()

    if not EMBED_HOST or not EMBED_MODEL:
        print("ERROR: embed_host and embed_model must be set in configuration.json ai_agent section")
        sys.exit(1)

    db = psycopg2.connect(**books_conf)

    skip_book = "" if args.rebuild else """
        AND NOT EXISTS (
            SELECT 1 FROM book_note_embeddings e
            WHERE e.bookid = b.BookId AND e.source = 'book_note'
        )"""

    skip_read = "" if args.rebuild else """
        AND NOT EXISTS (
            SELECT 1 FROM book_note_embeddings e
            WHERE e.bookid = r.BookId AND e.read_date = r.ReadDate AND e.source = 'read_note'
        )"""

    with db.cursor() as c:
        c.execute(
            f"SELECT BookId, BookNote FROM books "
            f"WHERE BookNote IS NOT NULL AND TRIM(BookNote) != ''{skip_book}"
        )
        book_rows = c.fetchall()

    print(f"Indexing {len(book_rows)} book notes...")
    for i, (book_id, note) in enumerate(book_rows, 1):
        print(f"  [{i}/{len(book_rows)}] book_note BookId={book_id}")
        edb = psycopg2.connect(**books_conf)
        try:
            upsert_book_note_embedding(edb, book_id, note.strip())
        finally:
            edb.close()

    with db.cursor() as c:
        c.execute(
            f"SELECT BookId, ReadDate, ReadNote FROM books_read "
            f"WHERE ReadNote IS NOT NULL AND TRIM(ReadNote) != ''{skip_read}"
        )
        read_rows = c.fetchall()

    print(f"Indexing {len(read_rows)} read notes...")
    for i, (book_id, read_date, note) in enumerate(read_rows, 1):
        print(f"  [{i}/{len(read_rows)}] read_note BookId={book_id} ReadDate={read_date}")
        edb = psycopg2.connect(**books_conf)
        try:
            upsert_read_note_embedding(edb, book_id, str(read_date), note.strip())
        finally:
            edb.close()

    db.close()
    print("Done.")


if __name__ == "__main__":
    main()
