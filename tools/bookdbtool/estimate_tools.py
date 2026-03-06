__version__ = "0.2.0"

import datetime
import logging
import requests

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

FMT = "%Y-%m-%d"

console = Console()


class ESTTool:
    """
    Reading Estimate Tool - Track reading progress and predict completion dates.

    This class provides methods to track daily reading progress and calculate
    estimated completion dates based on reading pace.

    Workflow:
        1. Start tracking with new_book_estimate(book_id, total_pages)
        2. Record daily progress with add_page_date(record_id, current_page)
        3. View estimates with list_book_estimates(book_id)

    Attributes:
        result: Stores the result of the last operation (typically a BookId or RecordId).
        end_point: The API endpoint URL.

    Example:
        >>> est = ESTTool("http://localhost:8084", "your-api-key")
        >>> est.nbe(123, 350)     # Start tracking book 123 with 350 pages
        >>> est.aps(45, 100)      # Record progress: reached page 100
        >>> est.lbe(123)          # View completion estimates
    """

    def __init__(self, endpoint, api_key):
        self.end_point = endpoint
        self.header = {"x-api-key": f"{api_key}"}
        self.result = None

    def version(self):
        """
        Display version information for the API and estimate tools.

        Shows a formatted table with the API endpoint, API version, and tool version.

        Alias: ver()

        Example:
            >>> est.ver()
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
                title="[bold magenta]Book Records - Estimate Tools[/bold magenta]",
                title_justify="center",
            )
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Endpoint", self.end_point)
            table.add_row("API Version", res["version"])
            table.add_row("Estimates Version", __version__)
            console.print(table)

    ver = version

    def new_book_estimate(self, book_id, total_readable_pages):
        """
        Start tracking reading progress for a book.

        Creates a new reading estimate record and begins tracking from today's date.
        After creating, automatically displays the estimate information.

        Args:
            book_id: The BookId of the book to track.
            total_readable_pages: Total number of pages in the book (excluding index, etc.).

        Result:
            est.result contains the BookId.

        Alias: nbe()

        Example:
            >>> est.nbe(123, 350)     # Start tracking book 123 with 350 pages
            >>> est.nbe(456, 280)     # Track another book
        """
        q = self.end_point + f"/add_book_estimate/{book_id}/{total_readable_pages}"
        try:
            tr = requests.put(q, headers=self.header)
            tres = tr.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            if "error" in tres:
                console.print(f'[red]Error:[/red] {tres["error"]}')
            else:
                tres = tres["add_book_estimate"]
                console.print(f'[green]Started:[/green] Book [cyan]{tres["BookId"]}[/cyan] on [yellow]{tres["StartDate"]}[/yellow]')
        self.list_book_estimates(book_id)

    nbe = new_book_estimate

    def list_book_estimates(self, book_id):
        """
        Display reading estimates for a book.

        Shows book info, all reading sessions, and estimated completion dates
        (expected, earliest, and latest).

        Args:
            book_id: The BookId to show estimates for.

        Result:
            est.result contains the BookId.

        Alias: lbe()

        Example:
            >>> est.lbe(123)
        """
        q = self.end_point + f"/record_set/{book_id}"
        q1 = self.end_point + f"/books_search?BookId={book_id}"
        try:
            tr = requests.get(q, headers=self.header)
            tres = tr.json()
            br = requests.get(q1, headers=self.header)
            bres = br.json()["data"][0]
        except requests.RequestException as e:
            logging.error(e)
        except IndexError as ie:
            logging.error(f'IndexError: {ie}')
            console.print("[yellow]No estimates found for this book.[/yellow]")
        else:
            logging.debug(br)
            if "error" in tres:
                console.print(f'[red]Error:[/red] {tres["error"]}')
                console.print("[yellow]No estimates found for this book.[/yellow]")
            elif len(tres["record_set"]) > 0:
                tres = tres["record_set"]

                # Book info panel
                console.print(Panel(
                    f'[green]"{bres[1]}"[/green] by [yellow]{bres[2]}[/yellow] has [cyan bold]{bres[7]}[/cyan bold] pages',
                    title="[bold]Book Info[/bold]",
                    border_style="blue"
                ))

                # Estimates table
                table = Table(
                    show_header=True,
                    header_style="bold magenta",
                    border_style="blue",
                    title="[bold]Reading Estimates[/bold]"
                )
                table.add_column("Start Date", style="cyan")
                table.add_column("Record ID", style="dim")
                table.add_column("Est. Finish", style="green bold")
                table.add_column("Earliest", style="yellow")
                table.add_column("Latest", style="red")

                for i in range(len(tres["RecordId"])):
                    table.add_row(
                        tres["RecordId"][i][0],
                        str(tres["RecordId"][i][1]),
                        tres["Estimate"][i][0],
                        tres["Estimate"][i][1],
                        tres["Estimate"][i][2]
                    )

                console.print(table)
            self.result = book_id

    lbe = list_book_estimates

    def add_page_date(self, record_id, page, date=None):
        """
        Record reading progress for a tracked book.

        Updates the current page reached, which is used to calculate completion estimates.

        Args:
            record_id: The RecordId from new_book_estimate (shown in list_book_estimates).
            page: The current page number reached.
            date: Optional date string (YYYY-MM-DD). Defaults to today.

        Result:
            est.result contains the RecordId.

        Alias: aps()

        Example:
            >>> est.aps(45, 100)                    # Record page 100 for today
            >>> est.aps(45, 150, "2024-03-01")      # Record with specific date
        """
        if date is None:
            date = datetime.datetime.now().strftime(FMT)
        # find record id
        q = self.end_point + f"/add_date_page"
        payload = {"RecordId": record_id, "RecordDate": date, "Page": page}
        try:
            tr = requests.post(q, json=payload, headers=self.header)
            res = tr.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            if "error" in res:
                console.print(f'[red]Error:[/red] {res["error"]}')
            else:
                res = res["add_date_page"]
                console.print(f'[green]Recorded:[/green] Record [cyan]{res["RecordId"]}[/cyan] read to page [bold]{res["Page"]}[/bold] on [yellow]{date}[/yellow]')
        self.result = record_id

    aps = add_page_date
