import json
import readline
from code import InteractiveConsole
import os

import bookdbtool.estimate_tools as et
import bookdbtool.book_db_tools as rt
import bookdbtool.isbn_lookup_tools as isbn_module
import bookdbtool.ai_tools as ai_module
import bookdbtool.manual as manual

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

CONFIG_PATH = "/book_service/config/configuration.json"  # root is "tools"
console = Console()


def get_endpoint():
    try:
        cfile = open(f".{CONFIG_PATH}", "r")
    except OSError:
        try:
            cfile = open(f"..{CONFIG_PATH}", "r")
        except OSError:
            print("Configuration file not found!")
    with cfile:
        config = json.load(cfile)
        end_point = config["endpoint"]
        if os.getenv("API_KEY") is not None:
            api_key = os.getenv("API_KEY").replace('\n', '')
        elif "api_key" in config:
            api_key = config["api_key"].replace('\n', '')
        # todo fix this so everyone uses the same config
    return config, (end_point, api_key), config["isbn_com"]


ai_conf, book_service_conf, isbn_conf = get_endpoint()


def history():
    """Display command history."""
    console.print(Panel(
        '\n'.join([str(readline.get_history_item(i + 1)) for i in range(readline.get_current_history_length())]),
        title="[bold]Command History[/bold]",
        border_style="blue"
    ))


def show_welcome():
    """Display the welcome screen with usage information."""
    # Title
    title = Text()
    title.append("Book Collection Database", style="bold magenta")
    title.append(" REPL", style="bold cyan")

    console.print(Panel(title, border_style="blue", padding=(0, 2)))

    # Quick reference table
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        title="[bold]Available Commands[/bold]",
        expand=False
    )
    table.add_column("Category", style="cyan bold", width=12)
    table.add_column("Commands", style="yellow")
    table.add_column("Description", style="white")

    table.add_row(
        "Search",
        "bs()  ts()  tc()  book()",
        "Search books, tags, view details"
    )
    table.add_row(
        "Reading",
        "bry()  brys()  sbry()  year_rank()",
        "Books read by year, summaries, rankings"
    )
    table.add_row(
        "Add/Edit",
        "ab()  abi()  arb()  at()",
        "Add books, ISBNs, read dates, tags"
    )
    table.add_row(
        "Estimates",
        "nbe()  lbe()  aps()",
        "Track reading progress"
    )
    table.add_row(
        "AI",
        "chat()",
        "Natural language queries"
    )
    table.add_row(
        "Lookup",
        "lookup()",
        "ISBN lookup"
    )

    console.print(table)

    # Help info
    help_table = Table(show_header=False, border_style="dim", expand=False, box=None)
    help_table.add_column("", style="dim")
    help_table.add_column("", style="white")
    help_table.add_row("[cyan]man.pages()[/cyan]", "Show full manual with all commands")
    help_table.add_row("[cyan]man.quick_ref()[/cyan]", "Show quick reference card")
    help_table.add_row("[cyan]history()[/cyan]", "Show command history")
    help_table.add_row("[cyan]ver()[/cyan]", "Show version info")
    help_table.add_row("[cyan]exit()[/cyan]", "Exit the REPL")
    help_table.add_row("", "")
    help_table.add_row("[dim]Tip:[/dim]", "[dim]Results stored in 'result' variable[/dim]")
    help_table.add_row("[dim]Tip:[/dim]", "[dim]Original objects: bc, est, ai, isbn[/dim]")

    console.print(Panel(help_table, title="[bold]Quick Help[/bold]", border_style="green"))
    console.print()


# Create tool instances
bc = rt.BCTool(*book_service_conf)
est = et.ESTTool(*book_service_conf)
isbn = isbn_module.ISBNLookup(isbn_conf)
ai = ai_module.OllamaAgent(ai_conf)

# Track the last result from any operation
result = None


def _wrap_method(method, name):
    """Wrap a method to capture its result in the global 'result' variable."""
    def wrapper(*args, **kwargs):
        global result
        ret = method(*args, **kwargs)
        # Capture result from the instance if available
        if hasattr(method, '__self__') and hasattr(method.__self__, 'result'):
            result = method.__self__.result
        return ret
    wrapper.__doc__ = method.__doc__
    wrapper.__name__ = name
    return wrapper


# Build scope with all functions exposed directly
scope_vars = {
    # Original tool instances (for advanced use)
    "bc": bc,
    "est": est,
    "isbn": isbn,
    "ai": ai,

    # Utilities
    "history": history,
    "man": manual,

    # Global result variable
    "result": None,

    # === Book Collection (bc) methods ===
    # Version/Info
    "version": _wrap_method(bc.version, "version"),
    "ver": _wrap_method(bc.version, "ver"),
    "columns": _wrap_method(bc.columns, "columns"),
    "col": _wrap_method(bc.columns, "col"),

    # Search
    "books_search": _wrap_method(bc.books_search, "books_search"),
    "bs": _wrap_method(bc.books_search, "bs"),
    "tags_search": _wrap_method(bc.tags_search, "tags_search"),
    "ts": _wrap_method(bc.tags_search, "ts"),
    "tag_counts": _wrap_method(bc.tag_counts, "tag_counts"),
    "tc": _wrap_method(bc.tag_counts, "tc"),
    "book": _wrap_method(bc.book, "book"),

    # Reading history
    "books_read_by_year": _wrap_method(bc.books_read_by_year, "books_read_by_year"),
    "bry": _wrap_method(bc.books_read_by_year, "bry"),
    "books_read_by_year_with_summary": _wrap_method(bc.books_read_by_year_with_summary, "books_read_by_year_with_summary"),
    "brys": _wrap_method(bc.books_read_by_year_with_summary, "brys"),
    "summary_books_read_by_year": _wrap_method(bc.summary_books_read_by_year, "summary_books_read_by_year"),
    "sbry": _wrap_method(bc.summary_books_read_by_year, "sbry"),
    "year_rank": _wrap_method(bc.year_rank, "year_rank"),

    # Add/Edit
    "add_books": _wrap_method(bc.add_books, "add_books"),
    "ab": _wrap_method(bc.add_books, "ab"),
    "add_books_by_isbn": _wrap_method(bc.add_books_by_isbn, "add_books_by_isbn"),
    "abi": _wrap_method(bc.add_books_by_isbn, "abi"),
    "add_read_books": _wrap_method(bc.add_read_books, "add_read_books"),
    "arb": _wrap_method(bc.add_read_books, "arb"),
    "add_tags": _wrap_method(bc.add_tags, "add_tags"),
    "at": _wrap_method(bc.add_tags, "at"),
    "update_tag_value": _wrap_method(bc.update_tag_value, "update_tag_value"),

    # === Estimate (est) methods ===
    "new_book_estimate": _wrap_method(est.new_book_estimate, "new_book_estimate"),
    "nbe": _wrap_method(est.new_book_estimate, "nbe"),
    "list_book_estimates": _wrap_method(est.list_book_estimates, "list_book_estimates"),
    "lbe": _wrap_method(est.list_book_estimates, "lbe"),
    "add_page_date": _wrap_method(est.add_page_date, "add_page_date"),
    "aps": _wrap_method(est.add_page_date, "aps"),

    # === AI methods ===
    "chat": _wrap_method(ai.chat, "chat"),
    "clear_history": _wrap_method(ai.clear_history, "clear_history"),
    "show_history": _wrap_method(ai.show_history, "show_history"),
    "show_reply": _wrap_method(ai.show_reply, "show_reply"),

    # === ISBN methods ===
    "lookup": _wrap_method(isbn.lookup, "lookup"),
}


# Function to sync the global result with tool results
def _update_result():
    """Update global result from tool instances."""
    global result
    for tool in [bc, est, isbn, ai]:
        if hasattr(tool, 'result') and tool.result is not None:
            result = tool.result
            break


# Show welcome screen
show_welcome()

footer = "\n[bold green]Thanks for using the Book Collection REPL![/bold green]"

InteractiveConsole(locals=scope_vars).interact("", footer)
