__version__ = "0.1.1"

import datetime
import logging
import requests

FMT = "%Y-%m-%d"
DIVIDER_WIDTH = 72

class ESTTool:
    def __init__(self, endpoint, api_key):
        # File path contortions so notebook uses the same config as REPL command line
        self.end_point = endpoint
        self.header = {"x-api-key": f"{api_key}"}
        self.result = None

    def version(self):
        """ Retrieve the back end version. """
        q = self.end_point + "/configuration"
        try:
            r = requests.get(q, headers=self.header)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            print("*" * DIVIDER_WIDTH)
            print("        Book Records and Reading Database")
            print("*" * DIVIDER_WIDTH)
            print("Endpoint:          {}".format(self.end_point))
            print("Endpoint Version:  {}".format(res["version"]))
            print("Estimates Version: {}".format(__version__))
            print("*" * DIVIDER_WIDTH)

    ver = version
    def new_book_estimate(self, book_id, total_readable_pages):
        q = self.end_point + f"/add_book_estimate/{book_id}/{total_readable_pages}"
        try:
            tr = requests.put(q, headers=self.header)
            tres = tr.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            if "error" in tres:
                print(f'Error: {tres["error"]}')
            else:
                tres = tres["add_book_estimate"]
                print(f'{tres["BookId"]} started on {tres["StartDate"]}.')
        self.list_book_estimates(book_id)

    nbe = new_book_estimate

    def list_book_estimates(self, book_id):
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
            print("No estimates found for this book.")
        else:
            logging.debug(br)
            if "error" in tres:
                print(f'Error: {tres["error"]}')
                print("No estimates found for this book.")
            elif len(tres["record_set"]) > 0:
                tres = tres["record_set"]
                print("*" * DIVIDER_WIDTH)
                print(f'"{bres[1]}" by {bres[2]} has {bres[7]} pages.\n')
                for i in range(len(tres["RecordId"])):  # print all records
                    print(f'  Start date: {tres["RecordId"][i][0]}   Record ID: {tres["RecordId"][i][1]}')
                    print(f'  Estimated Finish: {tres["Estimate"][i][0]}  Earliest: {tres["Estimate"][i][1]}   Latest: {tres["Estimate"][i][2]}')
                    print(f'  ----------') if len(tres["RecordId"]) > 1 else None
                print("*" * DIVIDER_WIDTH)
            self.result = book_id

    lbe = list_book_estimates

    def add_page_date(self, record_id, page, date=None):
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
                logging.error(f'Error: {res["error"]}')
            else:
                res = res["add_date_page"]
                print(f'{res["RecordId"]} read to page {res["Page"]} on {date}.')
        self.result = record_id

    aps = add_page_date

