import requests
import json


class Endpoint:
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

    def __init__(self, conf):
        self.config = conf

    def get_book_by_isbn(self, isbn=None):
        url = self.config.get("url_isbn").format(isbn)
        headers = {'Authorization': self.config.get("key")}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            return {
                'error': error_message
            }

    def get_books_by_isbn_list(self, isbn_list=[]):
        result = {}
        for isbn in isbn_list:
            try:
                result[isbn] = self.get_book_by_isbn(isbn)
            except Exception as e:
                result[isbn] = {'error': str(e)}
        return result

    def _endpoint_to_collection_db(self, isbn_dict):
        proto = self.COLLECTION_DB_DICT.copy()
        proto["Title"] = isbn_dict["book"]["title"]
        proto["Author"] = isbn_dict["book"]["authors"][0]
        proto["IsbnNumber"] = isbn_dict["book"]["isbn"]
        proto["IsbnNumber13"] = isbn_dict["book"]["isbn13"]
        try:
            proto["PublisherName"] = isbn_dict["book"]["publisher"]
        except KeyError:
            proto["PublisherName"] = "unknown"
        proto["Pages"] = isbn_dict["book"]["pages"]
        try:
            _pub = str(isbn_dict["book"]["date_published"])[:10]  # yyyy-mm-dd
            if len(_pub) == 4:
                _pub += "-01-01"
            proto["CopyrightDate"] = _pub
        except KeyError:
            proto["CopyrightDate"] = "0000-01-01"
        return proto
