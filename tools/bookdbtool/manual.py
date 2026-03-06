from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

doc_groups = {
    "search": {
        "title": "Search Commands",
        "description": "Find books, tags, and view details",
        "commands": [
            ("bs(**query)", "Search books by any field", "bs(Title=\"hobbit\", Author=\"tolkien\")"),
            ("book(id)", "Show complete book details with tags", "book(123)"),
            ("ts(match)", "Search for books by tag", "ts(\"fiction\")"),
            ("tc(tag)", "Show tag usage counts", "tc(\"sci\")"),
            ("col()", "List all searchable columns", "col()"),
        ]
    },
    "reading": {
        "title": "Reading History",
        "description": "View and analyze reading statistics",
        "commands": [
            ("bry(year)", "List books read in a year", "bry(2024)"),
            ("brys(year)", "Books read with inline summaries", "brys()"),
            ("sbry(year)", "Yearly summary (books & pages)", "sbry()"),
            ("year_rank(pages=True)", "Rank years by reading volume", "year_rank()"),
        ]
    },
    "add": {
        "title": "Add & Edit",
        "description": "Add books, tags, and reading records",
        "commands": [
            ("ab(n=1)", "Add books interactively", "ab()"),
            ("abi(isbn_list)", "Add books by ISBN lookup", "abi([\"978...\"])"),
            ("arb(id_list)", "Mark books as read", "arb([123, 456])"),
            ("at(id, tags)", "Add tags to a book", "at(123, [\"fiction\"])"),
            ("update_tag_value(old, new)", "Rename a tag globally", "update_tag_value(\"scifi\", \"sci-fi\")"),
        ]
    },
    "estimates": {
        "title": "Reading Estimates",
        "description": "Track reading progress and predict completion",
        "commands": [
            ("nbe(id, pages)", "Start tracking a book", "nbe(123, 350)"),
            ("lbe(id)", "Show estimates for a book", "lbe(123)"),
            ("aps(record_id, page)", "Record current page", "aps(45, 150)"),
        ]
    },
    "ai": {
        "title": "AI Assistant",
        "description": "Natural language queries using Ollama",
        "commands": [
            ("chat(prompt)", "Ask questions about your books", "chat(\"books by Tolkien?\")"),
            ("clear_history()", "Reset the conversation", "clear_history()"),
            ("show_history()", "View conversation history", "show_history()"),
            ("show_reply()", "See last AI response details", "show_reply()"),
        ]
    },
    "isbn": {
        "title": "ISBN Lookup",
        "description": "Fetch book info from ISBN databases",
        "commands": [
            ("lookup(isbn)", "Look up book by ISBN", "lookup(\"9780547928227\")"),
        ]
    },
    "utility": {
        "title": "Utilities",
        "description": "System and helper commands",
        "commands": [
            ("ver()", "Show version information", "ver()"),
            ("history()", "Show command history", "history()"),
            ("man.pages()", "Show this manual", "man.pages()"),
            ("man.quick_ref()", "Show quick reference", "man.quick_ref()"),
        ]
    }
}

# Legacy mapping for backwards compatibility
legacy_groups = {
    "bc": ["search", "reading", "add"],
    "est": ["estimates"],
    "ai": ["ai"],
    "isbn": ["isbn"],
}


def pages(groups=None):
    """
    Display the manual for specified command groups.

    Args:
        groups: List of group names to display. Options:
                "search", "reading", "add", "estimates", "ai", "isbn", "utility"
                Or legacy names: "bc", "est", "ai", "isbn"
                Default: all groups
    """
    if groups is None:
        groups = ["search", "reading", "add", "estimates", "ai", "isbn", "utility"]

    # Handle legacy group names
    expanded_groups = []
    for group in groups:
        if group in legacy_groups:
            expanded_groups.extend(legacy_groups[group])
        else:
            expanded_groups.append(group)
    groups = expanded_groups

    # Title
    title = Text()
    title.append("BookDBTool ", style="bold magenta")
    title.append("Manual", style="bold cyan")
    console.print(Panel(title, border_style="blue", padding=(0, 2)))

    for group in groups:
        if group not in doc_groups:
            console.print(f"[red]Unknown group: {group}[/red]")
            continue

        info = doc_groups[group]

        # Section header
        console.print(f"\n[bold magenta]{info['title']}[/bold magenta]")
        console.print(f"[dim]{info['description']}[/dim]\n")

        # Commands table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=False,
            row_styles=["", "dim"]
        )
        table.add_column("Command", style="yellow", width=30)
        table.add_column("Description", style="white", width=35)
        table.add_column("Example", style="green")

        for cmd, desc, example in info["commands"]:
            table.add_row(cmd, desc, example)

        console.print(table)

    # Footer with tips
    console.print()
    tips = Table(show_header=False, box=None, padding=(0, 2))
    tips.add_column("", style="cyan")
    tips.add_column("", style="white")
    tips.add_row("[bold]Tip:[/bold]", "Results stored in [yellow]result[/yellow] variable after each command")
    tips.add_row("", "Original tool objects available as [yellow]bc[/yellow], [yellow]est[/yellow], [yellow]ai[/yellow], [yellow]isbn[/yellow]")
    tips.add_row("", "Use [yellow]pagination=False[/yellow] to disable paging on long results")
    console.print(Panel(tips, border_style="green", title="[bold]Tips[/bold]"))


def quick_ref():
    """Show a compact quick reference card."""
    table = Table(
        title="[bold]Quick Reference[/bold]",
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    table.add_column("Action", style="white")
    table.add_column("Command", style="yellow")

    table.add_row("Search by title", "bs(Title=\"...\")")
    table.add_row("Search by author", "bs(Author=\"...\")")
    table.add_row("Search by tag", "ts(\"...\")")
    table.add_row("View book details", "book(ID)")
    table.add_row("Books read this year", "bry(2024)")
    table.add_row("Year rankings", "year_rank()")
    table.add_row("Add tags to book", "at(ID, [\"tag1\", \"tag2\"])")
    table.add_row("Track reading", "nbe(ID, pages)")
    table.add_row("Record progress", "aps(record_id, page)")
    table.add_row("AI search", "chat(\"...\")")
    table.add_row("ISBN lookup", "lookup(\"...\")")

    console.print(table)
