#!/usr/bin/env python3
"""
Fix Article Titles Utility

Moves articles (A, An, The) from the end of book titles to the beginning.

Examples:
    "Hobbit, The" -> "The Hobbit"
    "Cat in the Hat, The" -> "The Cat in the Hat"
    "Apple a Day, An" -> "An Apple a Day"

Usage:
    python bin/fix_article_titles.py --dry-run
    python bin/fix_article_titles.py --verbose
    python bin/fix_article_titles.py --limit 10
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    print("Error: pymysql not installed. Run: poetry install")
    sys.exit(1)


class TitleFixer:
    """Fix book titles by moving articles from end to beginning."""

    # Articles to look for at the end of titles
    ARTICLES = ['The', 'A', 'An']

    def __init__(self, config_path, dry_run=False, verbose=False, limit=None):
        """
        Initialize the title fixer.

        Args:
            config_path: Path to configuration.json
            dry_run: If True, don't commit changes to database
            verbose: If True, show all changes
            limit: Maximum number of titles to fix (None = no limit)
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.limit = limit
        self.config = self._load_config(config_path)
        self.connection = None

        # Statistics
        self.stats = {
            'total_scanned': 0,
            'needs_fixing': 0,
            'fixed': 0,
            'errors': 0
        }

    def _load_config(self, config_path):
        """Load database configuration."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {config_path}")
            print("Create it from: book_service/config/configuration_example.json")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def connect(self):
        """Connect to the database."""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config.get('port', 3306),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"Connected to database: {self.config['database']} at {self.config['host']}")
        except KeyError as e:
            print(f"Error: Missing configuration key: {e}")
            sys.exit(1)
        except pymysql.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("\nDisconnected from database")

    def needs_fixing(self, title):
        """
        Check if a title needs fixing.

        Returns:
            tuple: (needs_fixing: bool, article: str or None)
        """
        if not title:
            return False, None

        # Check for each article at the end
        for article in self.ARTICLES:
            # Pattern: ends with ", Article" (case insensitive at end)
            pattern = re.compile(rf',\s*{re.escape(article)}$', re.IGNORECASE)
            if pattern.search(title):
                return True, article

        return False, None

    def fix_title(self, title):
        """
        Fix a title by moving the article to the front.

        Args:
            title: Original title

        Returns:
            str: Fixed title, or None if no fix needed
        """
        needs_fix, article = self.needs_fixing(title)

        if not needs_fix:
            return None

        # Remove the article and comma from the end
        pattern = re.compile(rf',\s*{re.escape(article)}$', re.IGNORECASE)
        title_without_article = pattern.sub('', title).strip()

        # Add article to the front
        fixed_title = f"{article} {title_without_article}"

        return fixed_title

    def get_books_to_fix(self):
        """
        Query database for books that need fixing.

        Returns:
            list: List of dict with BookId and Title
        """
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT BookId, Title, Author
                    FROM books
                    ORDER BY Title
                """
                cursor.execute(sql)
                all_books = cursor.fetchall()

                # Filter books that need fixing
                books_to_fix = []
                for book in all_books:
                    self.stats['total_scanned'] += 1

                    if self.needs_fixing(book['Title'])[0]:
                        books_to_fix.append(book)
                        self.stats['needs_fixing'] += 1

                        # Apply limit if specified
                        if self.limit and len(books_to_fix) >= self.limit:
                            break

                return books_to_fix

        except pymysql.Error as e:
            print(f"Error querying database: {e}")
            return []

    def update_title(self, book_id, new_title):
        """
        Update a book's title in the database.

        Args:
            book_id: BookId
            new_title: New title to set

        Returns:
            bool: True if successful, False otherwise
        """
        if self.dry_run:
            return True  # Pretend success in dry-run mode

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    UPDATE books
                    SET Title = %s
                    WHERE BookId = %s
                """
                cursor.execute(sql, (new_title, book_id))
                self.connection.commit()
                return True

        except pymysql.Error as e:
            print(f"Error updating book {book_id}: {e}")
            self.stats['errors'] += 1
            return False

    def fix_all_titles(self):
        """Main function to fix all titles that need fixing."""
        print("=" * 80)
        print("BOOK TITLE ARTICLE FIXER")
        print("=" * 80)

        if self.dry_run:
            print("*** DRY RUN MODE - No changes will be made to the database ***")

        if self.limit:
            print(f"Limiting to {self.limit} fixes")

        print()

        # Get books that need fixing
        print("Scanning database for titles that need fixing...")
        books_to_fix = self.get_books_to_fix()

        print(f"\nScanned {self.stats['total_scanned']} books")
        print(f"Found {self.stats['needs_fixing']} titles that need fixing")

        if not books_to_fix:
            print("\nNo titles need fixing!")
            return

        # Process each book
        print("\n" + "=" * 80)
        print("CHANGES:")
        print("=" * 80 + "\n")

        for book in books_to_fix:
            book_id = book['BookId']
            old_title = book['Title']
            author = book['Author']
            new_title = self.fix_title(old_title)

            if new_title:
                # Show the change
                if self.verbose:
                    print(f"ID: {book_id}")
                    print(f"Author: {author}")
                    print(f"  OLD: {old_title}")
                    print(f"  NEW: {new_title}")
                    print()
                else:
                    print(f"{old_title:60s} -> {new_title}")

                # Update in database
                if self.update_title(book_id, new_title):
                    self.stats['fixed'] += 1

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total books scanned:  {self.stats['total_scanned']}")
        print(f"Titles needing fix:   {self.stats['needs_fixing']}")
        print(f"Titles fixed:         {self.stats['fixed']}")
        print(f"Errors:               {self.stats['errors']}")

        if self.dry_run:
            print("\n*** DRY RUN - No actual changes were made ***")
        else:
            print(f"\n✓ Successfully updated {self.stats['fixed']} titles in the database")

        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fix book titles by moving articles from end to beginning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview changes without modifying database
    python bin/fix_article_titles.py --dry-run

    # Fix all titles with verbose output
    python bin/fix_article_titles.py --verbose

    # Fix only first 10 titles
    python bin/fix_article_titles.py --limit 10 --dry-run

    # Actually apply fixes
    python bin/fix_article_titles.py
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information for each change'
    )

    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit to fixing N titles'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='book_service/config/configuration.json',
        help='Path to configuration.json (default: book_service/config/configuration.json)'
    )

    args = parser.parse_args()

    # Initialize fixer
    fixer = TitleFixer(
        config_path=args.config,
        dry_run=args.dry_run,
        verbose=args.verbose,
        limit=args.limit
    )

    try:
        # Connect to database
        fixer.connect()

        # Fix titles
        fixer.fix_all_titles()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    finally:
        # Always disconnect
        fixer.disconnect()


if __name__ == '__main__':
    main()
