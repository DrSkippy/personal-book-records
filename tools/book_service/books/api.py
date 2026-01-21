__version__ = '0.16.2'

import functools
import os
from io import BytesIO
from logging.config import dictConfig

import pandas as pd
import requests
from booksdb.api_util import *
from flask import Flask, Response, send_file, request, abort
from matplotlib import pylab as plt
from werkzeug.utils import secure_filename

from books.isbn_com import Endpoint as isbn

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)


def resp_header(rdata):
    """
    Generate HTTP response headers for a JSON payload.

    This function constructs a list of header tuples suitable for sending an HTTP
    response containing JSON data.  It automatically sets the `Content-Type`
    to JSON with UTF‑8 encoding and calculates the correct `Content-Length`
    based on the supplied response body.

    Args:
        rdata (bytes or str): The raw response body.  The length of this data is
            used to set the `Content-Length` header.  `rdata` should already be
            encoded as UTF‑8 bytes or a Unicode string representing the JSON
            payload.

    Returns:
        list[tuple[str, str]]: A list of two‑item tuples where each tuple
            contains a header name and its corresponding value.  The list
            always contains the `Content-Type` header for JSON with UTF‑8
            encoding followed by the `Content-Length` header reflecting
            the byte length of `rdata`.
    """
    response_header = [
        ('Content-type', 'application/json; charset=utf-8'),
        ('Content-Length', str(len(rdata)))
    ]
    return response_header


def require_app_key(view_function):
    """
    Verify that an incoming HTTP request contains a valid API key before executing
    the wrapped view function.

    Parameters
    ----------
    view_function : callable
        The view function to be protected. It will be called with the same
        positional and keyword arguments that the decorated function receives.

    Returns
    -------
    callable
        A new function that first checks the request header 'x-api-key' against
        the configured API_KEY. If the key matches, it forwards the call to
        view_function; otherwise it logs an error and aborts with a 401
        Unauthorized response.

    Raises
    ------
    HTTPException
        Raised when the 'x-api-key' header is missing or does not match
        the expected API_KEY. The abort(401) call from Flask triggers this
        exception, causing an HTTP 401 Unauthorized error to be returned.
    """

    @functools.wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        # Select one of these:
        # if request.args.get('key') and request.args.get('key') == key:
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            app_logger.error("x-api-key missing or incorrect.")
            abort(401)

    return decorated_function


def json_response(data, status=200):
    """
    Create a Flask Response object with JSON data and appropriate headers.

    Parameters
    ----------
    data : dict or list
        The data to serialize as JSON.
    status : int, optional
        The HTTP status code (default: 200).

    Returns
    -------
    Response
        A Flask Response object with JSON content and headers.
    """
    rdata = json.dumps(data)
    return Response(response=rdata, status=status, headers=resp_header(rdata))


def json_string_response(json_str, status=200):
    """
    Create a Flask Response object from an already-serialized JSON string.

    Parameters
    ----------
    json_str : str
        A pre-serialized JSON string.
    status : int, optional
        The HTTP status code (default: 200).

    Returns
    -------
    Response
        A Flask Response object with JSON content and headers.
    """
    return Response(response=json_str, status=status, headers=resp_header(json_str))


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/configuration')
@require_app_key
def configuration():
    """
    Retrieves the application configuration and metadata as a JSON response.

    Parameters
        None

    Returns
        flask.Response - JSON string containing the application version, the
        configuration dictionaries, the ISBN configuration, and the current
        date/time in ISO 8601 format.
    """
    books_conf_clean = books_conf.copy()
    books_conf_clean["passwd"] = "******"
    isbn_conf_clean = isbn_conf.copy()
    isbn_conf_clean["key"] = "******"
    clean = {
        "version": __version__,
        "configuration": books_conf_clean,
        "isbn_configuration": isbn_conf_clean,
        "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    }
    return json_response(clean)


##########################################################################
# UI Utilities
##########################################################################

@app.route('/valid_locations')
@require_app_key
def valid_locations():
    """
    Retrieve a list of all valid locations.

    This endpoint gathers the data of all valid locations from the database,
    serialises it into the desired format, and returns a HTTP 200 response.
    The data is obtained by calling :func:`get_valid_locations`, which returns
    the raw data rows, the status code, the header information, and any
    validation errors. The rows, header, and errors are then processed by
    :func:`serialize_rows` to produce a serialised representation suitable
    for the client. The resulting string is wrapped in a Flask
    :class:`Response` object and returned with a 200 status code and headers
    derived from :func:`resp_header`.

    Returns
    -------
    Response
        A Flask Response object containing the serialized valid locations
        data and the appropriate HTTP headers.
    """
    rdata, s, header, errors = get_valid_locations()
    result = serialized_result_dict(rdata, header, errors)
    return json_string_response(result)


##########################################################################
# BOOKS WITH MOST RECENT UPDATES
##########################################################################


@app.route('/recent')
@app.route('/recent/<limit>')
@require_app_key
def recent(limit=10):
    """
    Retrieves a list of the most recently accessed books.

    The function is registered as a route handler for the `/recent` endpoint and accepts an
    optional `limit` parameter that determines the maximum number of books to return.
    The default limit is 10.  It calls the internal helper `get_recently_touched` to
    obtain the books, serializes the result, and returns a Flask `Response` object
    containing the data along with appropriate headers.

    Args:
        limit (int): Maximum number of recent books to return. Defaults to 10.

    Returns:
        flask.Response: A response object containing the serialized list of recent
        books, a status code of 200, and any necessary headers.

    Raises:
        None.
    """
    limit = int(limit)
    recent_books, s, header, error_list = get_recently_touched(limit)
    result = serialized_result_dict(recent_books, header, error_list)
    return json_string_response(result)


##########################################################################
# ADDS
##########################################################################

@app.route('/add_books', methods=['POST'])
@require_app_key
def add_books():
    """
    JSON Post Payload:
    [{
      "Title": "Delete Me Now",
      "Author": "Tester, N A",
      "CopyrightDate": "1999-01-01",
      "ISBNNumber": "1234",
      "ISBNNumber13": "1234",
      "PublisherName": "Printerman",
      "CoverType": "Hard",
      "Pages": "7",
      "Location": "Main Collection",
      "Note": "",
      "Recycled": 0
    }, ...]

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_add_books.json \
    http://172.17.0.2:5000/add_books

    :return:
    """
    # records should be a list of dictionaries including all fields
    db = pymysql.connect(**books_conf)
    records = request.get_json()
    search_str = ("INSERT INTO `book collection` "
                  "(Title, Author, CopyrightDate, ISBNNumber, ISBNNumber13, PublisherName, CoverType, Pages, "
                  "Location, Note, Recycled) "
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    book_id_str = "SELECT LAST_INSERT_ID();"
    rdata = []
    with db:
        with db.cursor() as c:
            for record in records:
                try:
                    copyright_date = record["CopyrightDate"]
                    if len(copyright_date.strip()) == 4:
                        copyright_date += "-01-01 00:00:00"  # make it a valid date string!
                    c.execute(search_str, (
                        record["Title"],
                        record["Author"],
                        copyright_date,
                        record["ISBNNumber"],
                        record["ISBNNumber13"],
                        record["PublisherName"],
                        record["CoverType"],
                        record["Pages"],
                        record["Location"],
                        record["Note"],
                        record["Recycled"]
                    ))
                    c.execute(book_id_str)
                    record["BookCollectionID"] = c.fetchall()[0][0]
                    rdata.append(record)
                except pymysql.Error as e:
                    app.logger.error(e)
                    rdata.append({"error": str(e)})
        db.commit()
    return json_response({"add_books": rdata})


@app.route('/add_read_dates', methods=['POST'])
@require_app_key
def add_read_dates():
    """
    Post Payload:
    [{
      "BookCollectionID": 1606,
      "ReadDate": "0000-00-00",
      "ReadNote": ""
    }, ...]

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_update_read_dates.json \
    http://172.17.0.2:5000/update_read_dates

    :return:
    """
    # records should be a list of dictionaries including all fields
    db = pymysql.connect(**books_conf)
    records = request.get_json()
    search_str = 'INSERT INTO `books read` (BookCollectionID, ReadDate, ReadNote) VALUES (%s, %s, %s)'
    res = {"update_read_dates": [], "error": []}
    with db:
        with db.cursor() as c:
            for record in records:
                try:
                    app.logger.debug(f"Inserting read date for BookCollectionID: {record['BookCollectionID']}")
                    c.execute(search_str, (
                        record["BookCollectionID"],
                        record["ReadDate"],
                        record["ReadNote"]
                    ))
                    res["update_read_dates"].append(record)
                except pymysql.Error as e:
                    app.logger.error(e)
                    res["error"].append(str(e))
        db.commit()
    return json_response(res)


@app.route('/books_by_isbn', methods=['POST'])
@require_app_key
def books_by_isbn():
    """
    Creates records from isbn lookup and adds to the collection.

    curl -X POST http://192.168.127.7/books/books_by_isbn -H 'Content-type:application/json' -d '{"isbn_list":["0060929480"]}'

    Arguments
        List of isbns in isbn_list (strings) of the books you wish to get info
    Returns
        None or error
        bc.result is list of ids added.
    """
    book_isbn_list = request.get_json()["isbn_list"]
    res = []
    a = isbn(isbn_conf)
    for book_isbn in book_isbn_list:
        res_json = a.get_book_by_isbn(book_isbn)
        if res_json is not None:
            proto = a._endpoint_to_collection_db(res_json)
            res.append(proto)
        else:
            app.logger.error(f"No records found for isbn {book_isbn}.")
    return json_response({"book_records": res})


##########################################################################
# UPDATES
##########################################################################
@app.route('/update_edit_read_note', methods=['POST'])
@require_app_key
def update_edit_read_note():
    """
    Post Payload:
    {
      "BookCollectionID": 1606,
      "ReadDate": "0000-00-00"
      "ReadNote": "New note."
    }

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_update_edit_read_note.json \
    http://172.17.0.2:5000/update_update_edit_read_note

    :return:
    """
    # records should be a single dictionaries including all fields
    db = pymysql.connect(**books_conf)
    record = request.get_json()
    search_str = "UPDATE `books read` SET ReadNote=%s WHERE BookCollectionID = %s AND ReadDate = %s"
    app.logger.debug(f"Updating read note for BookCollectionID: {record['BookCollectionID']}")
    rdata = []
    with db:
        with db.cursor() as c:
            try:
                c.execute(search_str, (
                    record["ReadNote"],
                    record["BookCollectionID"],
                    record["ReadDate"]
                ))
                rdata.append(record)
            except pymysql.Error as e:
                app.logger.error(e)
                rdata.append({"error": str(e)})
        db.commit()
    return json_response({"update_read": rdata})


@app.route('/update_book_note_status', methods=['POST'])
@require_app_key
def update_book_note_status():
    """
    Post Payload:
    {
      "BookCollectionID": 1606,
      "Note": "",
      "Recycled": 0
    }

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_update_book_note_status.json \
    http://172.17.0.2:5000/update_book_note_status

    :return:
    """
    # records should be a single dictionaries including all changed fields
    record = request.get_json()
    # test of the record has BookCollectionID and one or both of Note and Recycled fields
    if not ("BookCollectionID" in record and ("Note" in record or "Recycled" in record)):
        return json_response({"error": "Missing required fields: BookCollectionID, Note OR Recycled"}, status=400)
    else:
        data = update_book_record_by_key(record)
        return json_response({"update_read": data})


@app.route('/update_book_record', methods=['POST'])
@require_app_key
def update_book_record():
    """
    Post Payload:
    {
      "BookCollectionID": 1606,
      "Recycled": 0
    }

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_update_book_note_status.json \
    http://172.17.0.2:5000/update_book_record

    :return:
    """
    # records should be a single dictionaries including all changed fields
    record = request.get_json()
    # test of the record has BookCollectionID and one of any other field
    if not ("BookCollectionID" in record and len(record.keys()) > 1):
        return json_response({"error": "Missing required fields: BookCollectionID, and any other field"}, status=400)
    else:
        data = update_book_record_by_key(record)
        return json_response({"update_read": data})


##########################################################################
# REPORTS
##########################################################################


@app.route('/summary_books_read_by_year')
@app.route('/summary_books_read_by_year/<target_year>')
@require_app_key
def summary_books_read_by_year(target_year=None):
    """
    Generates a summarized list of books read by year, optionally filtered by a
    specific target year.

    Parameters
    ----------
    target_year : str or None
        The year to filter the summary. If ``None``, summaries for all years
        are included.

    Returns
    -------
    Response
        A Flask Response object containing the serialized summary data, the
        appropriate HTTP headers, and a 200 status code.
    """
    rdata, header, error_list = summary_books_read_by_year_utility(target_year)
    result = serialized_result_dict(rdata, header, error_list)
    return json_string_response(result)


@app.route('/books_read')
@app.route('/books_read/<target_year>')
@require_app_key
def books_read(target_year=None):
    """
    Handles HTTP GET requests for books read statistics.

    This route accepts an optional ``target_year`` path parameter. When
    provided, the function retrieves books read data for the specified year;
    otherwise it returns data for all available years. The underlying utility
    function ``books_read_by_year_utility`` returns a tuple of the data,
    header and error list. The response is serialized, wrapped with
    appropriate HTTP headers, and returned as a Flask ``Response`` object
    with status code 200.

    :param target_year: The year for which to filter the books read
        statistics. If omitted, statistics for all years are returned.
    :type target_year: str or None

    :return: Flask response object containing the serialized data and HTTP
        headers.
    :rtype: Response
    """
    rdata, _, header, error_list = books_read_by_year_utility(target_year)
    result = serialized_result_dict(rdata, header, error_list)
    return json_string_response(result)


@app.route('/status_read/<book_id>')
@require_app_key
def status_read(book_id=None):
    """
    Return the status of a book identified by book_id.

    Parameters
    ----------
    book_id : str, optional
        Identifier of the book.  If omitted, the function will
        return status information for all books.

    Returns
    -------
    Response
        A Flask Response object containing the status data for the
        requested book.  The response body is the raw data returned
        by `status_read_utility`, and the status code is 200.
    """
    rdata, header, error_list = status_read_utility(book_id)
    result = serialized_result_dict(rdata, header, error_list)
    return json_string_response(result)


##########################################################################
# SEARCH
##########################################################################

@app.route('/books_search', methods=['POST', 'GET'])
@require_app_key
def books_search():
    """
    Search for books by query parameters.

    Parameters
    ----------
    None

    Returns
    -------
    Response
        A Flask Response object containing the serialized search results.
        The response body is JSON encoded and includes any error messages that
        occurred during processing. The HTTP status code is always 200.

    Notes
    -----
    The function extracts query arguments from the Flask `request.args` object,
    passes them to the `books_search_utility` helper, and then serializes
    the resulting data with `serialized_result_dict`.
    The `resp_header` function is used to construct the appropriate HTTP
    headers for the response.

    """
    # process any query parameters
    args = request.args
    rdata, header, error_list = books_search_utility(args)
    result = serialized_result_dict(rdata, header, error_list)
    return json_string_response(result)


##########################################################################
# COMPLETE BOOK RECORD
##########################################################################


@app.route('/complete_records_window/<book_id>/<window>')
@require_app_key
def complete_record_window(book_id, window=20):
    """
    Return a JSON list of complete book records for a window of book IDs
    around the given book_id.

    Parameters
    ----------
    book_id
        The identifier of the book for which a window of complete records
        is requested.
    window
        The number of book IDs to include in the window.  Defaults to 20
        if not supplied.

    Returns
    -------
    flask.Response
        A Flask Response object containing a JSON string that represents a
        list of complete book records for the requested window.  The HTTP
        status is set to 200.

    Raises
    ------
    None.

    Notes
    -----
    This route internally uses `get_book_ids_in_window` to obtain the list
    of book IDs, then retrieves each complete record with
    `get_complete_book_record`.  The response headers are generated by
    `resp_header`.

    See Also
    --------
    get_book_ids_in_window, get_complete_book_record, resp_header
    """
    window_list = []
    for bid in get_book_ids_in_window(book_id, int(window)):
        window_list.append(get_complete_book_record(bid))
    return json_response(window_list)


@app.route('/complete_record/<book_id>')
@app.route('/complete_record/<book_id>/<adjacent>')
@require_app_key
def complete_record(book_id, adjacent=None):
    """
    Detailed summary:
    The `complete_record` view retrieves the full book record for a given book ID.
    It can optionally navigate to the next or previous book by interpreting the
    `adjacent` parameter. The returned value is a Flask `Response` containing JSON
    data and the necessary HTTP headers.

    Parameters:
        book_id (str): Identifier of the book whose complete record is requested.
        adjacent (str or None, optional): Navigation direction relative to the
            current book. Accepts `"next"` or `"prev"` (case‑insensitive).
            If omitted or `None`, the current book record is returned.

    Returns:
        flask.Response: A Flask `Response` object with a JSON‑encoded body that
        contains the complete book record. The response headers are set by
        `resp_header`. If an invalid `adjacent` value is supplied, an empty JSON
        object is returned.

    Raises:
        None: The function handles any invalid input internally via logging and
        does not raise exceptions to the caller.

    Notes:
        * When `adjacent` is `"next"`, the function obtains the next book ID
          with `get_next_book_id(book_id, 1)` and retrieves that record.
        * When `adjacent` starts with `"prev"`, it obtains the previous book ID
          with `get_next_book_id(book_id, -1)` and retrieves that record.
        * Invalid `adjacent` values are logged with `app.logger.error` and result
          in an empty JSON response.
    """
    if adjacent is None:
        return json_response(get_complete_book_record(book_id))
    elif adjacent.lower() == "next":
        next_id = get_next_book_id(book_id, 1)
        return json_response(get_complete_book_record(next_id))
    elif adjacent.lower().startswith("prev"):
        previous_id = get_next_book_id(book_id, -1)
        return json_response(get_complete_book_record(previous_id))
    else:
        app.logger.error(f"Invalid adjacent parameter: {adjacent}")
        return json_response({})


##########################################################################
# TAGS
##########################################################################

@app.route('/add_tag/<book_id>/<tag>', methods=["PUT"])
@require_app_key
def add_tag(book_id, tag):
    result_data, error_list = add_tag_to_book(book_id, tag)
    return json_response(result_data)


@app.route('/tag_counts')
@app.route('/tag_counts/<tag>')
@require_app_key
def tag_counts(tag=None):
    """
    Retrieve tag count information from the database.

    Args:
        tag (str or None): Optional tag name used to filter results by label prefix.

    Returns:
        Response: Flask Response object with JSON data and response headers.
    """
    rows, header, error_list = get_tag_counts(tag)
    if error_list:
        return json_response({"error": error_list})
    result = serialized_result_dict(rows, header)
    return json_string_response(result)


@app.route('/tags/<book_id>')
@require_app_key
def tags(book_id=None):
    """
    Retrieve serialized tags for a book by its identifier.

    This Flask view handles GET requests to the `/tags/<book_id>` endpoint. It
    fetches the tags associated with the given book, serializes the result into a
    dictionary, sets appropriate response headers, and returns a Flask
    `Response` object with a status code of 200.

    Parameters:
        book_id (str): The unique identifier of the book whose tags are to be
            retrieved. If omitted, the route will not match and Flask will
            return a 404.

    Returns:
        Response: A Flask `Response` object containing the serialized tag data
            and custom headers.
    """
    rdata, error_list = book_tags(book_id)
    if error_list:
        rdata["error"] = error_list
    return json_response(rdata)


@app.route('/update_tag_value/<current>/<updated>', methods=["PUT"])
@require_app_key
def update_tag_value(current, updated):
    """
    Handles updating a tag label in the database.

    This endpoint accepts the current tag label and the updated tag label as URL
    parameters, performs an UPDATE statement on the `tag labels` table and returns
    a JSON response with the number of affected rows or an error message.  The
    operation is protected by the # @require_app_key decorator and logs any
    database errors.

    Parameters
    ----------
    current : str
        The tag label to be replaced.
    updated : str
        The new tag label to use in place of the current one.

    Returns
    -------
    Response
        A Flask Response object with status 200 and a JSON body.  The body
        contains either a ``data`` key with the update information or an
        ``error`` key if a database error occurred.

    Raises
    ------
    None
    """
    db = pymysql.connect(**books_conf)
    result_data = None
    with db:
        with db.cursor() as c:
            try:
                _updated = updated.lower().strip(" ")
                records = c.execute("UPDATE `tag labels` SET Label = %s WHERE Label = %s", (_updated, current))
                result_data = {"data": {"tag_update": f"{current} >> {updated}", "updated_tags": records}}
            except pymysql.Error as e:
                app.logger.error(e)
                result_data = {"error": str(e)}
        db.commit()
    return json_response(result_data)


@app.route('/tags_search/<match_str>')
@require_app_key
def tags_search(match_str):
    """
    Search tags for the given match string.

    Parameters
    ----------
    match_str : str
        The string to match tags against.

    Returns
    -------
    flask.Response
        A Flask Response object containing the tag search results
        with status 200 and appropriate response headers.

    Raises
    ------
    Any exception raised by `tags_search_utility`, `resp_header` or
    `Response` constructor will propagate to the caller.
    """
    row_data, header, error_list = tags_search_utility(match_str)
    result = serialized_result_dict(row_data, header, error_list)
    return json_string_response(result)


@app.route('/tag_maintenance')
@require_app_key
def tag_maintenance():
    db = pymysql.connect(**books_conf)
    rdata = {"tag_maintenance": {}}
    with db:
        with db.cursor() as c:
            try:
                # lower case
                c.execute("UPDATE `tag labels` SET Label = TRIM(LOWER(Label))")
                db.commit()
            except pymysql.Error as e:
                rdata = {"error": [str(e)]}
                app.logger.error(e)
    return json_response(rdata)


##########################################################################
# READING ESTIMATES
##########################################################################
@app.route('/date_page_records/<record_id>')
@require_app_key
def date_page_records(record_id=None):
    # data is [(RecordDate, page, day_number from first page record), ...]
    data, error_list = daily_page_record_from_db(record_id)
    rdata = {"date_page_records": [], "RecordID": record_id}
    if error_list:
        rdata["error"] = error_list
    elif len(data) > 0:
        rdata["date_page_records"] = [(x.strftime(FMT), int(y), int(z)) for [x, y, z] in data]
    else:
        rdata["error"] = "No records found."
    return json_response(rdata)


@app.route('/record_set/<book_id>')
@require_app_key
def record_set(book_id=None):
    db = pymysql.connect(**books_conf)
    rdata = {"record_set": {"BookCollectionID": book_id, "RecordID": [], "Estimate": []}}
    q = "SELECT StartDate, RecordID FROM `complete date estimates` WHERE BookCollectionID = %s ORDER BY StartDate ASC"
    with db:
        with db.cursor() as c:
            try:
                c.execute(q, (book_id,))
                res = c.fetchall()
            except pymysql.Error as e:
                rdata["error"] = [str(e)]
                app.logger.error(e)
                res = []
        db.commit()
    for record in [(str(x[0]), int(x[1])) for x in res]:
        rdata["record_set"]["RecordID"].append(record)
        rdata["record_set"]["Estimate"].append(calculate_estimates(record[1]))
    return json_response(rdata)


@app.route('/add_date_page', methods=['POST'])
@require_app_key
def add_date_page():
    """
    Post Payload:
    {
      "RecordID": 123,
      "RecordDate": "0000-00-00"
      "Page": 123
    }

    E.g.
    curl -X POST -H "Content-type: application/json" -d @./example_json_payloads/test_add_date_page.json \
    http://172.17.0.2:5000/add_date_page

    :return:
    """
    # records should be a single dictionaries including all fields
    record = request.get_json()
    search_str = "INSERT INTO `daily page records` (RecordID, RecordDate, page) VALUES (%s, %s, %s)"
    app.logger.debug(f"Inserting date page record for RecordID: {record.get('RecordID')}")
    db = pymysql.connect(**books_conf)
    result_data = {"error": "No record added."}
    with db:
        with db.cursor() as c:
            try:
                c.execute(search_str, (
                    record["RecordID"],
                    record["RecordDate"],
                    record["Page"]
                ))
                result_data = {"add_date_page": record}
            except pymysql.Error as e:
                app.logger.error(e)
                result_data = {"add_date_page": {}, "error": str(e)}
        db.commit()
    return json_response(result_data)


@app.route('/add_book_estimate/<book_id>/<last_readable_page>', methods=["PUT"])
@app.route('/add_book_estimate/<book_id>/<last_readable_page>/<start_date>', methods=["PUT"])
@require_app_key
def add_book_estimate(book_id, last_readable_page, start_date=None):
    # TODO: if you call it again, you get a new record_id for a second reading of the same book
    db = pymysql.connect(**books_conf)
    last_readable_page = int(last_readable_page)
    if start_date is None:
        start_date = datetime.datetime.now().strftime(FMT)
    q = "INSERT INTO `complete date estimates` (BookCollectionID, StartDate, LastReadablePage) VALUES (%s, %s, %s)"
    app.logger.debug(f"Inserting book estimate for BookCollectionID: {book_id}")
    result_data = None
    with db:
        with db.cursor() as c:
            try:
                c.execute(q, (book_id, start_date, last_readable_page))
                result_data = {"add_book_estimate":
                                   {"BookCollectionID": f"{book_id}", "LastReadablePage":
                                       f"{last_readable_page}", "StartDate": f"{start_date}"}}
            except pymysql.Error as e:
                app.logger.error(e)
                result_data = {"add_book_estimate": {}, "error": str(e)}
        db.commit()
    return json_response(result_data)


##########################################################################
# IMAGES
##########################################################################
@app.route('/images/<book_id>')
@require_app_key
def get_images(book_id):
    """
    Retrieve all image information for a given BookCollectionID.

    Parameters:
        book_id: The BookCollectionID to fetch images for

    Returns:
        JSON response with list of image records for the book
    """
    images, error_list = get_images_for_book(book_id)
    if error_list:
        return json_response({"error": error_list})
    return json_response({
        "BookCollectionID": int(book_id),
        "images": images,
        "count": len(images)
    })


@app.route('/add_image', methods=['POST'])
@require_app_key
def add_image():
    """
    Add an image entry to the images database table.

    Post Payload:
    {
      "BookCollectionID": 1234,
      "name": "book_cover.jpg",
      "url": "/resources/books/book_cover.jpg",
      "type": "cover-face"
    }

    E.g.
    curl -X POST -H "Content-type: application/json" -H "x-api-key: YOUR_API_KEY" \
    -d '{"BookCollectionID": 1234, "name": "cover.jpg", "url": "/resources/books/cover.jpg", "type": "cover-face"}' \
    http://172.17.0.2:5000/add_image

    Returns:
        JSON response with the inserted image record including the auto-generated id
    """
    db = pymysql.connect(**books_conf)
    record = request.get_json()

    # Validate required fields
    if 'BookCollectionID' not in record:
        return json_response({"error": "Missing required field: BookCollectionID"}, status=400)

    # Set default type if not provided
    if 'type' not in record:
        record['type'] = 'cover-face'

    # Verify image exists at the provided url
    if 'url' in record and record['url']:
        image_url = record['url']

        # Check if it's a web URL (http:// or https://)
        if image_url.startswith('http://') or image_url.startswith('https://'):
            try:
                # Make a HEAD request to check if the URL is accessible
                response = requests.head(image_url, timeout=5, allow_redirects=True)

                # If HEAD is not supported, try GET with stream
                if response.status_code == 405:
                    response = requests.get(image_url, timeout=5, stream=True, headers={'Range': 'bytes=0-0'})

                if response.status_code != 200:
                    app.logger.warning(f"Image URL returned status {response.status_code}: {image_url}")
                    return json_response(
                        {"error": f"Image URL not accessible (status {response.status_code}): {image_url}"}, status=400)

                # Optionally verify it's an image by checking content-type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    app.logger.warning(f"URL does not point to an image (content-type: {content_type}): {image_url}")
                    return json_response({"error": f"URL does not appear to be an image (content-type: {content_type})"}, status=400)

            except requests.exceptions.Timeout:
                app.logger.error(f"Timeout while verifying image URL: {image_url}")
                return json_response({"error": f"Timeout while verifying image URL: {image_url}"}, status=400)
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Error verifying image URL: {image_url} - {str(e)}")
                return json_response({"error": f"Error verifying image URL: {str(e)}"}, status=400)

    search_str = ("INSERT INTO `images` "
                  "(BookCollectionID, name, url, type) "
                  "VALUES (%s, %s, %s, %s)")
    image_id_str = "SELECT LAST_INSERT_ID();"

    result_data = None
    with db:
        with db.cursor() as c:
            try:
                app.logger.debug(f"Inserting image for BookCollectionID: {record['BookCollectionID']}")
                c.execute(search_str, (
                    record["BookCollectionID"],
                    record.get("name", ""),
                    record.get("url", ""),
                    record["type"]
                ))
                c.execute(image_id_str)
                record["id"] = c.fetchall()[0][0]
                result_data = {"add_image": record}
            except pymysql.Error as e:
                app.logger.error(e)
                result_data = {"error": str(e)}
        db.commit()

    return json_response(result_data)


@app.route('/upload_image', methods=['POST'])
@require_app_key
def upload_image():
    """
    Upload an image file and store it in the configured image path.

    Post Payload (multipart/form-data):
    - file: The image file to upload
    - filename (optional): Custom filename for the uploaded file

    E.g.
    curl -X POST -H "x-api-key: YOUR_API_KEY" -F "file=@/path/to/image.jpg" \
    http://172.17.0.2:5000/upload_image

    Returns:
        JSON response with upload status and file path
    """
    if 'file' not in request.files:
        return json_response({"error": "No file part in the request"}, status=400)

    file = request.files['file']

    if file.filename == '':
        return json_response({"error": "No file selected"}, status=400)

    # Get the configured image path
    image_path = '/books/uploads'

    # Ensure the directory exists
    if not os.path.exists(image_path):
        try:
            os.makedirs(image_path)
        except OSError as e:
            app.logger.error(f"Failed to create directory {image_path}: {e}")
            return json_response({"error": f"Failed to create directory: {str(e)}"}, status=500)

    # Use custom filename if provided, otherwise use secure_filename on original
    custom_filename = request.form.get('filename')
    if custom_filename:
        filename = secure_filename(custom_filename)
    else:
        filename = secure_filename(file.filename)

    file_path = os.path.join(image_path, filename)

    try:
        file.save(file_path)
        app.logger.info(f"File uploaded successfully: {file_path}")
        return json_response({
            "upload_image": {
                "status": "success",
                "filename": filename,
                "path": file_path
            }
        })
    except Exception as e:
        app.logger.error(f"Failed to save file: {e}")
        return json_response({"error": f"Failed to save file: {str(e)}"}, status=500)


@app.route('/image/year_progress_comparison.png')
@app.route('/image/year_progress_comparison.png/<window>')
@require_app_key
def year_progress_comparison(window=15):
    window = int(window)
    img = BytesIO()
    _, s, h, e = books_read_by_year_utility()
    df1 = pd.DataFrame(s, columns=h)
    df1["read_date"] = pd.to_datetime(df1["ReadDate"])
    df1 = df1.set_index("ReadDate")
    df1.index = pd.to_datetime(df1.index)
    ds_pages = df1.groupby(df1.index.to_period('Y'))["Pages"].cumsum()
    ds_day = df1.read_date.apply(lambda x: x.dayofyear)
    ds_year = df1.read_date.apply(lambda x: x.year)
    df1 = pd.concat([ds_pages, ds_day, ds_year], axis=1)
    df1.columns = ["Pages", "Day", "Year"]
    fig_size = [8, 8]
    xlim = [0, 365]
    ylim = [0, max(df1.Pages)]
    years = df1.Year.unique()[-window:].tolist()
    current_year = max(years)
    y = years.pop(0)
    _df = df1.loc[df1.Year == y]
    ax = _df.plot("Day", "Pages", figsize=fig_size, xlim=xlim, ylim=ylim, label=y)
    for y in years:
        _df = df1.loc[df1.Year == y]
        lw = 1 if y != current_year else 4
        ax = _df.plot("Day", "Pages", figsize=fig_size, xlim=xlim, ylim=ylim, ax=ax, label=y, lw=lw)
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')


@app.route('/image/all_years.png')
@app.route('/image/all_years.png/<year>')
@require_app_key
def all_years(year=None):
    if year is None:
        year = datetime.datetime.now().year
    else:
        year = int(year)
    img = BytesIO()
    s, h, e = summary_books_read_by_year_utility()
    df = pd.DataFrame(s, columns=h)
    df['pages read'] = df['pages read'].astype(float)
    df["rank"] = df["pages read"].rank(ascending=False)
    df.sort_values(by=["rank"], inplace=True)
    df.reset_index()
    # When we are in a new year, but no read books yet, we need to add the year
    if year not in df.year.unique():
        year = df.year.unique().max()
    now_df = df.loc[df["year"] == year]
    app.logger.debug(now_df)
    fig, axs = plt.subplots(3, 1, figsize=[10, 18])
    df.hist("pages read", bins=14, color="darkblue", ax=axs[0])
    axs[0].axvline(x=int(now_df["pages read"].iloc[0]), color="red")
    df.plot.bar(x="rank", y="pages read", width=.95, color="darkblue", ax=axs[1])
    axs[1].axvline(x=int(now_df["rank"].iloc[0]) - 1, color="red")
    df.sort_values("year").plot.bar(x="year", y="pages read", width=.95, color="darkblue", ax=axs[2])
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
