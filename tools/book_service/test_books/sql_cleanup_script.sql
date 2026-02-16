-- This script removes test data entries from various tables in the database.
-- Run via: make clean-test-records
USE book_collection;
DELETE FROM tag_labels WHERE label="delete_me";
DELETE FROM tag_labels WHERE label="deleteme";
DELETE FROM images WHERE Name LIKE "test_%";
DELETE FROM images WHERE Name LIKE "custom_test%";
DELETE FROM books WHERE PublisherName="Printerman";
DELETE FROM books_read WHERE ReadDate="1945-10-19";
DELETE FROM complete_date_estimates WHERE LastReadablePage=15000;
