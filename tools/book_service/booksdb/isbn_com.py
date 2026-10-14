import datetime
import re
import time

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

    RETRY_STATUS = 429  # isbndb's per-second rate limit
    RETRY_DELAYS = (1.0, 2.0)

    def _get(self, url, params=None):
        """GET with the API key, retrying on isbndb's rate limit. Returns the Response."""
        headers = {'Authorization': self.config.get("key")}
        for delay in self.RETRY_DELAYS + (None,):
            response = requests.get(url, headers=headers, params=params, timeout=20)
            if response.status_code != self.RETRY_STATUS or delay is None:
                return response
            time.sleep(delay)

    def _base_url(self):
        return self.config.get("url_isbn").rsplit("/book/", 1)[0]

    def get_book_by_isbn(self, isbn=None):
        try:
            response = self._get(self.config.get("url_isbn").format(isbn))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            return {
                'error': error_message
            }

    def _book_list(self, path, params, key="books"):
        """Raw isbndb book dicts from a list endpoint, [] when nothing matches (isbndb
        answers 404), or {'error': ...} on a request failure."""
        try:
            response = self._get(f"{self._base_url()}{path}", params=params)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json().get(key) or []
        except (requests.exceptions.RequestException, ValueError) as e:
            return {'error': str(e)}

    def search_books_by_title(self, title, page_size=20):
        """GET /books/{title}?column=title"""
        return self._book_list(f"/books/{title}", {"page": 1, "pageSize": page_size, "column": "title"})

    def search_books_by_text(self, text, page_size=20):
        """GET /books/{text} across all columns (title, author, ...)"""
        return self._book_list(f"/books/{text}", {"page": 1, "pageSize": page_size})

    def search_books(self, text, author=None, page_size=20):
        """GET /search/books?text=&author= -- isbndb's ranked search; the best match for a
        title plus author."""
        params = {"text": text, "page": 1, "pageSize": page_size}
        if author:
            params["author"] = author
        return self._book_list("/search/books", params, key="data")

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
    def binding_to_cover_type(binding):
        """Map an isbndb binding ("Hardcover", "Mass Market Paperback", "Kindle Edition", ...)
        to a collection CoverType (Hard/Soft/Digital), or "" when it doesn't say."""
        b = str(binding or "").lower()
        if any(k in b for k in ("kindle", "ebook", "e-book", "digital", "epub", "nook")):
            return "Digital"
        if any(k in b for k in ("hardcover", "hardback", "hard cover", "library binding")):
            return "Hard"
        if any(k in b for k in ("paperback", "softcover", "soft cover", "mass market", "trade")):
            return "Soft"
        return ""

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
        proto["CoverType"] = self.binding_to_cover_type(book.get("binding"))
        return proto
