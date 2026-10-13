import datetime
import re

import requests


class Endpoint:
    COLLECTION_DB_DICT = {
        "Title": "",
        "Author": "",
        "CopyrightDate": "2000-01-01",
        "IsbnNumber": "",
        "IsbnNumber13": "",
        "PublisherName": "",
        "CoverType": "Digital, Hard, Soft",
        "Pages": 0,
        "Location": "Main Collection, DOWNLOAD, Oversized, Pets, Woodwork, Reference, Birding",
        "BookNote": "",
        "Recycled": "0=No or 1=Yes"
    }

    def __init__(self, conf):
        self.config = conf

    def get_book_by_isbn(self, isbn=None):
        url = self.config.get("url_isbn").format(isbn)
        headers = {'Authorization': self.config.get("key")}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            return {
                'error': error_message
            }

    def get_books_by_isbn_list(self, isbn_list=[]):
        result = {}
        for isbn in isbn_list:
            try:
                result[isbn] = self.get_book_by_isbn(isbn)
            except Exception as e:
                result[isbn] = {'error': str(e)}
        return result

    @staticmethod
    def _normalize_published_date(value):
        """Return a Postgres-safe YYYY-MM-DD string, or None if the value is missing or unusable."""
        if not value:
            return None
        m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", str(value).strip())
        if not m:
            return None
        year, month, day = m.group(1), m.group(2) or "01", m.group(3) or "01"
        try:
            return datetime.date(int(year), int(month), int(day)).isoformat()
        except ValueError:
            return None

    @staticmethod
    def isbn13_to_isbn10(isbn13):
        """Return the ISBN-10 for a 978-prefixed ISBN-13, or None (979 prefixes have no ISBN-10)."""
        digits = re.sub(r"[^0-9]", "", str(isbn13 or ""))
        if len(digits) != 13 or not digits.startswith("978"):
            return None
        core = digits[3:12]
        check = (11 - sum((10 - i) * int(d) for i, d in enumerate(core)) % 11) % 11
        return core + ("X" if check == 10 else str(check))

    @classmethod
    def _isbn10_from_book(cls, book):
        """isbndb's "isbn" field often holds the ISBN-13, so only trust a 10-character value."""
        for candidate in (book.get("isbn10"), book.get("isbn")):
            if candidate and len(str(candidate).strip()) == 10:
                return str(candidate).strip()
        return cls.isbn13_to_isbn10(book.get("isbn13") or book.get("isbn")) or ""

    def _endpoint_to_collection_db(self, isbn_dict):
        """Convert an isbndb response into a collection record, or None if it holds no usable book."""
        book = isbn_dict.get("book") if isinstance(isbn_dict, dict) else None
        if not book or not book.get("title"):
            return None
        proto = self.COLLECTION_DB_DICT.copy()
        proto["Title"] = book["title"]
        authors = book.get("authors") or []
        proto["Author"] = authors[0] if authors else ""
        proto["IsbnNumber"] = self._isbn10_from_book(book)
        proto["IsbnNumber13"] = book.get("isbn13") or ""
        proto["PublisherName"] = book.get("publisher") or "unknown"
        proto["Pages"] = book.get("pages") or None
        proto["CopyrightDate"] = self._normalize_published_date(book.get("date_published"))
        return proto
