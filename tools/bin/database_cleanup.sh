#!/bin/bash
# clean up test records from the book_service database
# created by the test_books/test_docker_api.py script and generated cUrl commands
# from test_books/generate_curl_commands.py
#
# `make clean-test-records` runs test_books/clean_test_records.py instead of this
# script; this is kept for manual/ad-hoc cleanup against PostgreSQL.

UN=scott
DBHOST=192.168.1.90
DBPORT=5434
DB=book-collection

echo "Running cleanup script..."
psql -U $UN -h $DBHOST -p $DBPORT -d $DB -f ./book_service/test_books/sql_cleanup_script.sql
echo "Done."
