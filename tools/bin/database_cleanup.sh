#!/bin/bash
# clean up test records from the book_service database
# created by the test_books/test_docker_api.py script and generated cUrl commands
# from test_books/generate_curl_commands.py

UN=scott
DBHOST=192.168.1.90

echo "Running cleanup script..."
mysql -vu $UN -p -h $DBHOST books < ./book_service/test_books/sql_cleanup_script.sql
echo "Done."
