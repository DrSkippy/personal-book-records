"""
Serialization utilities for converting database results to JSON.
"""
import datetime
import json
from decimal import Decimal
from typing import Any

from .config import app_logger


def sort_list_by_index_list(
    lst: list[Any],
    indexes: list[int],
    reverse: bool = False
) -> list[Any]:
    """
    Sort elements of a list based on a corresponding list of indexes.

    Parameters
    ----------
    lst : list[Any]
        The list of values to be reordered.
    indexes : list[int]
        The list of indexes that determine the sorting order.
    reverse : bool, optional
        If True, the sorting order is reversed.

    Returns
    -------
    list[Any]
        A list of values from `lst` sorted according to `indexes`.
    """
    return [val for (_, val) in sorted(zip(indexes, lst), key=lambda x: x[0], reverse=reverse)]


def serialized_result_dict(
    db_result_rows: list[tuple[Any, ...]] | None,
    header: list[str] | None = None,
    error_list: list[str] | None = None
) -> str:
    """
    Serializes database result rows into JSON.

    Arguments
    ---------
    db_result_rows : list[tuple[Any, ...]] | None
        The rows returned from a database query.
    header : list[str] | None
        Optional list of column names.
    error_list : list[str] | None
        Optional list of error messages.

    Returns
    -------
    str
        A JSON formatted string representing the serialized result set.
    """
    result = _create_serializeable_result_dict(db_result_rows, header, error_list=None)
    result_dict_json = json.dumps(result)
    return result_dict_json


def _convert_db_types(value_list: list[Any] | tuple[Any, ...]) -> list[Any]:
    """
    Converts database row values to JSON-serializable types.

    Args:
        value_list: The list of values to be converted.

    Returns:
        A new list with Decimal converted to float, dates formatted as strings.
    """
    new_value_list: list[Any] = []
    for d in value_list:
        if isinstance(d, Decimal):
            new_value_list.append(float(d))
        elif isinstance(d, datetime.datetime) or isinstance(d, datetime.date):
            new_value_list.append(d.strftime("%Y-%m-%d"))
        else:
            new_value_list.append(d)
    return new_value_list


def _create_serializeable_result_dict(
    db_result: list[tuple[Any, ...]] | None,
    header: list[str] | None,
    error_list: list[str] | None = None
) -> dict[str, Any]:
    """
    Converts database query results into a dictionary format with header and data.

    Parameters
    ----------
    db_result : list[tuple[Any, ...]] | None
        The database cursor containing the query results.
    header : list[str] | None
        A list of strings representing the column names.
    error_list : list[str] | None, optional
        A list of error strings.

    Returns
    -------
    dict[str, Any]
        A dictionary with 'header', 'data', and optionally 'error' keys.
    """
    result_dict: dict[str, Any] = {"header": header, "data": []}
    if error_list is not None:
        result_dict["error"] = error_list

    result_rows: list[list[Any]] = []
    if db_result is None or len(db_result) == 0:
        pass
    elif isinstance(db_result[0], tuple) or isinstance(db_result[0], list):
        for row in db_result:
            if header and len(header) != len(row):
                app_logger.debug("mismatched header to data provided")
            result_rows.append(_convert_db_types(row))
    else:
        result_rows = _convert_db_types(db_result)  # type: ignore[assignment]
    result_dict["data"] = result_rows
    return result_dict
