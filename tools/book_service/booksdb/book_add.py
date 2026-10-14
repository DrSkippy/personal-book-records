"""
Resolve, de-duplicate, insert and correct book records.

Used by the books MCP server's add-book tools (an AI client adding a book, or
working through a list from a source with incomplete book information) and by
book-service's POST /add_books (insert only).

resolve_book() takes whatever fields the caller has and:

1. Fills blanks from isbndb -- the same lookup the UI's ISBN entry uses. With a
   caller ISBN that edition is authoritative. Without one, a title search
   (fallback chain: ranked search with author, title column, title + surname
   text) is scored to prefer physical, English, US-market, complete editions
   and to push down digital, audio and bundle editions.
2. Stops for review ("needs_review") instead of guessing when the pick is
   unclear: no match, no physical edition (or none in the caller's
   cover_type), both Hard and Soft editions with no cover_type given, or the
   caller's author conflicting with isbndb's. Nothing is filled from isbndb in
   that case; add_book refuses until the caller picks an isbn13 or passes
   accept_as_is to store only its own fields.
3. Normalizes: authors "Last, First and First Last", titles with a leading
   article and the full "Title: Subtitle", cleaned isbndb values.
4. Checks the collection for redundant copies:
   - same caller-supplied ISBN (either form)           -> "duplicate", never added
   - same title + author, same CoverType (or unknown)  -> "duplicate", never added
   - same title + author, a different CoverType        -> "confirm_second_copy":
     added only with confirm_second_copy=True after the user confirms it
     really is a second acquisition
   - same title under a different author               -> warning only

Digital books are always stored at DOWNLOAD, but a Digital cover type is only
taken from the caller or from the caller's ISBN, never from a title-search guess.
"""
import datetime
import re
from typing import Any

from .config import app_logger, books_conf, isbn_conf
from .isbn_com import Endpoint
from . import api_util

psycopg2 = api_util.psycopg2

COVER_TYPES = ("Hard", "Soft", "Digital")
DEFAULT_LOCATION = "Main Collection"
DIGITAL_LOCATION = "DOWNLOAD"
# The UI's VALID_LOCATIONS; locations already in use are accepted too
KNOWN_LOCATIONS = ("Main Collection", "Bedroom", "Storage", "Oversized", "Pets",
                   "Woodwork", "Reference", "Birding", "DOWNLOAD")
FIELD_LIMITS = {"Title": 200, "Author": 200, "PublisherName": 50}
MAX_PAGES = 32767  # SMALLINT
MIN_PAGES = 50  # isbndb page counts below this are usually wrong (e.g. 20 for The Power Broker)
MAX_BATCH = 25
COMPACT_CANDIDATES = 3
SEARCH_PAGE_SIZE = 50
MIN_CONFIDENT_SCORE = 2.0  # below this the best physical edition is doubtful (bundle, odd title, ...)
CLOSE_SCORE = 0.5  # editions within this of the best are treated as equally likely
FIELDS = ("Title", "Author", "CopyrightDate", "IsbnNumber", "IsbnNumber13", "PublisherName",
          "CoverType", "Pages", "Location", "BookNote", "Recycled")
REQUIRED = ("Title", "Author", "Location")

_AUTHOR_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "phd", "ph.d.", "md"}
_SURNAME_PARTICLES = {"van", "von", "de", "der", "den", "del", "della", "da", "di", "du", "la", "le"}
_LEADING_ARTICLES = ("the", "a", "an")
_SMALL_WORDS = {"a", "an", "the", "and", "or", "nor", "but", "of", "in", "on", "at", "to", "for",
                "by", "from", "with", "over", "into", "as", "vs"}
_AUDIO_RE = re.compile(r"\b(audio|cd|cassette|mp3|preloaded|playaway|audible|audiobook)\b")
_BUNDLE_RE = re.compile(r"\b(package|box(ed)? set|collection set|postcards|library edition|bundle|"
                        r"leader'?s edition|study guide|summary of|workbook)\b")
_BINDING_SCORE = {"physical": 0, "unknown": -2, "digital": -4, "audio": -6}

INSERT_SQL = ("INSERT INTO books "
              "(Title, Author, CopyrightDate, IsbnNumber, IsbnNumber13, PublisherName, CoverType, Pages, "
              "Location, BookNote, Recycled) "
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING bookid")


##########################################################################
# ISBNs
##########################################################################

def _isbn10_check(core9: str) -> str:
    check = (11 - sum((10 - i) * int(d) for i, d in enumerate(core9)) % 11) % 11
    return "X" if check == 10 else str(check)


def _isbn13_check(core12: str) -> str:
    return str((10 - sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core12)) % 10) % 10)


def normalize_isbn(value: Any) -> tuple[str | None, str | None]:
    """Return (isbn10, isbn13) for a valid ISBN-10 or ISBN-13 in any punctuation, deriving the
    other form where one exists (979- ISBN-13s have no ISBN-10). (None, None) if invalid."""
    s = re.sub(r"[^0-9Xx]", "", str(value or "")).upper()
    if len(s) == 10 and s[:9].isdigit() and _isbn10_check(s[:9]) == s[9]:
        core = "978" + s[:9]
        return s, core + _isbn13_check(core)
    if len(s) == 13 and s.isdigit() and _isbn13_check(s[:12]) == s[12]:
        return Endpoint.isbn13_to_isbn10(s), s
    return None, None


##########################################################################
# Authors: stored "Last, First" for the first author, "First Last" for the
# rest -- "Levitt, Steven D and Stephen J Dubner", "A, B, C and D"
##########################################################################

def _clean_name(name: Any) -> str:
    """Tidy one isbndb/caller name: whitespace, life dates ("Herzog, Werner,, 1942-"), doubled
    and trailing punctuation."""
    name = re.sub(r"\s+", " ", str(name or "")).strip()
    name = re.sub(r",?\s*\(?\b\d{3,4}\s*-\s*(\d{3,4})?\)?\.?$", "", name)
    name = re.sub(r"\s*,\s*,+", ",", name)
    return name.strip(" ,;")


def split_authors(value: Any) -> list[str]:
    """Split authors given as a list and/or joined with ";", " and " or " & "."""
    items = value if isinstance(value, (list, tuple)) else [value]
    out = []
    for item in items:
        for part in re.split(r"\s*;\s*|\s+(?:and|&)\s+", str(item or "")):
            name = _clean_name(part)
            if name:
                out.append(name)
    return out


def _split_name(name: str) -> tuple[str, str]:
    """(given names, surname) for "Last, First" or "First [particle] Last [Jr.]"."""
    if "," in name:
        last, given = (p.strip() for p in name.split(",", 1))
        return given, last
    tokens = name.split(" ")
    suffix = []
    if len(tokens) > 2 and tokens[-1].lower() in _AUTHOR_SUFFIXES:
        suffix = [tokens.pop()]
    if len(tokens) < 2:
        return "", name
    i = len(tokens) - 1
    while i > 1 and tokens[i - 1].lower() in _SURNAME_PARTICLES:
        i -= 1
    return " ".join(tokens[:i] + suffix), " ".join(tokens[i:])


def _last_first(name: str) -> str:
    given, last = _split_name(name)
    return f"{last}, {given}" if given else last


def _first_last(name: str) -> str:
    given, last = _split_name(name)
    return f"{given} {last}" if given else last


def format_authors(names: list[str]) -> str:
    if not names:
        return ""
    head, rest = _last_first(names[0]), [_first_last(n) for n in names[1:]]
    if not rest:
        return head
    if len(rest) == 1:
        return f"{head} and {rest[0]}"
    return f"{head}, {', '.join(rest[:-1])} and {rest[-1]}"


def normalize_author(value: Any) -> str:
    """Authors (a string or a list) in the collection's form. "Kevin Fedarko" -> "Fedarko, Kevin";
    ["Acemoglu, Daron", "Johnson, Simon"] -> "Acemoglu, Daron and Simon Johnson"; "Ludwig van
    Beethoven" -> "van Beethoven, Ludwig". A first author already in "Last, First" form is kept."""
    return format_authors(split_authors(value))


def _author_keys(value: Any) -> list[tuple[str, str]]:
    """(surname, first initial) for each author."""
    out = []
    for name in split_authors(value):
        given, last = _split_name(name)
        surname = re.findall(r"\w+", last.lower())
        initial = re.findall(r"[^\W\d_]", given.lower())
        if surname:
            out.append((surname[-1], initial[0] if initial else ""))
    return out


def _surname_key(author: Any) -> str:
    keys = _author_keys(author)
    return keys[0][0] if keys else ""


def _author_match(caller: Any, candidate: Any) -> str:
    """"match", "conflict" (same surname, different first initial -- e.g. "John Vernon Moore"
    vs "Moore, Lucy") or "none" for the caller's first author against the candidate's authors."""
    caller_keys = _author_keys(caller)
    if not caller_keys:
        return "match"
    surname, initial = caller_keys[0]
    same = [i for s, i in _author_keys(candidate) if s == surname]
    if not same:
        return "none"
    if initial and all(i and i != initial for i in same):
        return "conflict"
    return "match"


##########################################################################
# Titles: leading article ("The X", not "X, The"), full "Title: Subtitle"
##########################################################################

def normalize_title(title: Any) -> str:
    """Collapse whitespace, strip trailing punctuation, and move a trailing article to the front:
    "Lost Elements, The: The periodic table's shadow side" -> "The Lost Elements: The periodic ..."."""
    t = re.sub(r"\s+", " ", str(title or "")).strip().rstrip(" ./;,")
    m = re.match(r"^(.+?),\s*(The|A|An)\s*(:.*)?$", t, flags=re.IGNORECASE)
    if m:
        t = f"{m.group(2).capitalize()} {m.group(1)}{m.group(3) or ''}"
    return t


def _title_words(title: Any) -> list[str]:
    words = re.findall(r"\w+", normalize_title(title).lower())
    if words and words[0] in _LEADING_ARTICLES:
        words = words[1:]
    return words


def _main_title(title: Any) -> str:
    return normalize_title(title).split(":")[0].strip()


def titles_match(a: Any, b: Any) -> bool:
    """Same title, ignoring case, punctuation, a leading (or trailing) article, and a subtitle on
    either side (isbndb often drops the colon: "The Emerald Mile The Epic Story ...")."""
    wa, wb = _title_words(a), _title_words(b)
    if not wa or not wb:
        return False
    short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return long_[:len(short)] == short


def _title_exact(query: Any, candidate: Any) -> bool:
    q = _title_words(query)
    return q == _title_words(candidate) or q == _title_words(_main_title(candidate))


def _title_case(text: str) -> str:
    words = text.split(" ")
    return " ".join(w if i and w.lower() in _SMALL_WORDS
                    else "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
                    for i, w in enumerate(words))


def full_title(caller_title: str, candidate_title: str) -> str:
    """The caller's title extended with the candidate's subtitle ("Power and Progress" +
    "Power and progress: our thousand-year struggle ..." -> "Power and Progress: Our
    Thousand-Year Struggle ..."), or the caller's title if there is no subtitle to add."""
    caller_title = normalize_title(caller_title)
    if ":" in caller_title or not candidate_title:
        return caller_title
    query = _title_words(caller_title)
    cand = normalize_title(candidate_title)
    if ":" in cand:
        main, sub = cand.split(":", 1)
        if _title_words(main) != query:
            return caller_title
    else:
        pattern = r"^\W*(?:(?:the|a|an)\W+)?" + r"\W+".join(map(re.escape, query)) + r"\b\W*(.*)$"
        m = re.match(pattern, cand, flags=re.IGNORECASE)
        if not m:
            return caller_title
        sub = m.group(1)
    sub = sub.strip(" .;:/")
    if not sub:
        return caller_title
    significant = [w for w in caller_title.split(" ") if w.lower() not in _SMALL_WORDS]
    if significant and all(w[:1].isupper() or not w[:1].isalpha() for w in significant):
        sub = _title_case(sub)
    else:
        sub = sub[:1].upper() + sub[1:]
    full = f"{caller_title}: {sub}"
    return full if len(full) <= FIELD_LIMITS["Title"] else caller_title


def _cover_base(cover: Any) -> str:
    """'Soft; 22x28' -> 'Soft'."""
    return str(cover or "").split(";")[0].strip()


def _cover_type(value: Any) -> str | None:
    """Caller cover type in canonical case, or None if not one of COVER_TYPES."""
    base = _cover_base(value).lower()
    return next((c for c in COVER_TYPES if c.lower() == base), None)


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
    return None if value in ("", None, []) else value


##########################################################################
# isbndb candidates
##########################################################################

def _endpoint() -> Endpoint:
    return Endpoint(isbn_conf)


def _binding_class(binding: Any) -> str:
    b = str(binding or "").lower()
    if _AUDIO_RE.search(b):
        return "audio"
    cover = Endpoint.binding_to_cover_type(b)
    return {"Hard": "physical", "Soft": "physical", "Digital": "digital"}.get(cover, "unknown")


def _to_candidate(ep: Endpoint, book: dict) -> dict | None:
    """An isbndb book as a cleaned collection-format record plus binding/language/notes."""
    proto = ep._endpoint_to_collection_db({"book": book})
    if proto is None:
        return None
    for k in ("Location", "BookNote", "Recycled"):
        proto.pop(k, None)
    proto["Title"] = normalize_title(proto["Title"])
    proto["Author"] = normalize_author(book.get("authors") or [])
    publisher = re.sub(r"\s+", " ", str(proto.get("PublisherName") or ""))
    publisher = re.sub(r",?\s+an imprint of .*$", "", publisher, flags=re.IGNORECASE).strip(" ,;:")
    proto["PublisherName"] = None if publisher.lower() in ("", "unknown") else publisher
    try:
        pages = int(proto.get("Pages") or 0)
    except (TypeError, ValueError):
        pages = 0
    proto["Pages"] = pages if pages >= MIN_PAGES else None
    if 0 < pages < MIN_PAGES:
        proto["pages_dropped"] = pages
    proto["CoverType"] = proto.get("CoverType") or None
    proto["IsbnNumber"] = proto.get("IsbnNumber") or None
    proto["IsbnNumber13"] = proto.get("IsbnNumber13") or None
    proto["title_long"] = book.get("title_long") or ""
    proto["binding"] = book.get("binding") or ""
    proto["language"] = book.get("language") or ""
    proto["binding_class"] = _binding_class(proto["binding"])
    return proto


def score_candidate(c: dict, query_title: str | None = None) -> float:
    """Higher is a better guess at the copy in hand: physical, exact title, US/English,
    complete, already published; bundles, digital and audio editions pushed down."""
    score = float(_BINDING_SCORE[c["binding_class"]])
    if query_title:
        score += 3 if _title_exact(query_title, c["Title"]) else -1
    if _BUNDLE_RE.search(f"{c['Title']} {c.get('title_long', '')} {c['binding']}".lower()):
        score -= 5
    isbn13 = c.get("IsbnNumber13") or ""
    if isbn13.startswith(("9780", "9781")):
        score += 1.5
    elif isbn13.startswith("9798"):
        score += 1
    lang = c["language"].lower()
    if lang in ("en", "eng") or lang.startswith(("en_", "en-")):
        score += 1
    elif lang:
        score -= 3
    if not c.get("Pages"):
        score -= 1.5
    if not c.get("PublisherName"):
        score -= 0.5
    date = c.get("CopyrightDate")
    if not date:
        score -= 0.5
    elif date > datetime.date.today().isoformat():
        score -= 3
    return score


def _rank(cands: list[dict], query_title: str | None) -> list[dict]:
    """Sort by score, then pages present, keeping isbndb's relevance order among ties; drop
    repeated ISBNs."""
    seen, unique = set(), []
    for c in cands:
        key = c.get("IsbnNumber13") or c.get("IsbnNumber") or id(c)
        if key not in seen:
            seen.add(key)
            c["score"] = round(score_candidate(c, query_title), 1)
            unique.append(c)
    unique.sort(key=lambda c: (-c["score"], not c.get("Pages")))  # stable: isbndb order among ties
    return unique


def candidate_summary(c: dict) -> str:
    """One line per candidate for compact responses."""
    year = (c.get("CopyrightDate") or "?")[:4]
    pages = f"{c['Pages']}pp" if c.get("Pages") else "?pp"
    return (f"{c.get('IsbnNumber13') or c.get('IsbnNumber') or '?'} | {c.get('binding') or 'binding?'} | "
            f"{c.get('PublisherName') or '?'} | {year} | {pages} | {c.get('language') or '?'} | "
            f"{c.get('Author') or '?'} | {c['Title'][:70]}")


def _title_search(ep: Endpoint, title: str, author: Any) -> tuple[list[dict], str | None, list[str]]:
    """Fallback chain for a book without an ISBN. Returns (candidates matching the title and the
    author's surname, the step that found them, errors)."""
    names = split_authors(author) if author else []
    surname = _surname_key(names) if names else ""
    queries = [normalize_title(title)]
    if _main_title(title) != queries[0]:
        queries.append(_main_title(title))
    steps = []
    for q in queries:
        if names:
            steps.append(("search", lambda q=q: ep.search_books(q, author=_first_last(names[0]),
                                                                page_size=SEARCH_PAGE_SIZE)))
        steps.append(("title", lambda q=q: ep.search_books_by_title(q, page_size=SEARCH_PAGE_SIZE)))
        if surname:
            steps.append(("title+author text", lambda q=q: ep.search_books_by_text(
                f"{q} {surname}", page_size=SEARCH_PAGE_SIZE)))
    errors = []
    for step, fetch in steps:
        books = fetch()
        if isinstance(books, dict):
            errors.append(str(books.get("error")))
            continue
        cands = [c for c in (_to_candidate(ep, b) for b in books)
                 if c and titles_match(title, c["Title"])
                 and (not surname or surname in {s for s, _ in _author_keys(c["Author"])})]
        if cands:
            return cands, step, errors
    return [], None, errors


def lookup_metadata(isbn: str | None = None, title: str | None = None, author: Any = None,
                    limit: int = 5) -> dict:
    """Look a book up on isbndb. With an ISBN, that edition; otherwise the title-search fallback
    chain, ranked best guess first (each candidate has a "score"). Writes nothing.

    Returns {"source": "isbn"|"title_search", "search": step, "candidates": [...], "error"?}."""
    ep = _endpoint()
    if isbn:
        isbn10, isbn13 = normalize_isbn(isbn)
        if not (isbn10 or isbn13):
            return {"source": "isbn", "candidates": [], "error": f"Not a valid ISBN: {isbn}"}
        res = ep.get_book_by_isbn(isbn13 or isbn10)
        if isinstance(res, dict) and res.get("error"):
            return {"source": "isbn", "candidates": [], "error": res["error"]}
        cand = _to_candidate(ep, (res or {}).get("book") or {})
        return {"source": "isbn", "candidates": [cand] if cand else []}
    if not title:
        return {"source": None, "candidates": [], "error": "Give an isbn or a title"}
    cands, step, errors = _title_search(ep, title, author)
    result = {"source": "title_search", "search": step, "candidates": _rank(cands, title)[:limit]}
    if errors and not cands:
        result["error"] = "; ".join(errors)
    return result


##########################################################################
# Duplicates
##########################################################################

def find_duplicates(record: dict, exclude_id: int | None = None) -> list[dict]:
    """Existing books matching the record's ISBN (either form), its title + author surname, or
    its title alone. Each match carries "match": "isbn", "title_author" or "title_only"."""
    isbns = {i for i in (record.get("IsbnNumber"), record.get("IsbnNumber13")) if i}
    surname = _surname_key(record.get("Author") or "")
    title_words = _title_words(_main_title(record.get("Title")))[:4]
    clauses, params = [], []
    if isbns:
        clauses.append("upper(regexp_replace(coalesce(IsbnNumber,''), '[^0-9Xx]', '', 'g')) = ANY(%s) "
                       "OR regexp_replace(coalesce(IsbnNumber13,''), '[^0-9]', '', 'g') = ANY(%s)")
        params += [list(isbns), list(isbns)]
    if surname:
        clauses.append("lower(Author) LIKE %s")
        params.append(f"%{surname}%")
    if title_words:
        clauses.append("Title ILIKE %s")
        params.append("%" + "%".join(title_words) + "%")
    if not clauses:
        return []
    sql = ("SELECT BookId, Title, Author, CoverType, Location, IsbnNumber, IsbnNumber13 FROM books WHERE ("
           + " OR ".join(f"({c})" for c in clauses) + ")")
    if exclude_id is not None:
        sql += " AND BookId <> %s"
        params.append(exclude_id)
    db = psycopg2.connect(**books_conf)
    try:
        with db.cursor() as c:
            c.execute(sql, params)
            rows = c.fetchall()
    finally:
        db.close()
    out = []
    for book_id, title, author, cover, location, i10, i13 in rows:
        existing = {normalize_isbn(i10)[0], normalize_isbn(i10)[1], normalize_isbn(i13)[1]} - {None}
        if existing & isbns:
            match = "isbn"
        elif not titles_match(record.get("Title"), title):
            continue
        elif surname and _surname_key(author) == surname:
            match = "title_author"
        else:
            match = "title_only"
        out.append({"BookId": book_id, "Title": title, "Author": author, "CoverType": cover,
                    "Location": location, "IsbnNumber": i10, "IsbnNumber13": i13, "match": match})
    return out


def _duplicate_status(record: dict, duplicates: list[dict]) -> tuple[str | None, str | None]:
    if any(d["match"] == "isbn" for d in duplicates):
        return "duplicate", "A book with this ISBN is already in the collection."
    same_work = [d for d in duplicates if d["match"] == "title_author"]
    if not same_work:
        return None, None
    cover = _cover_base(record.get("CoverType"))
    if not cover:
        return "duplicate", ("This title and author are already in the collection. If this is a "
                             "second copy in a different format, give its cover_type.")
    if any(_cover_base(d["CoverType"]) == cover for d in same_work):
        return "duplicate", f"This title and author are already in the collection as {cover}."
    return "confirm_second_copy", (
        "This title and author are already in the collection in a different format. Ask the user "
        "whether this is really a second acquisition; add it only with confirm_second_copy=true.")


##########################################################################
# Validation shared by add and update
##########################################################################

def _valid_locations() -> list[str]:
    """The UI's locations plus any others already in use (get_valid_locations only returns
    locations some book has, so an unused one like "Bedroom" would otherwise be rejected)."""
    in_use = []
    try:
        locations, _, _, errors = api_util.get_valid_locations()
        if not errors and locations:
            in_use = list(locations)
    except Exception as e:  # noqa: BLE001 -- fall back rather than fail the add
        app_logger.error(f"get_valid_locations failed: {e}")
    return list(KNOWN_LOCATIONS) + [loc for loc in in_use if loc not in KNOWN_LOCATIONS]


def _normalize_fields(record: dict, sources: dict, keys, warnings: list, errors: list) -> None:
    """Normalize and validate record[k] for k in keys, in place."""
    keys = set(keys)
    if "Author" in keys and record.get("Author"):
        record["Author"] = normalize_author(record["Author"])
    if "Title" in keys and record.get("Title"):
        record["Title"] = normalize_title(record["Title"])
    if "PublisherName" in keys and record.get("PublisherName"):
        record["PublisherName"] = str(record["PublisherName"]).strip(" ,;:")
    if "CopyrightDate" in keys and record.get("CopyrightDate"):
        date = Endpoint._normalize_published_date(record["CopyrightDate"])
        if date:
            record["CopyrightDate"] = date
        else:
            warnings.append(f"Ignored unusable CopyrightDate {record.pop('CopyrightDate')!r}")
            sources.pop("CopyrightDate", None)
    if "Pages" in keys and record.get("Pages") is not None:
        try:
            pages = int(record["Pages"])
            if not 0 < pages <= MAX_PAGES:
                raise ValueError
            record["Pages"] = pages
        except (TypeError, ValueError):
            warnings.append(f"Ignored unusable Pages {record.pop('Pages')!r}")
            sources.pop("Pages", None)
    if "CoverType" in keys and record.get("CoverType"):
        cover = _cover_type(record["CoverType"])
        if cover is None:
            errors.append(f"CoverType must be one of {', '.join(COVER_TYPES)}")
        else:
            record["CoverType"] = cover
    for k, limit in FIELD_LIMITS.items():
        if k in keys and record.get(k) and len(record[k]) > limit:
            warnings.append(f"{k} truncated to {limit} characters")
            record[k] = record[k][:limit].rstrip()
    if keys & {"CoverType", "Location"}:
        # Digital <=> DOWNLOAD, as in the UI's BookForm
        if record.get("CoverType") == "Digital":
            if record.get("Location") != DIGITAL_LOCATION:
                if record.get("Location"):
                    warnings.append(f"Digital books are stored at {DIGITAL_LOCATION}; "
                                    f"ignored Location {record['Location']!r}")
                record["Location"], sources["Location"] = DIGITAL_LOCATION, "default"
        elif record.get("Location") == DIGITAL_LOCATION:
            errors.append(f"{DIGITAL_LOCATION} is only for Digital books")
        elif not record.get("Location"):
            record["Location"], sources["Location"] = DEFAULT_LOCATION, "default"
        valid = _valid_locations()
        if record["Location"] not in valid:
            errors.append(f"Unknown Location {record['Location']!r}; valid: {', '.join(valid)}")
    for k in REQUIRED:
        if k in keys and not record.get(k):
            errors.append(f"{k} is required and could not be found")


##########################################################################
# Resolve
##########################################################################

def _caller_fields(fields: dict, warnings: list) -> dict:
    """Caller fields with blanks dropped and ISBNs validated (either form in either field)."""
    given = {k: _clean(fields.get(k)) for k in FIELDS}
    isbn10 = isbn13 = None
    for key in ("IsbnNumber13", "IsbnNumber"):
        if given[key]:
            i10, i13 = normalize_isbn(given[key])
            if not (i10 or i13):
                warnings.append(f"Ignored invalid ISBN {given[key]!r}")
            isbn10, isbn13 = isbn10 or i10, isbn13 or i13
    given["IsbnNumber"], given["IsbnNumber13"] = isbn10, isbn13
    return {k: v for k, v in given.items() if v is not None}


def _fill_from(record: dict, sources: dict, cand: dict, trusted: bool, warnings: list) -> None:
    """Fill record blanks from an isbndb candidate. Title gets the candidate's subtitle; author
    gains co-authors when isbndb lists more. A Digital cover is only taken when trusted (the
    caller's ISBN), so a title-search guess never moves a shelf book to DOWNLOAD."""
    if record.get("Title"):
        caller_title = normalize_title(record["Title"])
        longer = next((t for t in (full_title(caller_title, cand.get("title_long")),
                                   full_title(caller_title, cand["Title"])) if t != caller_title), None)
        if longer:
            record["Title"], sources["Title"] = longer, "caller+isbndb"
    if record.get("Author") and cand.get("Author"):
        if (_author_match(record["Author"], cand["Author"]) == "match"
                and len(split_authors(cand["Author"])) > len(split_authors(record["Author"]))):
            record["Author"], sources["Author"] = cand["Author"], "isbndb"
            warnings.append(f"Co-authors added from isbndb: {cand['Author']}")
    for k in ("Title", "Author", "CopyrightDate", "IsbnNumber", "IsbnNumber13", "PublisherName", "Pages"):
        if not record.get(k) and cand.get(k):
            record[k], sources[k] = cand[k], "isbndb"
    if not record.get("CoverType") and cand.get("CoverType"):
        if cand["CoverType"] != "Digital" or trusted:
            record["CoverType"], sources["CoverType"] = cand["CoverType"], "isbndb"
        else:
            warnings.append("isbndb's edition is digital; CoverType left blank and Location not "
                            "changed. Pass cover_type if this is a Digital book.")
    if cand.get("pages_dropped") and not record.get("Pages"):
        warnings.append(f"Ignored isbndb page count {cand['pages_dropped']} (implausibly low)")


def _choose_edition(cands: list[dict], wanted: str | None,
                    caller_author: Any) -> tuple[dict | None, list[dict], list[dict]]:
    """Pick the title-search candidate to fill from. Returns (best or None, review reasons,
    the candidates to show first -- the editions the caller should choose between)."""
    if not cands:
        return None, [{"reason": "no_match", "detail": "isbndb has no match for this title and author; "
                                                         "the record would have no ISBN, publisher or pages."}], []
    if wanted:
        pool = [c for c in cands if c.get("CoverType") == wanted]
        if not pool:
            return None, [{"reason": "edition_choice", "detail": f"No {wanted} edition found on isbndb."}], cands
    else:
        pool = [c for c in cands if c["binding_class"] == "physical"]
        if not pool:
            return None, [{"reason": "edition_choice",
                           "detail": "No physical (Hard/Soft) edition found; only digital, audio or "
                                     "unknown bindings."}], cands
    best, review = pool[0], []
    close = [c for c in pool[1:] if c["score"] >= best["score"] - CLOSE_SCORE]
    if best["score"] < MIN_CONFIDENT_SCORE:
        review.append({"reason": "edition_choice",
                       "detail": "The best matching edition looks doubtful (bundle, odd title or missing "
                                 "details); pick an isbn13."})
        pool = sorted(cands, key=lambda c: -c["score"])
    elif not wanted and any(c.get("CoverType") != best.get("CoverType") for c in pool[1:]):
        review.append({"reason": "edition_choice",
                       "detail": "Both Hard and Soft editions found; pass cover_type, or pick an isbn13."})
    elif any(c.get("PublisherName") != best.get("PublisherName") for c in close):
        review.append({"reason": "edition_choice",
                       "detail": f"{len(close) + 1} equally likely editions from different publishers; "
                                 "pick an isbn13."})
    if caller_author and _author_match(caller_author, best["Author"]) == "conflict":
        review.append({"reason": "author_conflict",
                       "detail": f"Caller author {normalize_author(caller_author)!r} but isbndb has "
                                 f"{best['Author']!r} for this title. Check the author."})
    return (None if review else best), review, pool


def resolve_book(fields: dict, lookup: bool = True) -> dict:
    """Build the best complete record from the caller's fields (DB column names; Author may be a
    list), isbndb and defaults; validate it; and check for duplicates. Writes nothing.

    Returns {"status": "ready"|"needs_review"|"duplicate"|"confirm_second_copy"|"invalid",
    "message", "record", "sources" (field -> caller|isbndb|caller+isbndb|default), "missing",
    "warnings", "errors", "review", "duplicates", "candidates", "lookup"}."""
    warnings, errors, review = [], [], []
    record = _caller_fields(fields, warnings)
    sources = {k: "caller" for k in record}
    caller_isbn = bool(record.get("IsbnNumber") or record.get("IsbnNumber13"))
    lookup_info, candidates = None, []

    if lookup and caller_isbn:
        lookup_info = lookup_metadata(isbn=record.get("IsbnNumber13") or record.get("IsbnNumber"))
        candidates = lookup_info["candidates"]
        if candidates:
            cand = candidates[0]
            if record.get("Author") and _author_match(record["Author"], cand["Author"]) != "match":
                warnings.append(f"isbndb lists {cand['Author']!r} as the author of this ISBN; "
                                f"kept the caller's {normalize_author(record['Author'])!r}.")
            _fill_from(record, sources, cand, trusted=True, warnings=warnings)
        else:
            reason = f" ({lookup_info['error']})" if lookup_info.get("error") else ""
            warnings.append(f"isbndb has no record for this ISBN{reason}; only the caller's fields are used.")
    elif lookup and record.get("Title"):
        lookup_info = lookup_metadata(title=record["Title"], author=record.get("Author"), limit=20)
        candidates = lookup_info["candidates"]
        if lookup_info.get("error"):
            warnings.append(f"isbndb lookup failed: {lookup_info['error']}")
        best, review, options = _choose_edition(candidates, _cover_type(record.get("CoverType")),
                                                record.get("Author"))
        candidates = options + [c for c in candidates if c not in options]
        if best:
            warnings.append(f"Edition chosen by isbndb title search: {candidate_summary(best)}. "
                            "Check it matches the copy in hand, or pass isbn13.")
            _fill_from(record, sources, best, trusted=False, warnings=warnings)

    _normalize_fields(record, sources, FIELDS, warnings, errors)
    if "Recycled" not in record:
        record["Recycled"], sources["Recycled"] = 0, "default"
    missing = [k for k in ("CopyrightDate", "IsbnNumber", "IsbnNumber13", "PublisherName", "CoverType", "Pages")
               if record.get(k) in (None, "")]

    duplicates = find_duplicates(record) if not errors else []
    if not caller_isbn:
        # An ISBN guessed by title search isn't proof of the same edition; let the
        # title/author format rule decide instead.
        surname = _surname_key(record.get("Author"))
        for d in duplicates:
            if d["match"] == "isbn":
                d["match"] = "title_author" if _surname_key(d["Author"]) == surname else "title_only"
    possible = [d for d in duplicates if d["match"] == "title_only"]
    if possible:
        warnings.append("Possible duplicate under a different author: " + "; ".join(
            f"BookId {d['BookId']} {d['Title']!r} by {d['Author']!r}" for d in possible))

    status, message = _duplicate_status(record, duplicates)
    # Review comes before confirm_second_copy, so confirming a second copy can't store a
    # record with a doubtful edition or author.
    if status != "duplicate" and review:
        status, message = "needs_review", ("Not ready: " + " ".join(r["detail"] for r in review)
                                           + " add_book refuses this until you pass isbn13 (from candidates) "
                                             "or accept_as_is=true to store only the given fields.")
    if errors:
        status, message = "invalid", "; ".join(errors)
    return {"status": status or "ready", "message": message or "Ready to add.", "record": record,
            "sources": sources, "missing": missing, "warnings": warnings, "errors": errors,
            "review": review, "duplicates": duplicates, "candidates": candidates, "lookup": lookup_info}


##########################################################################
# Response shaping
##########################################################################

def summarize(result: dict, verbose: bool = False) -> dict:
    """Compact form of a resolve/add/update result for MCP responses: empty lists dropped,
    duplicates trimmed, candidates as one-line summaries (top 3, only when a choice is needed).
    verbose=True returns everything, with full candidate records."""
    if verbose:
        out = {k: v for k, v in result.items() if k != "lookup"}
        out["search"] = (result.get("lookup") or {}).get("search")
        return out
    out = {k: result[k] for k in ("status", "message", "BookId", "record", "sources", "changes")
           if k in result}
    for k in ("missing", "warnings", "review"):
        if result.get(k):
            out[k] = result[k]
    if result.get("duplicates"):
        out["duplicates"] = [{k: d[k] for k in ("BookId", "Title", "Author", "CoverType", "match")}
                             for d in result["duplicates"]]
    if result.get("status") == "needs_review" and result.get("candidates"):
        out["candidates"] = [candidate_summary(c) for c in result["candidates"][:COMPACT_CANDIDATES]]
    return out


##########################################################################
# Add
##########################################################################

def insert_book_row(cursor, record: dict) -> int:
    """INSERT one books row with the caller's cursor (no commit) and return its BookId."""
    copyright_date = record.get("CopyrightDate") or None
    if copyright_date and len(str(copyright_date).strip()) == 4:
        copyright_date = f"{str(copyright_date).strip()}-01-01 00:00:00"  # make it a valid date string!
    cursor.execute(INSERT_SQL, (
        record["Title"],
        record["Author"],
        copyright_date,
        record.get("IsbnNumber") or None,
        record.get("IsbnNumber13") or None,
        record.get("PublisherName") or None,
        record.get("CoverType") or None,
        record.get("Pages") or None,
        record["Location"],
        record.get("BookNote") or None,
        record.get("Recycled", 0),
    ))
    return cursor.fetchone()[0]


def _embed_book_note(db, book_id: int, note: str | None) -> None:
    if note and note.strip():
        try:
            api_util.upsert_book_note_embedding(db, book_id, note.strip())
        except Exception as e:  # noqa: BLE001 -- the book is saved; the index can be rebuilt
            app_logger.error(f"book_note embed failed for BookId={book_id}: {e}")


def add_book_record(record: dict) -> int:
    """Insert one book, commit, and index its BookNote for RAG search. Returns the BookId."""
    db = psycopg2.connect(**books_conf)
    try:
        with db.cursor() as c:
            book_id = insert_book_row(c, record)
        db.commit()
        _embed_book_note(db, book_id, record.get("BookNote"))
    finally:
        db.close()
    return book_id


def add_book(fields: dict, confirm_second_copy: bool = False, accept_as_is: bool = False) -> dict:
    """resolve_book(), then insert unless the book is invalid, redundant or needs review.

    - "confirm_second_copy" is inserted only with confirm_second_copy=True.
    - accept_as_is=True skips the isbndb lookup and stores only the caller's fields (plus
      defaults) -- for a "needs_review" book the caller has checked, or one isbndb can't find.
    On success adds "BookId" and sets status "added"; otherwise nothing is written."""
    result = resolve_book(fields, lookup=not accept_as_is)
    if result["status"] == "ready" or (result["status"] == "confirm_second_copy" and confirm_second_copy):
        result["BookId"] = add_book_record(result["record"])
        result["status"], result["message"] = "added", f"Added as BookId {result['BookId']}."
    return result


def _batch_error(items: Any) -> str | None:
    if not isinstance(items, list) or not items:
        return "items must be a non-empty list"
    if len(items) > MAX_BATCH:
        return f"At most {MAX_BATCH} items per call; got {len(items)}"
    return None


def _batch_row(i: int, result: dict) -> dict:
    rec = result.get("record") or {}
    row = {"item": i, "status": result["status"], "Title": rec.get("Title"), "Author": rec.get("Author"),
           "IsbnNumber13": rec.get("IsbnNumber13"), "CoverType": rec.get("CoverType"),
           "Location": rec.get("Location")}
    if result.get("BookId"):
        row["BookId"] = result["BookId"]
    if result["status"] not in ("ready", "added"):
        row["message"] = result["message"]
    for k in ("warnings", "missing"):
        if result.get(k):
            row[k] = list(result[k])
    if result.get("duplicates"):
        row["duplicates"] = [f"{d['BookId']} ({d['match']}, {d['CoverType'] or '?'})" for d in result["duplicates"]]
    if result["status"] == "needs_review" and result.get("candidates"):
        row["candidates"] = [candidate_summary(c) for c in result["candidates"][:COMPACT_CANDIDATES]]
    return row


def _count_by(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def check_books(items: list[dict]) -> dict:
    """resolve_book() for up to MAX_BATCH items (DB-column dicts); one compact row each. Also
    flags items that repeat an earlier item in the same batch."""
    err = _batch_error(items)
    if err:
        return {"error": err}
    rows, seen = [], []
    for i, fields in enumerate(items):
        result = resolve_book(fields)
        row = _batch_row(i, result)
        rec = result["record"]
        for j, prev in seen:
            same_isbn = rec.get("IsbnNumber13") and rec.get("IsbnNumber13") == prev.get("IsbnNumber13")
            same_work = (titles_match(rec.get("Title"), prev.get("Title"))
                         and _surname_key(rec.get("Author")) == _surname_key(prev.get("Author")))
            if same_isbn or same_work:
                row.setdefault("warnings", []).append(f"Same book as item {j} in this batch")
        seen.append((i, rec))
        rows.append(row)
    return {"count": len(rows), "by_status": _count_by(rows), "items": rows}


def add_books(items: list[dict]) -> dict:
    """add_book() for up to MAX_BATCH items, each added or refused on its own. Items may carry
    "confirm_second_copy" / "accept_as_is" flags. Earlier items are in the collection by the
    time later ones are checked, so a repeated item comes back "duplicate"."""
    err = _batch_error(items)
    if err:
        return {"error": err}
    rows = []
    for i, fields in enumerate(items):
        fields = dict(fields)
        flags = {k: bool(fields.pop(k, False)) for k in ("confirm_second_copy", "accept_as_is")}
        try:
            rows.append(_batch_row(i, add_book(fields, **flags)))
        except Exception as e:  # noqa: BLE001 -- report and carry on with the rest of the batch
            app_logger.error(f"add_books item {i} failed: {e}")
            rows.append({"item": i, "status": "error", "message": str(e)})
    return {"count": len(rows), "by_status": _count_by(rows), "items": rows}


##########################################################################
# Update
##########################################################################

def _get_book_row(book_id: int) -> dict | None:
    db = psycopg2.connect(**books_conf)
    try:
        with db.cursor() as c:
            c.execute(f"SELECT {', '.join(FIELDS)} FROM books WHERE BookId = %s", (book_id,))
            row = c.fetchone()
    finally:
        db.close()
    if row is None:
        return None
    rec = dict(zip(FIELDS, row))
    if hasattr(rec.get("CopyrightDate"), "strftime"):
        rec["CopyrightDate"] = rec["CopyrightDate"].strftime("%Y-%m-%d")
    return rec


def update_book(book_id: int, fields: dict, dry_run: bool = False) -> dict:
    """Correct an existing book. fields uses DB column names; None means "leave as is" and ""
    clears an optional field. Changed fields get the same normalization and validation as
    add_book (unchanged ones are left alone), a changed ISBN is checked against other books,
    and the result shows before/after for each change. dry_run=True writes nothing."""
    current = _get_book_row(book_id)
    if current is None:
        return {"status": "invalid", "message": f"No book with BookId {book_id}", "BookId": book_id}
    changes = {k: v for k, v in fields.items() if k in FIELDS and v is not None}
    if not changes:
        return {"status": "invalid", "message": "Nothing to change", "BookId": book_id}
    warnings, errors = [], []
    record = dict(current)
    record.update({k: _clean(v) for k, v in changes.items()})
    isbn_value = next((record[k] for k in ("IsbnNumber13", "IsbnNumber") if k in changes and record.get(k)), None)
    if isbn_value:
        i10, i13 = normalize_isbn(isbn_value)
        if i10 or i13:
            record["IsbnNumber"], record["IsbnNumber13"] = i10, i13
        else:
            errors.append(f"Invalid ISBN {isbn_value!r}")
    sources = {k: "caller" for k in changes}
    _normalize_fields(record, sources, changes.keys(), warnings, errors)
    if not errors and isbn_value:
        clash = [d for d in find_duplicates(record, exclude_id=book_id) if d["match"] == "isbn"]
        if clash:
            errors.append("Another book already has this ISBN: " + ", ".join(str(d["BookId"]) for d in clash))
    diff = {k: {"before": current.get(k), "after": record.get(k)}
            for k in FIELDS if record.get(k) != current.get(k)}
    result = {"BookId": book_id, "changes": diff, "warnings": warnings}
    if errors:
        return result | {"status": "invalid", "message": "; ".join(errors)}
    if not diff:
        return result | {"status": "unchanged", "message": "No differences from the stored record."}
    if dry_run:
        return result | {"status": "dry_run", "message": "Nothing written; call again without dry_run to save."}
    db = psycopg2.connect(**books_conf)
    try:
        with db.cursor() as c:
            c.execute(f"UPDATE books SET {', '.join(f'{k} = %s' for k in diff)} WHERE BookId = %s",
                      [record[k] for k in diff] + [book_id])
        db.commit()
        if "BookNote" in diff:
            _embed_book_note(db, book_id, record.get("BookNote"))
    finally:
        db.close()
    return result | {"status": "updated", "message": f"Updated BookId {book_id}."}


def list_locations() -> dict:
    return {"locations": _valid_locations(),
            "rules": f"Digital books are always stored at {DIGITAL_LOCATION}, and {DIGITAL_LOCATION} "
                     f"is only for Digital books. Default for new books: {DEFAULT_LOCATION}."}
