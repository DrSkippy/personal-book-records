"""
API Utility Module for Books Database.

This module provides database access functions for the books collection.
It imports from sub-modules for configuration and serialization.
"""
import datetime
import numpy as np
import pymysql

# Import from sub-modules for modular organization
from .config import (
    app_logger,
    table_header,
    locations_sort_order,
    FMT,
    API_KEY,
    read_json_configuration,
    books_conf,
    isbn_conf,
)
from .serialization import (
    sort_list_by_index_list,
    serialized_result_dict,
    _convert_db_types,
    _create_serializeable_result_dict,
)

# Re-export for backward compatibility - consumers can still use:
#   from booksdb.api_util import API_KEY, books_conf, etc.
__all__ = [
    # Config exports
    'app_logger', 'table_header', 'locations_sort_order', 'FMT',
    'API_KEY', 'read_json_configuration', 'books_conf', 'isbn_conf',
    # Serialization exports
    'sort_list_by_index_list', 'serialized_result_dict',
    '_convert_db_types', '_create_serializeable_result_dict',
    # Functions defined in this module
    'get_valid_locations', 'get_recently_touched', 'get_next_book_id',
    'get_book_ids_in_window', 'get_complete_book_record',
    'update_book_record_by_key', 'summary_books_read_by_year_utility',
    'books_read_by_year_utility', 'status_read_utility',
    'tags_search_utility', 'books_search_utility', 'book_tags',
    'get_tag_counts', 'add_tag_to_book', 'get_images_for_book',
    'daily_page_record_from_db', 'reading_book_data_from_db',
    'update_reading_book_data', 'estimate_completion_dates',
    'calculate_estimates',
]


##########################################################################
# BASIC API UTILITIES
##########################################################################

def get_valid_locations():
    """
    Retrieves a sorted list of distinct locations from the book collection table.

    The function connects to the MySQL database, executes a query to obtain unique
    location values, and returns them in a sorted order according to a predefined
    sort index. It also provides the raw query results and a list of column names,
    along with any error messages that may have occurred during the database
    operation.

    Args:
        None

    Returns:
        tuple[list[str], tuple[tuple[str, ...], ...], list[str], list[str] | None]
            A 4‑tuple containing:
            - ``sorted_locations_list`` – the locations sorted according to
              ``locations_sort_order``.
            - ``locations`` – the raw ``SELECT`` result set as returned by
              ``fetchall()``.
            - ``["Location"]`` – a single‑element list of column names.
            - ``error_list`` – a list containing the string representation of any
              database error that was caught, or ``None`` if no error occurred.
    """
    db = None
    error_list = None
    try:
        db = pymysql.connect(**books_conf)
        cursor = db.cursor()

        # Execute the query
        query = "SELECT DISTINCT Location FROM `book collection` ORDER by Location ASC;"
        app_logger.debug(query)
        cursor.execute(query)

        # Fetch and process the results
        locations = cursor.fetchall()
        locations_list = [loc[0] for loc in locations]
        sorted_locations_list = sort_list_by_index_list(locations_list, locations_sort_order)
    except pymysql.Error as e:
        # Log and handle database errors
        app_logger.error(e)
        error_list = [str(e)]
    finally:
        # Ensure the database connection is closed
        if db:
            db.close()
    return sorted_locations_list, locations, ["Location"], error_list


def get_recently_touched(limit=10):
    """
    Retrieve a list of recently touched book collections.

    This function queries the database to find the most recently updated
    book collections, combining data from several tables.  It returns the
    results together with the raw database rows, a header describing the
    columns, and any error messages that occurred during execution.

    Parameters
    ----------
    limit : int, optional
        The maximum number of records to return. Defaults to 10.

    Returns
    -------
    tuple
        A 4‑tuple containing:

        * recent_books (list[list]): A list where each element is a list of
          three items: ``BookCollectionID`` (int), ``LastUpdate`` (str or
          None), and ``Title`` (str). ``LastUpdate`` is formatted according
          to the global ``FMT`` constant; titles longer than 43 characters
          are truncated to 40 characters followed by ellipsis.

        * s (tuple): The raw rows returned by the cursor's ``fetchall``.
          Each row is a tuple of the original column values.

        * header (list[str]): A list of column names used for the result
          set: ``["BookCollectionID", "LastUpdate", "Title"]``.

        * error_list (list[str] | None): A list containing a single error
          message if a ``pymysql.Error`` was raised; otherwise ``None``.

    Raises
    ------
    None
    """
    error_list = None
    db = None
    recent_books = []
    header = ["BookCollectionID", "LastUpdate", "Title"]
    s = None

    try:
        db = pymysql.connect(**books_conf)
        cursor = db.cursor()

        # Execute the query - get most recently touched books from all tables
        query = ('SELECT abc.BookCollectionID, max(abc.LastUpdate) as LastUpdate, bc.Title FROM\n'
                 '(       SELECT BookCollectionID, LastUpdate \n'
                 '        FROM `book collection`\n'
                 '        UNION \n'
                 '        SELECT BookID as BookCollectionID, LastUpdate\n'
                 '        FROM `books tags`\n'
                 '        UNION\n'
                 '        SELECT a.BookCollectionID, b.LastUpdate\n'
                 '        FROM `complete date estimates` a JOIN `daily page records` b ON\n'
                 '        a.RecordID = b.RecordID\n'
                 '        UNION \n'
                 '        SELECT BookCollectionID, EstimateDate as LastUpdate\n'
                 '        FROM `complete date estimates`\n'
                 '        UNION \n'
                 '        SELECT BookCollectionID, LastUpdated as LastUpdate\n'
                 '        FROM `images`\n'
                 ') abc\n'
                 'JOIN `book collection` bc ON abc.BookCollectionID = bc.BookCollectionID \n'
                 'GROUP BY abc.BookCollectionID, bc.Title\n'
                 'ORDER BY LastUpdate DESC LIMIT %s;\n')
        app_logger.debug(query)
        cursor.execute(query, (limit,))

        # Fetch and process the results
        s = cursor.fetchall()
        for a, b, c in s:
            _date = b.strftime(FMT) if b else None
            _title = c if len(c) <= 43 else c[:40] + "..."
            recent_books.append([a, _date, _title])

    except pymysql.Error as e:
        # Log and handle database errors
        app_logger.error(e)
        error_list = [str(e)]
    finally:
        # Ensure the database connection is closed
        if db:
            db.close()

    return recent_books, s, header, error_list


##########################################################################
# BOOKS WINDOW
##########################################################################

def get_next_book_id(current_book_id, direction=1):
    """
    Gets the next book collection ID in the database.

    Summary:
        Retrieves the next BookCollectionID from the `book collection` table in
        the MySQL database. The function uses the current ID and a direction
        flag to determine whether to look forward or backward. When the search
        reaches the end of the table it wraps around to the first or last
        entry, depending on the direction.

    Parameters:
        current_book_id (int): The current book collection identifier.
        direction (int, optional): A positive value indicates forward
            searching; a negative value indicates backward searching.
            Defaults to 1.

    Returns:
        int or None: The next book collection ID, or None if a database
        error occurs.

    Raises:
        pymysql.Error: If an error occurs during the database query.
    """
    db = pymysql.connect(**books_conf)
    # Direction determines comparison operator and sort order (safe - derived from int)
    if direction > 0:
        query_str = ("SELECT a.BookCollectionID FROM `book collection` as a "
                     "WHERE a.BookCollectionID > %s ORDER BY a.BookCollectionID ASC LIMIT 1")
    else:
        query_str = ("SELECT a.BookCollectionID FROM `book collection` as a "
                     "WHERE a.BookCollectionID < %s ORDER BY a.BookCollectionID DESC LIMIT 1")
    app_logger.debug(query_str)
    next_book_id = None
    c = db.cursor()
    try:
        c.execute(query_str, (current_book_id,))
    except pymysql.Error as e:
        app_logger.error(e)
        return next_book_id
    else:
        s = c.fetchall()
        # If no results, wrap around
        if len(s) == 0:
            if direction > 0:
                # get the first record
                next_book_id = 2
            else:
                query_str = "SELECT max(a.BookCollectionID) FROM `book collection` as a"
                c = db.cursor()
                try:
                    c.execute(query_str)
                except pymysql.Error as e:
                    app_logger.error(e)
                else:
                    s = c.fetchall()
                    next_book_id = s[0][0]
        else:
            next_book_id = s[0][0]
        return next_book_id


def get_book_ids_in_window(book_id, window):
    """
    Get a list of book IDs within a given window around a specific book ID.

    This function connects to a MySQL database and retrieves a contiguous block of
    book IDs that surrounds the supplied `book_id`. The window is divided into a
    top and bottom half.  If the requested range extends beyond the existing
    records, the function wraps around to the beginning or end of the collection
    to fill the deficit, ensuring the returned list has exactly `window`
    entries.

    Parameters
    ----------
    book_id : int
        The ID of the book around which the window is calculated.
    window : int
        The total number of book IDs to return, including the supplied
        `book_id`.

    Returns
    -------
    list[int]
        A list of book IDs ordered such that the supplied `book_id` is
        positioned near the center of the list.  The list length is equal to
        `window`.  If the underlying collection contains fewer records
        than requested, duplicates are inserted to satisfy the size.

    Raises
    ------
    pymysql.Error
        If a database query fails, the exception is logged but not
        propagated; the function continues with whatever results were
        retrieved so far.
    """
    db = pymysql.connect(**books_conf)
    app_logger.debug(f"Getting book ID window for book ID {book_id} with window {window}")
    top_half_window = int((window + 1) / 2)
    bottom_half_window = window - top_half_window

    # Query templates with parameterized book_id and limit
    # Comparison operator and order are safe (hardcoded strings)
    queries = {
        "le_desc": "SELECT a.BookCollectionID FROM `book collection` as a WHERE a.BookCollectionID <= %s ORDER BY a.BookCollectionID DESC LIMIT %s",
        "gt_desc": "SELECT a.BookCollectionID FROM `book collection` as a WHERE a.BookCollectionID > %s ORDER BY a.BookCollectionID DESC LIMIT %s",
        "gt_asc": "SELECT a.BookCollectionID FROM `book collection` as a WHERE a.BookCollectionID > %s ORDER BY a.BookCollectionID ASC LIMIT %s",
        "le_asc": "SELECT a.BookCollectionID FROM `book collection` as a WHERE a.BookCollectionID <= %s ORDER BY a.BookCollectionID ASC LIMIT %s",
    }

    c = db.cursor()
    book_id_list = []

    # get the bottom half first - window leading up to book_id
    try:
        c.execute(queries["le_desc"], (book_id, bottom_half_window))
        s = c.fetchall()
        for row in s:
            book_id_list.append(row[0])
        book_id_list.reverse()
    except pymysql.Error as e:
        app_logger.error(e)

    if len(book_id_list) < bottom_half_window:
        # Make a ring of ideas - get some from the end of book records
        deficit = bottom_half_window - len(book_id_list)
        try:
            c.execute(queries["gt_desc"], (book_id, deficit))
            s = c.fetchall()
            for row in s:
                book_id_list.insert(0, row[0])
        except pymysql.Error as e:
            app_logger.error(e)

    # now get the top half - window after book_id
    try:
        c.execute(queries["gt_asc"], (book_id, top_half_window))
        s = c.fetchall()
        for row in s:
            book_id_list.append(row[0])
    except pymysql.Error as e:
        app_logger.error(e)

    if len(book_id_list) < window:
        # Make a ring of ideas - get some from the start of book records
        deficit = window - len(book_id_list)
        try:
            c.execute(queries["le_asc"], (book_id, deficit))
            s = c.fetchall()
            for row in s:
                book_id_list.append(row[0])
        except pymysql.Error as e:
            app_logger.error(e)

    return book_id_list


def get_complete_book_record(book_id):
    """Retrieve complete book record including reads, tags, and images."""
    db = pymysql.connect(**books_conf)

    q_book = ("SELECT a.BookCollectionID, a.Title, a.Author, a.CopyrightDate, "
              "a.ISBNNumber, a.PublisherName, a.CoverType, a.Pages, "
              "a.Category, a.Note, a.Recycled, a.Location, a.ISBNNumber13 "
              "FROM `book collection` as a WHERE a.BookCollectionID = %s")
    h_book = table_header

    q_read = "SELECT b.ReadDate, b.ReadNote FROM `books read` as b WHERE b.BookCollectionID = %s"
    h_read = ["DateRead", "ReadNote"]

    q_tags = ("SELECT b.Label FROM `books tags` as a JOIN `tag labels` as b "
              "ON b.TagID = a.TagID WHERE a.BookID = %s")
    h_tags = ["Tag"]

    q_img = ("SELECT a.url FROM `images` as a "
             "WHERE a.BookCollectionID = %s AND a.type = 'cover-face'")
    h_img = ["ImageURL"]

    result_data = {"book": None, "reads": None, "tags": None, "img": None, "error": []}
    c = db.cursor()

    try:
        c.execute(q_book, (book_id,))
        s = c.fetchall()
        result_data["book"] = _create_serializeable_result_dict(s, h_book)
    except pymysql.Error as e:
        app_logger.error(e)
        result_data["error"].append(str(e))

    try:
        c.execute(q_read, (book_id,))
        s = c.fetchall()
        result_data["reads"] = _create_serializeable_result_dict(s, h_read)
    except pymysql.Error as e:
        app_logger.error(e)
        result_data["error"].append(str(e))

    try:
        c.execute(q_tags, (book_id,))
        s = c.fetchall()
        result_data["tags"] = _create_serializeable_result_dict([[x[0] for x in s]], h_tags)
    except pymysql.Error as e:
        app_logger.error(e)
        result_data["error"].append(str(e))

    try:
        c.execute(q_img, (book_id,))
        s = c.fetchall()
        result_data["img"] = _create_serializeable_result_dict([[x[0] for x in s]], h_img)
    except pymysql.Error as e:
        app_logger.error(e)
        result_data["error"].append(str(e))

    if len(result_data["error"]) == 0:
        del result_data["error"]
    return result_data


##########################################################################
# UPDATE BOOKS
##########################################################################

def update_book_record_by_key(update_dict):
    """
    Updates a book record in the database using the provided dictionary of record
    values and the corresponding `BookCollectionID`. Key-value pairs in the record
    represent the columns to update and their new values. If an error occurs while
    executing the SQL operation, an error dictionary will be returned.

    :param update_dict: A dictionary containing the record information for the book to
        be updated. The keys represent the column names, and the values represent
        the new data to be inserted for those columns.
    :type update_dict: dict
    :return: A list containing the result of the update operation. If successful,
        the `record` dictionary is returned; otherwise, an error dictionary is
        returned.
    :rtype: list
    """
    # Allowed column names for update (whitelist to prevent SQL injection)
    allowed_columns = {
        "Title", "Author", "CopyrightDate", "ISBNNumber", "ISBNNumber13",
        "PublisherName", "CoverType", "Pages", "Category", "Note",
        "Recycled", "Location"
    }

    db = pymysql.connect(**books_conf)
    book_collection_id = update_dict.get("BookCollectionID")
    if not book_collection_id:
        return [{"error": "BookCollectionID is required"}]

    # Build SET clause with parameterized values
    set_parts = []
    values = []
    for key, value in update_dict.items():
        if key == "BookCollectionID":
            continue
        if key not in allowed_columns:
            app_logger.warning(f"Ignoring unknown column: {key}")
            continue
        set_parts.append(f"`{key}` = %s")
        values.append(value)

    if not set_parts:
        return [{"error": "No valid columns to update"}]

    values.append(book_collection_id)
    search_str = f"UPDATE `book collection` SET {', '.join(set_parts)} WHERE BookCollectionID = %s"
    app_logger.debug(search_str)

    results = []
    with db:
        with db.cursor() as c:
            try:
                c.execute(search_str, tuple(values))
                results.append(update_dict)
            except pymysql.Error as e:
                app_logger.error(e)
                results.append({"error": str(e)})
        db.commit()
    return results


##########################################################################
# REPORTS
##########################################################################

def summary_books_read_by_year_utility(target_year=None):
    """
    Summarizes the number of pages read and books read each year.
    Can be filtered for a specific year.

    Parameters:
    target_year (int, optional): The year for which the summary is required. Defaults to None.

    Returns:
    tuple: A tuple containing the serialized result, raw data, and header.
    """
    error_list = None
    db = pymysql.connect(**books_conf)
    cursor = db.cursor()

    # Build query with optional year filter
    params = ()
    if target_year is not None:
        query = (
            "SELECT YEAR(b.ReadDate) as Year, SUM(a.Pages) as Pages, COUNT(a.Pages) as Books "
            "FROM `book collection` as a JOIN `books read` as b "
            "ON a.BookCollectionID = b.BookCollectionID "
            "WHERE b.ReadDate is not NULL AND YEAR(b.ReadDate) = %s "
            "GROUP BY Year ORDER BY Year ASC"
        )
        params = (target_year,)
    else:
        query = (
            "SELECT YEAR(b.ReadDate) as Year, SUM(a.Pages) as Pages, COUNT(a.Pages) as Books "
            "FROM `book collection` as a JOIN `books read` as b "
            "ON a.BookCollectionID = b.BookCollectionID "
            "WHERE b.ReadDate is not NULL "
            "GROUP BY Year ORDER BY Year ASC"
        )

    headers = ["year", "pages read", "books read"]
    app_logger.debug(query)

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
        results = None
    finally:
        db.close()

    return results, headers, error_list


def books_read_by_year_utility(target_year=None):
    """
    Retrieves books that have been read from the database, optionally filtered by a
    specific year.

    This function connects to a MySQL database using the connection parameters
    defined in ``books_conf``. It builds a SQL query that joins the
    ``book collection`` table with the ``books read`` table to fetch details for
    every book that has a non‑null ``ReadDate``.  If ``target_year`` is supplied,
    the query is restricted to entries whose ``ReadDate`` falls within that
    year.  The result set is returned together with a header list that
    contains column names and any error messages that occurred during query
    execution.

    Parameters
    ----------
    target_year : int, optional
        When supplied, only books whose ``ReadDate`` year matches
        ``target_year`` are returned.  If ``None`` (the default), all
        records with a non‑null ``ReadDate`` are included.

    Returns
    -------
    tuple
        * ``rows`` – A sequence of tuples, each representing a record
          returned by the query.  ``None`` if the query failed.
        * ``rows`` – The same sequence of tuples as the first element; kept
          for backward compatibility.
        * ``header`` – A list of column names for the result set.
        * ``error_list`` – A list containing an error message string if a
          database error was raised, otherwise ``None``.

    Raises
    ------
    pymysql.Error
        If the SQL execution fails, the exception is logged and the error
        message is stored in ``error_list``; the exception itself is not
        propagated.

    Notes
    -----
    The function logs the executed query using ``app_logger.debug``.  It is
    intended for internal use by other modules that require a list of books
    that have been read, possibly grouped by year.  The returned ``rows`` can
    be passed directly to functions that format the data for presentation
    or further analysis.
    """
    error_list = None
    db = pymysql.connect(**books_conf)

    params = ()
    if target_year is not None:
        search_str = ("SELECT a.BookCollectionID, a.Title, a.Author, a.CopyrightDate, "
                      "a.ISBNNumber, a.PublisherName, a.CoverType, a.Pages, "
                      "a.Category, a.Note, a.Recycled, a.Location, a.ISBNNumber13, "
                      "b.ReadDate "
                      "FROM `book collection` as a JOIN `books read` as b "
                      "ON a.BookCollectionID = b.BookCollectionID "
                      "WHERE b.ReadDate is not NULL AND YEAR(b.ReadDate) = %s "
                      "ORDER BY b.ReadDate, a.BookCollectionID ASC")
        params = (target_year,)
    else:
        search_str = ("SELECT a.BookCollectionID, a.Title, a.Author, a.CopyrightDate, "
                      "a.ISBNNumber, a.PublisherName, a.CoverType, a.Pages, "
                      "a.Category, a.Note, a.Recycled, a.Location, a.ISBNNumber13, "
                      "b.ReadDate "
                      "FROM `book collection` as a JOIN `books read` as b "
                      "ON a.BookCollectionID = b.BookCollectionID "
                      "WHERE b.ReadDate is not NULL "
                      "ORDER BY b.ReadDate, a.BookCollectionID ASC")

    header = table_header + ["ReadDate"]
    app_logger.debug(search_str)
    s = None
    c = db.cursor()
    try:
        c.execute(search_str, params)
        s = c.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    return s, header, error_list


def status_read_utility(book_id):
    """
    Retrieve the read status for a specified book from the database.

    Args:
        book_id (int): The ID of the book to query.

    Returns:
        tuple: A 4‑tuple with the following items:
            - s (list): The rows fetched from the query.
            - s (list): The same list of rows (duplicated in the original implementation).
            - header (list): The column names of the result set.
            - error_list (list or None): A list containing any error messages that
              occurred during execution, or ``None`` if the query succeeded.

    Notes:
        This function opens a connection to the MySQL database using the global
        ``books_conf`` configuration. It logs the SQL query for debugging purposes,
        executes the query, and captures any ``pymysql.Error`` exceptions.
        The database cursor is not closed explicitly; it relies on garbage
        collection for cleanup.
    """
    error_list = None
    db = pymysql.connect(**books_conf)
    search_str = ("SELECT BookCollectionID, ReadDate, ReadNote "
                  "FROM `books read` "
                  "WHERE BookCollectionID = %s ORDER BY ReadDate ASC")
    app_logger.debug(search_str)
    c = db.cursor()
    header = ["BookCollectionID", "ReadDate", "ReadNote"]
    s = None
    try:
        c.execute(search_str, (book_id,))
        s = c.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    return s, header, error_list


def tags_search_utility(match_str):
    """
    Search for book tags that match the given string.

    Parameters
    ----------
    match_str : str
        The substring used to search tag labels.  The value is converted to lower case,
        stripped of surrounding whitespace, and embedded in a SQL LIKE pattern.

    Returns
    -------
    tuple
        A tuple containing four elements:

        1. A list of rows returned by the database query.  Each row is a tuple of
           (BookID, TagID, Tag).
        2. A duplicate reference to the same list of rows (kept for backward
           compatibility).
        3. A list of column header names: ['BookCollectionID', 'TagID', 'Tag'].
        4. Either None if the query succeeded, or a list of error message strings
           collected from a pymysql.Error exception.
    """
    match_str = match_str.lower().strip()
    error_list = None
    db = pymysql.connect(**books_conf)
    search_str = ("SELECT a.BookID, b.TagID, b.Label as Tag"
                  " FROM `books tags` a JOIN `tag labels` b ON a.TagID=b.TagID"
                  " WHERE b.Label LIKE %s"
                  " ORDER BY b.Label ASC")
    header = ["BookCollectionID", "TagID", "Tag"]
    app_logger.debug(search_str)
    c = db.cursor()
    s = None
    try:
        c.execute(search_str, (f"%{match_str}%",))
        s = c.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    return s, header, error_list


def books_search_utility(args):
    """
    This function searches a book collection database for records matching the provided criteria.

    The function builds a SQL query dynamically based on the keys in the `args` dictionary.  Certain keys are treated specially – for example, a key of `"BookCollectionID"` is matched exactly, while `"ReadDate"` is matched using a `LIKE` pattern.  The `"Tags"` key triggers a call to `tags_search_utility`, converting a list of tag identifiers into a tuple used in a sub‑query.  All other keys are compared using a `LIKE` clause.

    The query joins the `book collection` table with the `books read` table.  If any conditions are supplied, they are added to a `WHERE` clause; the results are ordered by author and title.  The function logs the final query for debugging purposes.

    After executing the query, the function fetches all rows and returns them along with a header list and any error information that may have been captured.

    Parameters
    ----------
    args : dict
        A dictionary of search criteria.  Keys correspond to column names in the
        book collection tables.  The following keys are handled specially:

        * ``BookCollectionID`` – exact match on the collection ID.
        * ``ReadDate`` – matched using a ``LIKE`` pattern.
        * ``Tags`` – the value is passed to ``tags_search_utility``; the resulting
          tag IDs are used to filter the collection IDs.
        * All other keys – matched using a ``LIKE`` pattern against the column
          of the same name in the ``book collection`` table.

    Returns
    -------
    tuple
        A four‑tuple containing:

        * ``s`` – the list of rows returned by the database query (each row is a
          tuple of column values).
        * ``s`` – the same list of rows returned again (this duplication is
          intentional to match the original return signature).
        * ``header`` – a list of column names for the result set, including the
          ``ReadDate`` column appended to the global ``table_header``.
        * ``error_list`` – a list containing any database error messages that
          occurred during query execution, or ``None`` if no errors were
          encountered.

    Notes
    -----
    * The function relies on several global objects: ``books_conf`` for the
      database connection parameters, ``tags_search_utility`` for resolving tag
      IDs, ``app_logger`` for logging, and ``table_header`` for header
      construction.  These objects must be defined in the module before calling
      this function.

    * Because the query is built by interpolating values directly into the SQL
      string, it is susceptible to SQL injection if ``args`` contains untrusted
      data.  Ensure that all values in ``args`` are sanitized before use.

    * The returned list of rows is fetched using the ``fetchall`` method of a
      MySQL cursor, which yields a list of tuples.  The column order matches the
      selection in the query string.
    """
    # Allowed search columns (whitelist to prevent SQL injection)
    allowed_book_columns = {
        "BookCollectionID", "Title", "Author", "CopyrightDate", "ISBNNumber",
        "ISBNNumber13", "PublisherName", "CoverType", "Pages", "Category",
        "Note", "Recycled", "Location"
    }

    error_list = None
    s = None
    db = pymysql.connect(**books_conf)
    where_parts = []
    params = []

    for key in args:
        value = args.get(key)
        if key == "BookCollectionID":
            where_parts.append("a.BookCollectionID = %s")
            params.append(value)
        elif key == "ReadDate":
            where_parts.append("b.ReadDate LIKE %s")
            params.append(f"%{value}%")
        elif key == "Tags":
            # Get book IDs matching the tag
            tag_results, _, _ = tags_search_utility(value)
            if tag_results:
                book_ids = [int(x[0]) for x in tag_results]
                placeholders = ", ".join(["%s"] * len(book_ids))
                where_parts.append(f"a.BookCollectionID IN ({placeholders})")
                params.extend(book_ids)
            else:
                # No matching tags - force no results
                where_parts.append("a.BookCollectionID IN (0)")
        elif key in allowed_book_columns:
            where_parts.append(f"a.`{key}` LIKE %s")
            params.append(f"%{value}%")
        else:
            app_logger.warning(f"Ignoring unknown search column: {key}")

    search_str = ("SELECT a.BookCollectionID, a.Title, a.Author, a.CopyrightDate, "
                  "a.ISBNNumber, a.PublisherName, a.CoverType, a.Pages, "
                  "a.Category, a.Note, a.Recycled, a.Location, a.ISBNNumber13, "
                  "b.ReadDate "
                  "FROM `book collection` as a LEFT JOIN `books read` as b "
                  "ON a.BookCollectionID = b.BookCollectionID")
    if where_parts:
        search_str += " WHERE " + " AND ".join(where_parts)
    search_str += " ORDER BY a.Author, a.Title ASC"

    app_logger.debug(search_str)
    header = table_header + ["ReadDate"]
    c = db.cursor()
    try:
        c.execute(search_str, tuple(params))
        s = c.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    return s, header, error_list


def book_tags(book_id):
    """
    Retrieve tag labels for a specified book from the database.

    Parameters
    ----------
    book_id : int
        The unique identifier of the book for which tag labels are to be retrieved.

    Returns
    -------
    tuple
        A tuple containing two elements:
        1. A dictionary with keys ``"BookID"`` and ``"tag_list"``, where ``"tag_list"``
           holds a list of tag label strings associated with the book.
        2. A list of error messages or ``None`` if no errors occurred during the query.

    Raises
    ------
    None
        The function handles database errors internally and does not propagate
        exceptions to the caller.
    """
    error_list = None
    s = None
    db = pymysql.connect(**books_conf)
    search_str = "SELECT a.Label as Tag"
    search_str += " FROM `tag labels` a JOIN `books tags` b ON a.TagID = b.TagID"
    search_str += " WHERE b.BookID = %s ORDER BY Tag"
    app_logger.debug(search_str)
    c = db.cursor()
    try:
        c.execute(search_str, (book_id,))
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    else:
        s = c.fetchall()
        tag_list = [x[0].strip() for x in s]
        rdata = {"BookID": book_id, "tag_list": tag_list}
    return rdata, error_list


def get_tag_counts(tag_prefix=None):
    """
    Retrieve tag count information from the database.

    Parameters
    ----------
    tag_prefix : str or None
        Optional tag prefix to filter results. If provided, only tags
        starting with this prefix are returned.

    Returns
    -------
    tuple
        A tuple containing:
        1. rows - List of (Tag, Count) tuples
        2. header - List of column names ["Tag", "Count"]
        3. error_list - List of error messages or None if successful
    """
    db = pymysql.connect(**books_conf)
    search_str = "SELECT a.Label as Tag, COUNT(b.TagID) as Count"
    search_str += " FROM `tag labels` a JOIN `books tags` b ON a.TagID = b.TagID"
    params = ()
    if tag_prefix is not None:
        search_str += " WHERE Label LIKE %s"
        params = (f"{tag_prefix}%",)
    search_str += " GROUP BY Label ORDER BY Count DESC, Label ASC"
    app_logger.debug(search_str)
    header = ["Tag", "Count"]
    error_list = None
    rows = []
    c = db.cursor()
    try:
        c.execute(search_str, params)
        rows = c.fetchall()
    except pymysql.Error as e:
        app_logger.error(e)
        error_list = [str(e)]
    finally:
        db.close()
    return rows, header, error_list


def add_tag_to_book(book_id, tag):
    """
    Add a tag to a book, creating the tag label if it doesn't exist.

    Parameters
    ----------
    book_id : int
        The BookCollectionID of the book to tag.
    tag : str
        The tag label to add (will be lowercased).

    Returns
    -------
    tuple
        A tuple containing:
        1. A dictionary with BookID, Tag, and TagID on success,
           or an error dictionary on failure.
        2. A list of error messages or None if successful.
    """
    db = pymysql.connect(**books_conf)
    tag = tag.lower().strip()
    result_data = None
    error_list = None
    with db:
        with db.cursor() as c:
            try:
                c.execute('INSERT IGNORE INTO `tag labels` SET Label=%s', (tag,))
                c.execute('SELECT TagID FROM `tag labels` WHERE Label=%s', (tag,))
                tag_id = c.fetchone()[0]
                c.execute('INSERT INTO `books tags` (BookID, TagID) VALUES (%s, %s)', (book_id, tag_id))
                result_data = {"BookID": book_id, "Tag": tag, "TagID": tag_id}
            except pymysql.Error as e:
                app_logger.error(e)
                error_list = [str(e)]
                result_data = {"error": str(e)}
        db.commit()
    return result_data, error_list


##########################################################################
# IMAGES
##########################################################################


def get_images_for_book(book_id):
    """
    Retrieve all image records for a given BookCollectionID.

    Parameters
    ----------
    book_id : int
        The BookCollectionID to fetch images for.

    Returns
    -------
    tuple
        A tuple containing:
        1. A list of image dictionaries with keys: id, BookCollectionID, name, url, type
        2. A list of error messages or None if successful
    """
    db = pymysql.connect(**books_conf)
    search_str = "SELECT id, BookCollectionID, name, url, type FROM `images` WHERE BookCollectionID = %s"
    images = []
    error_list = None

    with db:
        with db.cursor() as c:
            try:
                c.execute(search_str, (book_id,))
                results = c.fetchall()

                for row in results:
                    images.append({
                        "id": row[0],
                        "BookCollectionID": row[1],
                        "name": row[2],
                        "url": row[3],
                        "type": row[4]
                    })
            except pymysql.Error as e:
                app_logger.error(e)
                error_list = [str(e)]

    return images, error_list


##########################################################################
# READING ESTIMATES
##########################################################################


def daily_page_record_from_db(RecordID):
    """
    Fetches daily page records for a specified RecordID from the database.

    Adds a day number column to each record, indicating the number of days since the first record.

    Parameters:
    RecordID (int): The ID for which daily page records are to be fetched.

    Returns:
    tuple: A tuple containing (data, error_list) where data is the modified list
           of records and error_list is None or a list of error strings.
    """
    # Initialize an empty list for the data
    data = []
    error_list = None

    # Connect to the database
    try:
        db = pymysql.connect(**books_conf)
        with db.cursor() as cur:
            # Execute the query to fetch daily page records
            q = ("SELECT a.RecordDate, a.page FROM `daily page records` a "
                 "WHERE a.RecordID = %s ORDER BY a.RecordDate ASC")
            app_logger.debug(q)
            cur.execute(q, (RecordID,))
            rows = cur.fetchall()

            # Check if any rows were returned
            if rows:
                first_record_date = rows[0][0]
                for row in rows:
                    # Calculate the day number and append it to the row
                    day_number = (row[0] - first_record_date).days
                    data.append(list(row) + [day_number])
    except pymysql.MySQLError as e:
        app_logger.error(f"Database error: {e}")
        error_list = [str(e)]
    finally:
        # Ensure the database connection is closed
        db.close()

    return data, error_list


def reading_book_data_from_db(RecordID):
    """
    Fetches book data for a specified RecordID from the database.

    Excludes the BookCollectionID and RecordID from the returned data.

    Parameters:
    RecordID (int): The ID for which book data is to be fetched.

    Returns:
    tuple: A tuple containing (rows, error_list) where rows is the list of book
           data records and error_list is None or a list of error strings.
    """
    # Initialize an empty list for the data
    rows = []
    error_list = None
    # Establish a database connection
    try:
        db = pymysql.connect(**books_conf)
        with db.cursor() as cur:
            # Execute the query to fetch book data
            q = 'SELECT StartDate, LastReadablePage FROM `complete date estimates` WHERE RecordID = %s'
            app_logger.debug(q)
            cur.execute(q, (RecordID,))
            rows = cur.fetchall()
    except pymysql.MySQLError as e:
        # Handle database errors
        app_logger.error(f"Database error: {e}")
        error_list = [str(e)]
    finally:
        # Ensure the database connection is closed
        db.close()

    return rows, error_list


def update_reading_book_data(record_id, date_range):
    result = {}
    db = pymysql.connect(**books_conf)
    with db:
        with db.cursor() as c:
            try:
                c.execute(
                    "UPDATE `complete date estimates` SET EstimateDate = %s, EstimatedFinishDate = %s WHERE RecordID = %s",
                    (datetime.datetime.now(), date_range[0], record_id))
            except pymysql.Error as e:
                app_logger.error(e)
                result = {"error": [str(e)]}
        db.commit()
    return result


def _estimate_values(x_values, y_values, target_x):
    """
    Estimates the minimum and maximum y-values for a given target x-value based on linear interpolation
    of the input x and y values.

    Parameters:
    - x_values (list or numpy array): The x-values of the data points.
    - y_values (list or numpy array): The y-values of the data points.
    - target_x (float): The x-value for which to estimate the corresponding y-value range.

    Returns:
    - list: A list containing the minimum and maximum estimated y-values for the target x-value.
    """
    slope, _ = np.polyfit(x_values, y_values, 1)  # linear fit to all points
    most_likely_y = slope * (target_x - np.max(x_values)) + np.max(y_values)
    estimated_range = [float('inf'), -float('inf')]
    for i in range(len(x_values) - 1):
        denom = x_values[i + 1] - x_values[i]
        if denom == 0:
            app_logger.error(f"Divide by zero error at index {i} -- skipping")
            app_logger.debug(f"Did you enter the same page count for two different days?")
            continue
        else:
            slope = (y_values[i + 1] - y_values[i]) / denom
        estimated_y = slope * (target_x - np.max(x_values)) + np.max(y_values)
        estimated_range[0] = min(estimated_range[0], estimated_y)
        estimated_range[1] = max(estimated_range[1], estimated_y)

    app_logger.debug(f"Estimated days: {most_likely_y} and estimated range: {estimated_range}")
    # expected, shortest, longest in days from first record
    return [int(x) for x in [most_likely_y, estimated_range[0], estimated_range[1]]]


def estimate_completion_dates(reading_data, total_pages):
    """
    Estimates the book completion date based on reading data and provides a range of potential completion dates.

    Parameters:
    - reading_data (list of lists): Each sublist contains [datetime object, pages read, day number].
    - start_date (datetime.date): The date when the reading started.
    - total_readable_pages (int): Total number of pages in the book.

    Returns:
    - datetime.date: The estimated date of completion.
    - tuple: A tuple containing the earliest and latest estimated completion dates as datetime.date objects.
    """

    start_date = reading_data[0][0]  # first record date
    # Convert input data to numpy arrays for manipulation
    data_array = np.array(reading_data)
    pages_read = np.array(data_array[:, 1], dtype=np.float64)  # Extract pages read
    day_number = np.array(data_array[:, 2], dtype=np.float64)  # Extract day numbers

    likely_days, min_days, max_days = _estimate_values(pages_read, day_number, total_pages)  # days from first record
    # Calculate the minimum and maximum estimated completion dates
    date_likely = start_date + datetime.timedelta(days=likely_days)
    est_date_min = start_date + datetime.timedelta(days=min_days)
    est_date_max = start_date + datetime.timedelta(days=max_days)

    return date_likely, est_date_min, est_date_max


def calculate_estimates(record_id):
    """
    Calculates date estimates for a book based on reading and book data.

    Parameters:
    record_id (int): The ID of the book record for which estimates are calculated.

    Returns:
    list: A list containing formatted estimated date range or an error message.
    """
    # Fetch daily page record from the database
    reading_data, _ = daily_page_record_from_db(record_id)
    if len(reading_data) < 2:
        return ["inadequate reading data", None, None]
    # Fetch book data from the database
    book_data, _ = reading_book_data_from_db(record_id)
    if not book_data:
        return ["inadequate book data", None, None]
    total_readable_pages = float(book_data[0][1])
    # Calculate the estimate date range
    estimate_date_range = estimate_completion_dates(reading_data, total_readable_pages)

    # Update the database with the estimated date range
    result = update_reading_book_data(record_id, estimate_date_range)
    if "error" in result:
        return [f'book reading data failure: {result["error"]}', None, None]

    # Format the estimated date range for output
    formatted_estimates = [date.strftime(FMT) for date in estimate_date_range]

    return formatted_estimates
