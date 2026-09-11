#!/usr/bin/env bash
# Backup the book_service database (PostgreSQL)
# Run from tools directory

DT=$(date +%Y-%m-%d_%H%M)
DEST=/mnt/raid1/shares/backups
DEST=.
UN=$(cat ./book_service/config/configuration.json | jq -r .username)
DBPASS=$(cat ./book_service/config/configuration.json | jq -r .password)
DB=$(cat ./book_service/config/configuration.json | jq -r .database)
DBHOST=$(cat ./book_service/config/configuration.json | jq -r .host)
DBPORT=$(cat ./book_service/config/configuration.json | jq -r .port)
BOOKSDBDUMP=booksdb_$DT.sql

echo "****************************************"
echo " BOOKS BACKUP STARTING..."
echo
echo "Reading database $DB from host $DBHOST for user $UN."
echo "Results in $DEST/$BOOKSDBDUMP..."
#
if [ -d $DEST ];  then
  PGPASSWORD=$DBPASS pg_dump -h $DBHOST -p $DBPORT -U $UN $DB > $DEST/$BOOKSDBDUMP
  PGPASSWORD=$DBPASS pg_dump --schema-only -h $DBHOST -p $DBPORT -U $UN $DB > $DEST/schema_$BOOKSDBDUMP
  echo "Backups present:"
  ls -lhs $DEST/*.sql
  echo "Done."
  echo "****************************************"
else
  echo "Destination $DEST does not exist. No backups created. Aborting."
fi
