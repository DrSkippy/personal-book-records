#!/usr/bin/env python3
"""
Fresh database setup for book-collection.

Creates the complete current-state schema from scratch — all tables, triggers,
indexes, and the pgvector embeddings table. Idempotent: safe to run against an
existing database (uses IF NOT EXISTS / CREATE OR REPLACE throughout).

Usage (from tools/ directory):
    poetry run python database/setup_db.py

Prerequisites:
  1. The database must already exist. Create it as a superuser if needed:
         createdb -U postgres -p <port> book-collection
  2. pgvector must be enabled in the database. A superuser must run:
         psql -U postgres -p <port> -d book-collection \\
             -c "CREATE EXTENSION IF NOT EXISTS vector;"
     This script will check and print the exact command if it is missing.
  3. configuration.json must be present with valid connection details.
     See tools/book_service/config/configuration_example.json for the format.

After setup, run the indexing script to populate embeddings for existing notes:
    poetry run python database/index_notes.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

import psycopg2
from booksdb.config import books_conf

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'schema_current.sql')

EXPECTED_TABLES = {
    'books',
    'books_read',
    'books_tags',
    'tag_labels',
    'complete_date_estimates',
    'daily_page_records',
    'images',
    'book_note_embeddings',
}


def main():
    host = books_conf['host']
    port = books_conf['port']
    dbname = books_conf['dbname']

    print(f"Connecting to {host}:{port} database={dbname} ...")

    try:
        db = psycopg2.connect(**books_conf)
    except psycopg2.OperationalError as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    db.autocommit = True

    # Check pgvector extension
    with db.cursor() as c:
        c.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        row = c.fetchone()

    if not row:
        print()
        print("ERROR: pgvector extension is not enabled in this database.")
        print("A PostgreSQL superuser must run the following command first:")
        print()
        print(f'    psql -U postgres -p {port} -d "{dbname}" -c "CREATE EXTENSION IF NOT EXISTS vector;"')
        print()
        sys.exit(1)

    print(f"pgvector {row[0]}: OK")

    # Apply schema
    print("Applying schema_current.sql ...")
    schema_sql = open(SCHEMA_FILE).read()

    # Strip the CREATE EXTENSION line — already confirmed present above
    lines = [l for l in schema_sql.splitlines() if not l.strip().startswith('CREATE EXTENSION')]
    schema_sql = '\n'.join(lines)

    with db.cursor() as c:
        c.execute(schema_sql)

    # Verify tables
    with db.cursor() as c:
        c.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        present = {r[0] for r in c.fetchall()}

    missing = EXPECTED_TABLES - present
    if missing:
        print(f"WARNING: expected tables not found: {', '.join(sorted(missing))}")
    else:
        print(f"Tables: {', '.join(sorted(present & EXPECTED_TABLES))}")

    # Verify indexes on embeddings table
    with db.cursor() as c:
        c.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'book_note_embeddings'"
        )
        indexes = [r[0] for r in c.fetchall()]
    print(f"Embedding indexes: {', '.join(indexes)}")

    db.close()
    print()
    print("Setup complete.")
    print()
    print("Next step — populate embeddings for existing notes:")
    print("    poetry run python database/index_notes.py")


if __name__ == '__main__':
    main()
