import datetime
import unittest
from decimal import Decimal

from booksdb import api_util as au
from books.api import resp_header


class TestAppUtilityFunctions(unittest.TestCase):

    def test_const(self):
        self.assertEqual(len(au.locations_sort_order), 7)
        self.assertEqual(len(au.table_header), 13)
        self.assertTrue(len(au.API_KEY) > 0)

    def test_get_configuration(self):
        config1, config2 = au.read_json_configuration()
        self.assertGreaterEqual(len(config1['user']), 4)
        self.assertGreaterEqual(len(config1['passwd']), 4)
        self.assertEqual(config1["db"], "books")
        self.assertEqual(len(config2), 2)

    def test_valid_locations(self):
        sll, loc, h, e = au.get_valid_locations()
        print(sll, loc, h, e)
        self.assertTrue(len(sll) == 7)
        self.assertTrue(len(loc) == 8)
        self.assertTrue(h[0] == 'Location')
        self.assertTrue(e is None)

    def test_sort_by_indexes(self):
        lst = [1, 2, 3, 4, 5]
        indexes = [4, 3, 2, 1, 0]
        sorted_lst = au.sort_list_by_index_list(lst, indexes)
        self.assertEqual(sorted_lst, [5, 4, 3, 2, 1])

    def test_serialize_rows(self):
        cursor = [(Decimal(1), 'Title1', 'Author1', datetime.date(2022, 1, 1)),
                  (Decimal(2), 'Title2', 'Author2', datetime.date(2022, 1, 2))]
        header = ['ID', 'Title', 'Author', 'Date']
        expected_result = '{"header": ["ID", "Title", "Author", "Date"], "data": [[1.0, "Title1", "Author1", "2022-01-01"], [2.0, "Title2", "Author2", "2022-01-02"]]}'
        result = au.serialized_result_dict(cursor, header)
        self.assertEqual(result, expected_result)

    def test_resp_header(self):
        rdata = '{"header": ["ID", "Title", "Author", "Date"], "data": [[1, "Title1", "Author1", "2022-01-01"], [2, "Title2", "Author2", "2022-01-02"]]}'
        response_header = resp_header(rdata)
        print(response_header)
        expected_header = [
            ('Content-type', 'application/json; charset=utf-8'),
            ('Content-Length', str(len(rdata)))
        ]
        self.assertEqual(response_header, expected_header)

    def test_summary_books_read_by_year(self):
        res, header, error = au.summary_books_read_by_year_utility(target_year=1966)
        self.assertEqual(len(res[0]), 3)
        print(res)
        print(str(res[0]))
        self.assertEqual(str(res[0]), """(1966, Decimal('2527'), 13)""")

    def test_books_read(self):
        res, header, error = au.books_read_by_year_utility(target_year=1966)
        self.assertEqual(len(res), 13)
        # print(res)
        print(str(res[0])[:64])
        self.assertEqual(str(res[0])[:64],
                         """(155, 'Letters To Children', 'Lewis, C S', datetime.datetime(198""")

    def test_tags_search(self):
        res, header, error = au.tags_search_utility("science")
        self.assertGreater(len(res), 0)  # Should find books with 'science' tag
        self.assertIsNone(error)
        self.assertEqual(header, ['BookCollectionID', 'TagID', 'Tag'])

    def test_books_search(self):
        res, header, error = au.books_search_utility({"Title": "lewis"})
        print(f"Title=lewis results: {len(res)} books found")
        self.assertGreater(len(res), 0)
        self.assertIsNone(error)

        res2, header2, error2 = au.books_search_utility({"Tags": "science"})
        print(f"Tags=science results: {len(res2)} books found")
        self.assertGreater(len(res2), 0)
        self.assertIsNone(error2)

    def test_depending_on_daily_page_record_from_db(self):
        d, _ = au.daily_page_record_from_db(1)
        self.assertEqual(len(d), 4)
        self.assertEqual(str(d[3]), '[datetime.datetime(2022, 2, 9, 0, 0), 279, 8]')

    def test_depending_on_reading_book_data_from_db(self):
        rows, error_list = au.reading_book_data_from_db(1)
        self.assertIsNone(error_list)
        self.assertEqual(rows[0], (datetime.datetime(2022, 2, 1, 0, 0), 788))

        d, _ = au.daily_page_record_from_db(1)
        print(rows[0])
        res1 = au.estimate_completion_dates(d, 1000)
        self.assertEqual(len(res1), 3)
        self.assertEqual(res1[0], datetime.datetime(2022, 5, 16, 0, 0))
        self.assertEqual(res1[1], datetime.datetime(2022, 4, 25, 0, 0))
        self.assertEqual(res1[2], datetime.datetime(2022, 11, 6, 0, 0))

    def test_calculate_estimates(self):
        res = au.calculate_estimates(1)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], "2022-04-18")
        self.assertEqual(res[1], "2022-04-03")
        self.assertEqual(res[2], "2022-08-18")

    def test_get_next_book_id(self):
        next_id = au.get_next_book_id(1873)
        self.assertEqual(next_id, 1874)
        next_id = au.get_next_book_id(1873, -1)
        self.assertEqual(next_id, 1872)
        next_id = au.get_next_book_id(3000, +1)  # last as of 2025-11-26
        self.assertEqual(next_id, 2)
        next_id = au.get_next_book_id(2, -1)  # last as of 2025-11-26
        self.assertGreaterEqual(next_id, 1875)

    def test_get_book_ids_(self):
        book_ids = au.get_book_ids_in_window(2, 20)
        self.assertTrue(set([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]).issubset(book_ids))
        self.assertEqual(len(book_ids), 20)
        book_ids = au.get_book_ids_in_window(3000, 20)  # last as of 2025-11-26
        self.assertTrue(set([2, 3, 4, 5, 6, 7, 8, 9, 10]).issubset(book_ids))
        self.assertEqual(len(book_ids), 20)
        book_ids = au.get_book_ids_in_window(477, 30)
        self.assertEqual(len(book_ids), 30)

    def test_complete_book_record(self):
        rec = au.get_complete_book_record(1873)
        print(rec)
        self.assertEqual(len(rec), 4)
        self.assertEqual(rec["book"]["data"][0][0], 1873)
        self.assertEqual(rec["book"]["data"][0][7], 548)
        self.assertEqual(len(rec["reads"]["data"]), 1)
        self.assertEqual(len(rec["tags"]["data"][0]), 8)
        # Book may or may not have images depending on data state
        self.assertIn("img", rec)

    def test_update_book_record_by_key(self):
        update_data = {
            "BookCollectionID": 1873,
            "Title": "FKA - Demon Copperhead A Novel"
        }
        res = au.update_book_record_by_key(update_data)
        rec = au.get_complete_book_record(1873)
        self.assertTrue(res)
        self.assertEqual(rec["book"]["data"][0][1], "FKA - Demon Copperhead A Novel")
        # Change it back
        update_data = {
            "BookCollectionID": 1873,
            "Title": "Demon Copperhead A Novel"
        }
        res = au.update_book_record_by_key(update_data)
        self.assertTrue(res)
        rec = au.get_complete_book_record(1873)
        self.assertEqual(rec["book"]["data"][0][1], "Demon Copperhead A Novel")

    def test_get_recently_touched(self):
        recent_books, raw_rows, header, error = au.get_recently_touched(limit=5)
        self.assertIsNone(error)
        self.assertEqual(header, ["BookCollectionID", "LastUpdate", "Title"])
        self.assertGreater(len(recent_books), 0)
        self.assertLessEqual(len(recent_books), 5)
        self.assertEqual(len(recent_books), len(raw_rows))
        # Check structure of first result
        self.assertEqual(len(recent_books[0]), 3)
        self.assertIsInstance(int(recent_books[0][0]), int)  # BookCollectionID is int represented as string
        # LastUpdate can be a string or None
        self.assertTrue(isinstance(recent_books[0][1], str) or recent_books[0][1] is None)
        self.assertIsInstance(recent_books[0][2], str)  # Title
        # Verify title truncation (should be <= 43 chars)
        self.assertLessEqual(len(recent_books[0][2]), 43)

    def test_book_tags(self):
        rdata, error = au.book_tags(1873)
        self.assertIsNone(error)
        self.assertIn("BookID", rdata)
        self.assertIn("tag_list", rdata)
        self.assertEqual(rdata["BookID"], 1873)
        self.assertIsInstance(rdata["tag_list"], list)
        self.assertGreater(len(rdata["tag_list"]), 0)
        # Verify all tags are strings
        for tag in rdata["tag_list"]:
            self.assertIsInstance(tag, str)

    def test_status_read_utility(self):
        # Test with a book ID that has read records
        s, header, error_list = au.status_read_utility(1873)
        self.assertIsNone(error_list)
        self.assertEqual(header, ["BookCollectionID", "ReadDate", "ReadNote"])
        self.assertIsNotNone(s)
        # Check structure if records exist
        if len(s) > 0:
            self.assertEqual(len(s[0]), 3)  # BookCollectionID, ReadDate, ReadNote
            self.assertIsInstance(s[0][0], int)  # BookCollectionID
            # ReadDate should be datetime or None
            self.assertTrue(isinstance(s[0][1], datetime.date))


if __name__ == '__main__':
    unittest.main()
