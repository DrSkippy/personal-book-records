"""ISBN Lookup Tools - Fetch book information from ISBN databases."""

from pprint import pprint
import requests as req


class ISBNLookup:
    """
    ISBN Lookup Tool - Fetch book metadata by ISBN number.

    Queries external ISBN databases to retrieve book information including
    title, author, publisher, page count, and more.

    Attributes:
        result: The last lookup result (dict or dict of dicts for multiple ISBNs).

    Example:
        >>> isbn = ISBNLookup(config)
        >>> isbn.lookup("9780547928227")
        >>> isbn.lookup(["0060929480", "9780140449136"])  # Multiple ISBNs
    """

    def __init__(self, config):
        """
        Initialize the ISBN lookup tool.

        Args:
            config: Configuration dict with 'key' (API key) and 'url_isbn' (API URL template).
        """
        self.config = config
        self.result = None

    def lookup(self, isbn=None):
        """
        Look up book information by ISBN.

        Fetches and displays book metadata from the ISBN database.
        Supports both single ISBN and multiple ISBN lookups.

        Args:
            isbn: ISBN string (ISBN-10 or ISBN-13) or list of ISBN strings.

        Result:
            isbn.result contains the API response:
                - Single ISBN: dict with book data
                - Multiple ISBNs: dict mapping ISBN -> book data

        Example:
            >>> isbn.lookup("9780547928227")           # Single lookup
            >>> isbn.lookup("0060929480")              # ISBN-10 format
            >>> isbn.lookup(["978...", "978..."])      # Multiple books
        """
        _result = None
        if isinstance(isbn, list):
            _result = {}
            for _isbn in isbn:
                self._lookup(_isbn)
                _result[_isbn] = self.result
                a = input("Return to continue; q to quit...") if _isbn != isbn[-1] else ""
                if a.startswith("q"):
                    break
            self.result = _result
        elif isbn:
            self._lookup(isbn)

    def _lookup(self, isbn):
        """
        Internal method to perform a single ISBN lookup.

        Args:
            isbn: Single ISBN string to look up.
        """
        headers = {'Authorization': self.config["key"]}
        url = self.config["url_isbn"].format(isbn)
        resp = req.get(url, headers=headers)
        pprint(resp.json(), indent=3)
        self.result = resp.json()
