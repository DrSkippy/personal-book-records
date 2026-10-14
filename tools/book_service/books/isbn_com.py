# Moved to booksdb.isbn_com so the MCP server image (which copies booksdb/ but
# not books/) can use the isbndb lookup too. Re-exported here for existing imports.
from booksdb.isbn_com import Endpoint

__all__ = ["Endpoint"]
