-- This script removes test data entries from various tables in the database.
-- `make clean-test-records` runs test_books/clean_test_records.py instead of this
-- file; kept for manual use via: psql -U <user> -h <host> -p 5434 -d book-collection < sql_cleanup_script.sql
DELETE FROM tag_labels WHERE label='delete_me';
DELETE FROM tag_labels WHERE label='deleteme';
DELETE FROM images WHERE Name LIKE 'test_%';
DELETE FROM images WHERE Name LIKE 'custom_test%';
DELETE FROM books WHERE PublisherName='Printerman';
DELETE FROM books_read WHERE ReadDate='1945-10-19';
DELETE FROM complete_date_estimates WHERE LastReadablePage=15000;
