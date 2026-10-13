"""
Server-side AI chat orchestration for the React AI Chat page.

Talks to an OpenAI-compatible chat LLM (ai_agent.chat_host/chat_model/
chat_api_key) and runs the full tool-calling loop in-process, so the
frontend never needs to know the chat model, host, or API key -- it just
POSTs its message history to POST /chat and gets back the updated history
plus a display trace (tool calls/results and the final reply).
"""
import json
from typing import Any

import requests

from .config import app_logger, CHAT_HOST, CHAT_MODEL, CHAT_API_KEY
from . import api_util

MAX_ITERATIONS = 10

# Some tools (e.g. get_tag_counts with no prefix) can return hundreds of
# rows -- large enough to blow past the chat model's context window on its
# own. Cap what goes back into the model-facing history; the UI still gets
# the full, untruncated result via the trace.
MAX_TOOL_RESULT_CHARS = 8000

SYSTEM_PROMPT = (
    "You are a helpful assistant for a personal book collection. You can search "
    "books, look up reading history, tags, and estimates using the tools provided. "
    "Be concise and friendly.\n\n"
    "Important: \"recent\"/\"recently\" is ambiguous - a book's record can be edited "
    "long after it was read. For any question about reading recency (recently read, "
    "last book read, what did I just finish, most recent book), use "
    "get_recently_read_books, which is based on actual reading completion date. "
    "Only use get_recently_edited_books when the user is explicitly asking about "
    "recent edits, updates, or changes to records - never use it to answer a "
    "reading-recency question, and never treat a book's ReadDate from "
    "get_book_details as \"recent\" just because the book itself came from "
    "get_recently_edited_books.\n\n"
    "Read-note reviews: when get_book_details returns reads_missing_notes, tell the user "
    "that read has no read note and ask for the 3 to 4 most important observations "
    "they took away from the book. Once they reply, call draft_read_note with those "
    "observations. The draft is shown to the user in an editable box with a Save "
    "button - you cannot save it yourself, so never say the note was saved or updated. "
    "After draft_read_note succeeds, reply with one short sentence saying the draft is "
    "ready to edit and save in the box below - do not restate the draft or the observations. "
    "If the user asks for changes, call draft_read_note again with the revised observations."
)

DRAFT_REVIEW_PROMPT = (
    "You write personal reading notes for a book collection. Write a 3 to 4 paragraph "
    "review in the first person, as the reader, built only from the reader's "
    "observations. You may use the title, author and tags for context, but do not "
    "invent plot details, quotes or opinions the reader did not give. Plain prose: no "
    "headings, no bullet points, no markdown (no asterisks or underscores, even around the "
    "title), no preamble - return only the review text, "
    "with paragraphs separated by a blank line."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": "Search the book collection by author, title, location, ISBN, or BookId. Returns a list of matching books.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Author": {"type": "string", "description": "Author name (partial match supported)"},
                    "Title": {"type": "string", "description": "Book title (partial match supported)"},
                    "Location": {"type": "string", "description": "Shelf location (e.g. Main Collection, Bedroom, Storage)"},
                    "IsbnNumber": {"type": "string", "description": "ISBN-10"},
                    "IsbnNumber13": {"type": "string", "description": "ISBN-13"},
                    "BookId": {"type": "number", "description": "Exact book ID"},
                    "BookNote": {"type": "string", "description": "Search within book notes/annotations (partial match supported)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_book_details",
            "description": "Get the full record for a specific book including metadata, reads, tags, and images.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bookId": {"type": "number", "description": "The BookId of the book"},
                },
                "required": ["bookId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recently_edited_books",
            "description": (
                "Get books ranked by when the record was last edited/touched (metadata edit, tag change, "
                "image upload, reading-progress update) - NOT by reading date. "
                "Do NOT use this for \"recently read\", \"last read\", or \"what did I just finish\" questions - "
                "those mean reading completion date, not edit history. Use get_recently_read_books instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Number of recent books to return (default 10)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recently_read_books",
            "description": (
                "Get the books most recently finished reading, ranked by actual completion date (ReadDate), "
                "not by when the record was last edited. This is the default tool for ANY question implying "
                "reading recency - \"recently read\", \"last book(s) I read\", \"what did I just finish\", "
                "\"most recent book(s)\", \"latest read\" - even if the word \"edited\" or \"updated\" is not used."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Number of books to return (default 10)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_books_read_by_year",
            "description": "Get books that were read in a given year. Omit year to get all read books across all years.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "number", "description": "Year (e.g. 2023). Omit for all years."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reading_summary",
            "description": "Get a yearly reading summary showing pages and books read per year.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "number", "description": "Specific year to filter to. Omit for all years."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tags_for_book",
            "description": "Get all tags associated with a specific book.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bookId": {"type": "number", "description": "The BookId of the book"},
                },
                "required": ["bookId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_books_by_tag",
            "description": "Find all books that have a specific tag label.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "description": "Tag label to search for (e.g. \"birding\", \"fiction\")"},
                },
                "required": ["tag"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tag_counts",
            "description": (
                "Get the count of books for each tag, sorted most-used first. "
                "A collection can have hundreds of distinct tags, so always pass "
                "a limit for \"top N\" / \"most common\" questions rather than "
                "fetching the full list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prefix": {"type": "string", "description": "Optional prefix to filter tag names"},
                    "limit": {"type": "number", "description": "Max number of tags to return, most-used first (default 20)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reading_estimates",
            "description": "Get reading estimate sessions for a specific book.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bookId": {"type": "number", "description": "The BookId of the book"},
                },
                "required": ["bookId"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_tag_to_book",
            "description": "Add a tag to a specific book. Creates the tag label if it does not already exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bookId": {"type": "number", "description": "The BookId of the book to tag"},
                    "tag": {"type": "string", "description": "The tag label to add (will be lowercased)"},
                },
                "required": ["bookId", "tag"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_read_note",
            "description": (
                "Draft a 3-4 paragraph read-note review of a book from the user's own "
                "observations, and show it to the user to edit and save. Does not save "
                "anything. Use after the user gives their observations for a read that "
                "has no read note."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bookId": {"type": "number", "description": "The BookId of the book"},
                    "readDate": {"type": "string", "description": "The read's DateRead (YYYY-MM-DD)"},
                    "observations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The user's 3-4 most important observations, in their words",
                    },
                },
                "required": ["bookId", "readDate", "observations"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search_notes",
            "description": (
                "Search book notes and reading notes by meaning rather than exact keywords. "
                "Use when the user asks about themes, topics, or ideas they remember from a book, "
                "or wants to find books related to a concept, feeling, or subject area."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language description of what to find"},
                    "limit": {"type": "number", "description": "Max results to return (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
]


def _tool_search_books(args: dict) -> dict:
    rows, header, _ = api_util.books_search_utility(args)
    return api_util._create_serializeable_result_dict(rows, header)


def _reads_missing_notes(record: dict) -> list[dict]:
    """Reads of a complete book record that have a date but a blank ReadNote."""
    reads = record.get("reads") or {}
    header = reads.get("header") or []
    if "DateRead" not in header or "ReadNote" not in header:
        return []
    i_date, i_note = header.index("DateRead"), header.index("ReadNote")
    return [
        {"ReadDate": row[i_date]}
        for row in reads.get("data") or []
        if row[i_date] and not (row[i_note] or "").strip()
    ]


def _tool_get_book_details(args: dict) -> dict:
    record = api_util.get_complete_book_record(args.get("bookId"))
    missing = _reads_missing_notes(record)
    if missing:
        # Flag it in the result rather than relying on the system prompt alone:
        # the chat model follows a field in a tool result more reliably.
        record["reads_missing_notes"] = missing
        record["next_step"] = (
            "This book was read but has no read note. Ask the user for the 3 to 4 most "
            "important observations about the book, then call draft_read_note with them."
        )
    return record


def _book_field(record: dict, name: str) -> Any:
    book = record.get("book") or {}
    header, data = book.get("header") or [], book.get("data") or []
    if not data or name not in header:
        return None
    return data[0][header.index(name)]


def draft_read_note(book_id: int, read_date: str, observations: list[str]) -> dict:
    """
    Ask the chat LLM for a 3-4 paragraph review of a book built from the
    reader's observations. Writes nothing -- the caller shows the draft to the
    user, who edits and saves it via POST /update_edit_read_note.

    Raises ValueError for a missing book or no usable observations, and
    requests.RequestException if the chat LLM call fails.
    """
    observations = [str(o).strip() for o in observations or [] if str(o).strip()]
    if not observations:
        raise ValueError("At least one observation is required")
    record = api_util.get_complete_book_record(book_id)
    title = _book_field(record, "Title")
    if not title:
        raise ValueError(f"No book with BookId {book_id}")
    reads = record.get("reads") or {}
    if "DateRead" in (reads.get("header") or []):
        i_date = reads["header"].index("DateRead")
        read_dates = [row[i_date] for row in reads.get("data") or []]
        if read_date not in read_dates:
            raise ValueError(f"BookId {book_id} has no read on {read_date}; its reads are {read_dates}")
    tags = (record.get("tags") or {}).get("data") or []
    tag_list = ", ".join(tags[0]) if tags and tags[0] else "none"
    user_content = (
        f"Book: {title}\nAuthor: {_book_field(record, 'Author') or 'unknown'}\n"
        f"Tags: {tag_list}\nFinished reading: {read_date}\n\nMy observations:\n"
        + "\n".join(f"- {o}" for o in observations)
    )
    response = chat_completion(
        [{"role": "system", "content": DRAFT_REVIEW_PROMPT}, {"role": "user", "content": user_content}],
        tools=None,
    )
    draft = (response["choices"][0]["message"].get("content") or "").strip()
    if not draft:
        raise ValueError("The chat model returned an empty draft")
    return {"BookId": book_id, "ReadDate": read_date, "Title": title, "draft": draft}


def _tool_draft_read_note(args: dict) -> dict:
    observations = args.get("observations") or []
    if isinstance(observations, str):
        observations = [line.lstrip("-* ").strip() for line in observations.splitlines()]
    result = draft_read_note(args.get("bookId"), args.get("readDate"), observations)
    result["status"] = "Draft shown to the user to edit and save. It has NOT been saved."
    return result


def _tool_get_recently_edited_books(args: dict) -> dict:
    recent_books, _, header, _ = api_util.get_recently_touched(args.get("limit") or 10)
    return api_util._create_serializeable_result_dict(recent_books, header)


def _tool_get_recently_read_books(args: dict) -> dict:
    recent_books, _, header, _ = api_util.get_recently_read(args.get("limit") or 10)
    return api_util._create_serializeable_result_dict(recent_books, header)


def _tool_get_books_read_by_year(args: dict) -> dict:
    rows, header, _ = api_util.books_read_by_year_utility(args.get("year"))
    return api_util._create_serializeable_result_dict(rows, header)


def _tool_get_reading_summary(args: dict) -> dict:
    rows, header, _ = api_util.summary_books_read_by_year_utility(args.get("year"))
    return api_util._create_serializeable_result_dict(rows, header)


def _tool_get_tags_for_book(args: dict) -> dict:
    rdata, _ = api_util.book_tags(args.get("bookId"))
    return rdata


def _tool_search_books_by_tag(args: dict) -> dict:
    rows, header, _ = api_util.tags_search_utility(args.get("tag", ""))
    return api_util._create_serializeable_result_dict(rows, header)


def _tool_get_tag_counts(args: dict) -> dict:
    rows, header, _ = api_util.get_tag_counts(args.get("prefix"))
    limit = args.get("limit") or 20
    return api_util._create_serializeable_result_dict(rows[:limit], header)


def _tool_get_reading_estimates(args: dict) -> dict:
    return api_util.get_estimate_records_for_book(args.get("bookId"))


def _tool_add_tag_to_book(args: dict) -> dict:
    rdata, _ = api_util.add_tag_to_book(args.get("bookId"), args.get("tag"))
    return rdata


def _tool_semantic_search_notes(args: dict) -> list:
    return api_util.rag_search(args.get("query", ""), limit=args.get("limit") or 5)


TOOL_DISPATCH = {
    "search_books": _tool_search_books,
    "get_book_details": _tool_get_book_details,
    "get_recently_edited_books": _tool_get_recently_edited_books,
    "get_recently_read_books": _tool_get_recently_read_books,
    "get_books_read_by_year": _tool_get_books_read_by_year,
    "get_reading_summary": _tool_get_reading_summary,
    "get_tags_for_book": _tool_get_tags_for_book,
    "search_books_by_tag": _tool_search_books_by_tag,
    "get_tag_counts": _tool_get_tag_counts,
    "get_reading_estimates": _tool_get_reading_estimates,
    "add_tag_to_book": _tool_add_tag_to_book,
    "draft_read_note": _tool_draft_read_note,
    "semantic_search_notes": _tool_semantic_search_notes,
}


def _serialize_tool_result_for_model(result: Any) -> str:
    """JSON-serialize a tool result for the model-facing history, truncating
    oversized results so a single large tool call can't blow the context
    window. Truncation only affects what the model sees, never `trace`."""
    serialized = json.dumps(result)
    if len(serialized) <= MAX_TOOL_RESULT_CHARS:
        return serialized
    return (
        serialized[:MAX_TOOL_RESULT_CHARS]
        + f"... [truncated, {len(serialized)} total characters -- ask a more specific question to narrow this down]"
    )


def _model_view_of_tool_result(name: str, result: Any) -> Any:
    """What the model sees of a tool result. A draft_read_note draft goes only
    to the UI (via trace): the model otherwise pastes the whole draft into its
    reply, duplicating the editable box, and revisions regenerate from the
    observations anyway."""
    if name == "draft_read_note" and isinstance(result, dict) and "draft" in result:
        return {**result, "draft": "[shown to the user in an editable box]"}
    return result


def execute_tool(name: str, args: dict) -> Any:
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(args or {})
    except Exception as e:
        app_logger.error(f"chat tool {name} failed: {e}")
        return {"error": str(e)}


def chat_completion(messages: list[dict], tools: list[dict] | None = TOOLS) -> dict:
    """POST an OpenAI-compatible /v1/chat/completions request to ai_agent.chat_host.
    Pass tools=None for a plain completion with no tool calling."""
    if not CHAT_HOST or not CHAT_MODEL:
        raise RuntimeError("ai_agent.chat_host and chat_model must be configured")
    url = f"{CHAT_HOST.rstrip('/')}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if CHAT_API_KEY:
        headers["Authorization"] = f"Bearer {CHAT_API_KEY}"
    payload = {"model": CHAT_MODEL, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_chat_loop(history: list[dict]) -> dict:
    """
    Run the tool-calling loop to completion against the given OpenAI-format
    message history (already including the user's new turn), mutating and
    returning it, plus a "trace" of display events (tool calls/results and
    the final assistant reply) for the frontend to render.

    `history` holds only user/assistant/tool turns -- SYSTEM_PROMPT is owned
    here and prepended to each model call, never stored in or returned as
    part of `history`.
    """
    trace: list[dict] = []
    for _ in range(MAX_ITERATIONS):
        response = chat_completion([{"role": "system", "content": SYSTEM_PROMPT}, *history])
        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            content = message.get("content") or "No response."
            history.append({"role": "assistant", "content": message.get("content") or ""})
            trace.append({"type": "assistant", "content": content})
            return {"history": history, "trace": trace}

        history.append({
            "role": "assistant",
            "content": message.get("content") or "",
            "tool_calls": tool_calls,
        })

        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            raw_args = tc["function"].get("arguments") or "{}"
            try:
                tool_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except json.JSONDecodeError:
                tool_args = {}
            result = execute_tool(tool_name, tool_args)
            trace.append({
                "type": "tool",
                "toolCallId": tc.get("id"),
                "toolName": tool_name,
                "toolArgs": tool_args,
                "toolResult": result,
            })
            history.append({
                "role": "tool",
                "content": _serialize_tool_result_for_model(_model_view_of_tool_result(tool_name, result)),
                "tool_call_id": tc.get("id"),
            })

    trace.append({
        "type": "assistant",
        "content": "Sorry, I couldn't finish that within the allowed number of steps.",
    })
    return {"history": history, "trace": trace}
