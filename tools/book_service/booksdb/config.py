"""
Configuration module for the books database.

This module handles loading configuration from JSON files and provides
shared configuration values used throughout the booksdb package.
"""
import json
import logging
import os
from typing import Any

app_logger: logging.Logger = logging.getLogger('flask.app')

# Constants
table_header: list[str] = [
    "BookCollectionID",
    "Title",
    "Author",
    "CopyrightDate",
    "ISBNNumber",
    "PublisherName",
    "CoverType",
    "Pages",
    "Category",
    "Note",
    "Recycled",
    "Location",
    "ISBNNumber13"
]

locations_sort_order: list[int] = [3, 4, 2, 1, 7, 6, 5]

FMT: str = "%Y-%m-%d"

API_KEY: str | None = None


def read_json_configuration() -> tuple[dict[str, Any], dict[str, str]]:
    """
    Retrieve database and ISBN lookup configuration from JSON file.

    Returns
    -------
    tuple[dict[str, Any], dict[str, str]]
        A tuple containing two dictionaries:
        * ``books_db_config`` – mapping database connection parameters
        * ``isbn_lookup_config`` – mapping ISBN lookup service parameters
        The global variable ``API_KEY`` is set during execution.

    Raises
    ------
    SystemExit
        If a configuration key is missing or the file cannot be read.
    """
    config_filename = os.getenv("BOOKDB_CONFIG", "./config/configuration.json")
    with open(config_filename, "r") as config_file:
        c = json.load(config_file)
        try:
            books_db_config: dict[str, Any] = {
                "user": c["username"].strip(),
                "passwd": c["password"].strip(),
                "db": c["database"].strip(),
                "host": c["host"].strip(),
                "port": int(c["port"])
            }
            isbn_lookup_config: dict[str, str] = {
                "url_isbn": c["isbn_com"]["url_isbn"].strip(),
                "key": c["isbn_com"]["key"].strip()
            }
            global API_KEY
            if os.getenv("API_KEY") is not None:
                API_KEY = os.getenv("API_KEY").replace('\n', '')
            elif "api_key" in c:
                API_KEY = c["api_key"].replace('\n', '')
            else:
                raise KeyError("Missing API key configuration.")
            app_logger.debug(f"API key configuration loaded successfully. Using API_KEY={API_KEY}")
        except KeyError as e:
            app_logger.error(e)
            raise SystemExit("Missing or incomplete configuration file.")
        return books_db_config, isbn_lookup_config


# Initialize configuration on module load
books_conf: dict[str, Any]
isbn_conf: dict[str, str]
books_conf, isbn_conf = read_json_configuration()
