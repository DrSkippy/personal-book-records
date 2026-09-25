__version__ = '0.7.1'

import datetime
import logging
import pprint

pp = pprint.PrettyPrinter(indent=3)

import pandas as pd
import requests
from rich.console import Console
from rich.table import Table

# Rich console for output
console = Console()


class BCTool:
    """
    Book Collection Tool - Interface for searching, browsing, and managing books.

    This class provides methods to interact with the book collection database API,
    including searching for books, viewing details, managing tags, and tracking
    reading history.

    Attributes:
        result: Stores the result of the last operation (typically a DataFrame or ID).
        end_point: The API endpoint URL.

    Example:
        >>> bc = BCTool("http://localhost:8084", "your-api-key")
        >>> bc.bs(Title="hobbit")  # Search by title
        >>> bc.book(123)           # View book details
        >>> bc.bry(2024)           # Books read in 2024
    """

    COLUMN_INDEX = {
        "BookId": 0,
        "Title": 1,
        "Author": 2,
        "CopyrightDate": 3,
        "IsbnNumber": 4,
        "PublisherName": 5,
        "CoverType": 6,
        "Pages": 7,
        "BookNote": 8,
        "Recycled": 9,
        "Location": 10,
        "IsbnNumber13": 11,
        "ReadDate": 12
    }
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
    MINIMAL_BOOK_INDEXES = [0, 1, 2, 7, 8, 9, 10, 12]
    page_size = 35
    terminal_width = 180
    DIVIDER_WIDTH = 50

    # Column styling for rich tables
    COLUMN_STYLES = {
        "BookId": "cyan bold",
        "Title": "green",
        "Author": "yellow",
        "CopyrightDate": "dim",
        "IsbnNumber": "dim",
        "IsbnNumber13": "dim",
        "PublisherName": "dim",
        "CoverType": "magenta",
        "Pages": "blue bold",
        "BookNote": "white",
        "Recycled": "red",
        "Location": "cyan",
        "ReadDate": "green bold",
        "TagId": "cyan bold",
        "Tag": "yellow",
        "Label": "yellow",
        "Count": "blue bold",
        "year": "cyan bold",
        "books read": "green bold",
        "pages read": "blue bold",
    }

    def __init__(self, endpoint, api_key):
        # File path contortions so notebook uses the same config as REPL command line
        self.end_point = endpoint
        self.header = {"x-api-key": f"{api_key}"}
        self.result = None

    def _row_column_selector(self, row, indexes):
        return [row[i] for i in indexes]

    def _column_selector(self, data, indexes):
        return [self._row_column_selector(i, indexes) for i in data]

    def _build_table(self, headers, rows):
        table = Table(
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
            row_styles=["", "dim"],
            expand=False,
            width=min(self.terminal_width, 200),
        )
        for col_name in headers:
            style = self.COLUMN_STYLES.get(col_name, "white")
            table.add_column(col_name, style=style, overflow="fold")
        for row in rows:
            table.add_row(*row)
        return table

    def _rows_that_fit(self, headers, rows, max_lines):
        """
        Return how many of rows fit on one screen, counting the table's real
        rendered height (borders, header, and cells that fold onto several lines).
        Always returns at least 1 so a single oversized row still gets shown.
        """
        n = 1
        while n < len(rows):
            table = self._build_table(headers, rows[:n + 1])
            if len(console.render_lines(table, console.options, pad=False)) > max_lines:
                break
            n += 1
        return n

    def _show_table(self, data, header, indexes, pagination=True):
        self.terminal_width, terminal_height = console.size
        selected_headers = self._row_column_selector(header, indexes)

        try:
            rows = [[str(cell) if cell is not None else "" for cell in row]
                    for row in self._column_selector(data, indexes)]
        except TypeError:
            console.print("[red]No data[/red]")
            return

        # Leave one line for the "Return to continue" prompt
        max_lines = max(terminal_height - 1, 5)
        i = 0
        while i < len(rows):
            n = self._rows_that_fit(selected_headers, rows[i:], max_lines) if pagination else len(rows)
            self.page_size = n
            console.print(self._build_table(selected_headers, rows[i:i + n]))

            i += n
            if i < len(rows):
                a = input("Return to continue; q to quit...")
                if a.startswith("q"):
                    break

    def _populate_new_book_record(self):
        proto = self.COLLECTION_DB_DICT.copy()
        return self._inputer(proto)

    def _populate_add_read_date(self, book_collection_id, today=True):
        proto = {
            "BookId": book_collection_id,
            "ReadDate": datetime.date.today().strftime("%Y-%m-%d"),
            "ReadNote": ""
        }
        return self._inputer(proto, exclude_keys=["BookId"])

    def _inputer(self, proto, exclude_keys=[]):
        verified = False
        while not verified:
            for key in proto:
                if key in exclude_keys:
                    print(f"{key}: {proto[key]}")
                else:
                    a = input(f"{key} ({proto[key]}     'a' to accept): ")
                    a = a.strip()
                    if a != "a":
                        proto[key] = a
            print("*" * self.DIVIDER_WIDTH)
            pp.pprint(proto)
            a = input("'x' to try again, 'a' to accept: ")
            a = a.strip()
            if a == "a":
                verified = True
        return proto


    def _add_books(self, records):
        result_message = "Added."
        q = self.end_point + "/add_books"
        try:
            tr = requests.post(q, json=records, headers=self.header)
            tres = tr.json()
        except requests.RequestException as e:
            logging.error(e)
            result_message = {"errors": [str(e)]}
        else:
            # The API reports per-row DB failures as {"error": ...} inside a 200 response,
            # and non-row failures (e.g. bad API key) as a top-level {"error": ...}.
            book_collection_id_list = []
            errors = []
            if "add_books" not in tres:
                errors.append(tres.get("error", f"Unexpected response: {tres}"))
            for rec in tres.get("add_books", []):
                if "BookId" in rec:
                    book_collection_id_list.append(rec["BookId"])
                else:
                    errors.append(rec.get("error", f"Unexpected record: {rec}"))
            for e in errors:
                logging.error(e)
            self.result = book_collection_id_list
            if errors:
                result_message = {"errors": errors}
        return result_message

    def version(self):
        """
        Display version information for the API and REPL.

        Shows a formatted table with the API endpoint, API version, and REPL version.

        Alias: ver()

        Example:
            >>> bc.ver()
        """
        q = self.end_point + "/configuration"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            table = Table(
                show_header=False,
                border_style="blue",
                title="[bold magenta]Book Records and Reading Database[/bold magenta]",
                title_justify="center",
            )
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Endpoint", self.end_point)
            table.add_row("API Version", res["version"])
            table.add_row("REPL Version", __version__)
            console.print(table)

    ver = version

    def columns(self):
        """
        Display all searchable database column names.

        Lists the column names that can be used as search parameters in books_search().

        Alias: col()

        Example:
            >>> bc.col()
            BookId
            Title
            Author
            ...
        """
        print("\n".join(list(self.COLUMN_INDEX.keys())))

    col = columns

    def tag_counts(self, tag=None, pagination=True):
        """
        Display tag usage statistics showing how many books have each tag.

        Args:
            tag: Optional string to filter tags (partial match). If None, shows all tags.
            pagination: If True (default), paginate output to fit screen.

        Result:
            bc.result contains a DataFrame with tag names and counts.

        Alias: tc()

        Example:
            >>> bc.tc()              # Show all tag counts
            >>> bc.tc("sci")         # Show tags containing "sci"
        """
        q = self.end_point + "/tag_counts"
        if tag is not None:
            q += f"/{tag}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            self._show_table(res["data"], res["header"], [0, 1], pagination)
            self.result = pd.DataFrame(res['data'], columns=res["header"])

    tc = tag_counts

    def books_search(self, **query):
        """
        Search for books by any combination of column values.

        Args:
            **query: Keyword arguments where keys are column names and values are
                     search terms (partial match supported).

        Result:
            bc.result contains a DataFrame with matching books.

        Alias: bs()

        Available columns: BookId, Title, Author, CopyrightDate, IsbnNumber,
                          PublisherName, CoverType, Pages, BookNote, Recycled,
                          Location, IsbnNumber13, Tags

        Example:
            >>> bc.bs(Title="hobbit")                    # Search by title
            >>> bc.bs(Author="tolkien")                  # Search by author
            >>> bc.bs(Title="ring", Author="tolkien")    # Multiple criteria
            >>> bc.bs(Tags="fantasy")                    # Search by tag
        """
        q = self.end_point + "/books_search?"
        first = True
        for k, v in query.items():
            if first:
                first = False
            else:
                q += "&"
            q += f"{k}={v}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            self._show_table(res["data"], res["header"], self.MINIMAL_BOOK_INDEXES)
            self.result = pd.DataFrame(res['data'], columns=res["header"])

    bs = books_search

    def tags_search(self, match_str, pagination=True, output=True):
        """
        Search for books by tag name.

        Args:
            match_str: Tag name to search for (partial match supported).
            pagination: If True (default), paginate output to fit screen.
            output: If True (default), display results. Set False to only populate result.

        Result:
            bc.result contains a set of BookIds for books with matching tags.

        Alias: ts()

        Example:
            >>> bc.ts("fiction")         # Find books tagged with "fiction"
            >>> bc.ts("sci", output=False)  # Get IDs without display
        """
        q = self.end_point + f"/tags_search/{match_str}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            if output:
                self._show_table(res["data"], res["header"], [0, 1, 2], pagination)
            self.result = set([x[0] for x in res["data"]])

    ts = tags_search

    def book(self, book_collection_id, pagination=True):
        """
        Display complete details for a single book.

        Shows book metadata, associated tags, and reading history (dates read).

        Args:
            book_collection_id: The BookId of the book to retrieve (integer).
            pagination: If True (default), paginate output to fit screen.

        Result:
            bc.result contains the BookId.

        Example:
            >>> bc.book(1234)
            >>> bc.book(bc.result)  # View book from previous search
        """
        try:
            book_collection_id = int(book_collection_id)
        except ValueError:
            print("Requires in integer Book ID")
            return
        q = self.end_point + f"/complete_record/{book_collection_id}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            self._show_table(res["book"]["data"], res["book"]["header"], [0, 1, 2, 3, 4], pagination)
            if res["tags"]["data"] and len(res["tags"]["data"][0]) > 0:
                tags = res["tags"]["data"][0]
                console.print("\n[bold cyan]TAGS:[/bold cyan]")
                tag_text = "  ".join([f"[yellow]{tag}[/yellow]" for tag in tags])
                console.print(f"  {tag_text}\n")
            if res["reads"]["data"] and len(res["reads"]["data"][0]) > 0:
                console.print("[bold cyan]READ DATES:[/bold cyan]")
                self._show_table(res["reads"]["data"], res["reads"]["header"], [0, 1], pagination)
            self.result = book_collection_id

    def books_read_by_year_with_summary(self, year=None, pagination=True):
        """
        Display books read with yearly summary statistics inline.

        Shows all books read, grouped by year, with total books and pages
        displayed after each year's entries.

        Args:
            year: Optional 4-digit year to filter. If None, shows all years.
            pagination: If True (default), paginate output to fit screen.

        Result:
            bc.result contains a list of DataFrames, one per year.

        Alias: brys()

        Example:
            >>> bc.brys()        # All years with summaries
            >>> bc.brys(2024)    # Just 2024 with summary
        """
        self.result = []
        q = self.end_point + "/summary_books_read_by_year"
        if year is not None:
            q += f"/{year}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            _data = []
            for year, pages, books in res["data"]:
                q = self.end_point + f"/books_read/{year}"
                try:
                    tr = requests.get(q, headers=self.header)
                    tres = tr.json()
                except requests.RequestException as e:
                    logging.error(e)
                else:
                    _template = [" " for i in range(len(tres["data"][0]))]
                    _data.append(_template)
                    self.result.append(pd.DataFrame(tres['data'], columns=tres["header"]))
                    _data.extend(tres["data"])
                    _template = ["" for i in range(len(tres["data"][0]))]
                    _template[0] = f" **** {year} ****"
                    _template[1] = f"Books = {books}"
                    _template[2] = f"Pages = {pages}"
                    _data.append(_template)
            self._show_table(_data, tres["header"], self.MINIMAL_BOOK_INDEXES, pagination)

    brys = books_read_by_year_with_summary

    def books_read_by_year(self, year=None, pagination=True):
        """
        Display books read in a given year or all years.

        Args:
            year: Optional 4-digit year to filter. If None, shows all years.
            pagination: If True (default), paginate output to fit screen.

        Result:
            bc.result contains a DataFrame with all matching books.

        Alias: bry()

        Example:
            >>> bc.bry()         # All books ever read
            >>> bc.bry(2024)     # Books read in 2024
        """
        q = self.end_point + "/books_read"
        if year is not None:
            q += f"/{year}"
        try:
            tr = requests.get(q, headers=self.header)
            tres = tr.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            self._show_table(tres["data"], tres["header"], self.MINIMAL_BOOK_INDEXES, pagination)
            self.result = pd.DataFrame(tres['data'], columns=tres["header"])

    bry = books_read_by_year

    def summary_books_read_by_year(self, year=None, show=True, pagination=True):
        """
        Display yearly reading statistics (books count and pages count per year).

        Args:
            year: Optional 4-digit year to filter. If None, shows all years.
            show: If True (default), display results. Set False to only populate result.
            pagination: If True (default), paginate output to fit screen.

        Result:
            bc.result contains a DataFrame with columns: year, books read, pages read.

        Alias: sbry()

        Example:
            >>> bc.sbry()                  # Summary for all years
            >>> bc.sbry(2024)              # Just 2024 stats
            >>> bc.sbry(show=False)        # Get data without display
        """
        q = self.end_point + "/summary_books_read_by_year"
        if year is not None:
            q += f"/{year}"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            self._show_table(res["data"], res["header"], [0, 1, 2], pagination) if show else None
            self.result = pd.DataFrame(res['data'], columns=res["header"])

    sbry = summary_books_read_by_year

    def year_rank(self, df=None, pages=True):
        """
        Rank years by reading volume (pages or books).

        Displays a ranked table showing which years had the most reading activity.

        Args:
            df: Optional DataFrame from summary_books_read_by_year(). If None,
                fetches fresh data automatically.
            pages: If True (default), rank by pages read. If False, rank by books read.

        Result:
            bc.result contains a DataFrame sorted by the chosen metric.

        Example:
            >>> bc.year_rank()              # Rank by pages (default)
            >>> bc.year_rank(pages=False)   # Rank by book count
        """
        if df is None:
            self.summary_books_read_by_year(show=False)
            df = self.result
        if pages:
            df = df.sort_values("pages read", ascending=False)
            sort_label = "Pages Read"
        else:
            df = df.sort_values("books read", ascending=False)
            sort_label = "Books Read"
        df.reset_index(inplace=True, drop=True)

        table = Table(
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
            title=f"[bold]Year Rankings by {sort_label}[/bold]",
            row_styles=["", "dim"],
        )
        table.add_column("Rank", style="cyan bold", justify="right")
        table.add_column("Year", style="cyan bold", justify="center")
        table.add_column("Books Read", style="green bold", justify="right")
        table.add_column("Pages Read", style="blue bold", justify="right")

        for idx, row in df.iterrows():
            table.add_row(
                str(idx + 1),
                str(int(row["year"])),
                str(int(row["books read"])),
                str(int(row["pages read"]))
            )

        console.print(table)
        self.result = df

    def add_books(self, n=1):
        """
        Interactively add new books to the collection.

        Prompts for each field (Title, Author, etc.) and allows editing before saving.

        Args:
            n: Number of books to add (default 1).

        Result:
            bc.result contains a list of BookIds for newly added books.

        Alias: ab()

        Example:
            >>> bc.ab()      # Add one book
            >>> bc.ab(3)     # Add three books
        """
        res = None
        records = [self._populate_new_book_record() for i in range(n)]
        res = self._add_books(records)
        return res

    ab = add_books

    def add_books_by_isbn(self, book_isbn_list):
        """
        Add books by looking up ISBN numbers.

        Fetches book metadata from ISBN database and allows editing before saving.

        Args:
            book_isbn_list: List of ISBN strings (ISBN-10 or ISBN-13).

        Result:
            bc.result contains the last book record added.

        Alias: abi()

        Example:
            >>> bc.abi(["9780547928227"])
            >>> bc.abi(["0060929480", "9780140449136"])
        """
        q = self.end_point + "/books_by_isbn"
        res = []
        # One lookup per ISBN: the API drops ISBNs it can't find, so a batched
        # response can't be reliably paired back to the requested ISBNs.
        for book_isbn in book_isbn_list:
            try:
                tr = requests.post(q, json={"isbn_list": [book_isbn]}, headers=self.header)
                book_record_list = tr.json()["book_records"]
            except (requests.RequestException, ValueError, KeyError) as e:
                logging.error(f"ISBN lookup failed for {book_isbn}: {e}")
                continue
            if not book_record_list:
                logging.error(f"No records found for isbn {book_isbn}.")
                continue
            proto = self._inputer(book_record_list[0])
            self.result = proto
            res.append(self._add_books([proto]))
        return res

    abi = add_books_by_isbn

    def add_read_books(self, book_collection_id_list):
        """
        Mark books as read with the current date.

        Prompts for read date and optional notes for each book.

        Args:
            book_collection_id_list: List of BookIds to mark as read.

        Result:
            bc.result contains a list of BookIds that were updated.

        Alias: arb()

        Example:
            >>> bc.arb([1234])           # Mark one book as read
            >>> bc.arb([123, 456, 789])  # Mark multiple books
        """
        records = [self._populate_add_read_date(id) for id in book_collection_id_list]
        q = self.end_point + "/add_read_dates"
        try:
            tr = requests.post(q, json=records, headers=self.header)
            tres = tr.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            new_book_collection_id_list = []
            for rec in tres["update_read_dates"]:
                new_book_collection_id_list.append(rec["BookId"])
            self.result = new_book_collection_id_list

    arb = add_read_books

    def update_tag_value(self, tag_value, new_tag_value):
        """
        Rename a tag globally across all books.

        Changes all occurrences of a tag to a new value.

        Args:
            tag_value: Current tag name to replace.
            new_tag_value: New tag name.

        Result:
            bc.result contains the API response with update count.

        Example:
            >>> bc.update_tag_value("scifi", "sci-fi")
            >>> bc.update_tag_value("favourites", "favorites")
        """
        q = self.end_point + f"/update_tag_value/{tag_value}/{new_tag_value}"
        try:
            r = requests.put(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            if "error" in res:
                console.print(f"[red]Error:[/red] {res['error']}")
            else:
                data = res["data"]
                console.print(f"[green]Updated:[/green] [yellow]{data['tag_update']}[/yellow] ([cyan]{data['updated_tags']}[/cyan] tags)")
            self.result = res

    def add_tags(self, book_collection_id, tags=[]):
        """
        Add one or more tags to a book.

        Tags are automatically normalized (lowercase, trimmed).

        Args:
            book_collection_id: The BookId to add tags to (integer).
            tags: List of tag strings to add.

        Result:
            bc.result contains the BookId.

        Alias: at()

        Example:
            >>> bc.at(1234, ["fiction", "classic"])
            >>> bc.at(1234, ["favorite"])
        """
        assert isinstance(book_collection_id, int), "Requires in integer Book ID"
        q = self.end_point + f"/add_tag/{book_collection_id}/" + "{}"
        result = {"data": [], "error": []}
        for t in tags:
            try:
                r = requests.put(q.format(t), headers=self.header)
                res = r.json()
                if "error" in res:
                    result["error"].append(res["error"])
                else:
                    result["data"].append(res)
            except requests.RequestException as e:
                logging.error(e)
                result["error"].append(e)
        else:
            console.print(f"[green]Added[/green] [cyan]{len(result['data'])}[/cyan] tags to book with id=[bold]{book_collection_id}[/bold]")
            if len(result["error"]) > 0:
                console.print(f"[red]Errors:[/red] {', '.join(str(e) for e in result['error'])}")
            self.result = book_collection_id

    at = add_tags


if __name__ == "__main__":
    rpl = BC_Tool()
    rpl.tag_counts()
    rpl.books_search(Title="science")
