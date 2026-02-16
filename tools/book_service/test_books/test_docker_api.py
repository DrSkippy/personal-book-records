import json
import unittest
import os
from io import BytesIO

import requests
from booksdb import api_util as au

ENDPOINT = "http://localhost:9999"
EXAMPLES_PATH = "./example_json_payloads"


class TestAppFunctions(unittest.TestCase):

    def setUp(self):
        ep = ENDPOINT + "/add_books"
        print(f"QUERY={ep}")
        with open(f"{EXAMPLES_PATH}/test_add_books.json", "r") as infile:
            data = json.load(infile)
        r = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(r.json())
        self.assertTrue(r.status_code == 200)
        self.book_id_list = [x["BookId"] for x in r.json()["add_books"]]

    def test_configuration(self):
        ep = ENDPOINT + "/configuration"
        print(f"QUERY={ep}")
        r = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(r.json())
        self.assertTrue(r.status_code == 200)

    def test_configuration1(self):
        ep = ENDPOINT + "/configuration"
        print(f"QUERY={ep}")
        r = requests.get(ep)
        print(r.status_code)
        self.assertTrue(r.status_code == 401)

    def test_locations(self):
        ep = ENDPOINT + "/valid_locations"
        print(f"QUERY={ep}")
        r = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(r.json())
        self.assertTrue(r.status_code == 200)

    def test_books_search(self):
        ep = ENDPOINT + "/books_search"
        ep1 = ep + "?Author=lewis"
        print(f"QUERY={ep1}")
        res1 = requests.post(ep1, headers={'x-api-key': f'{au.API_KEY}'})
        self.assertGreater(len(res1.json()["data"]), 0)
        print(res1.json())
        self.assertTrue(res1.status_code == 200)
        ep2 = ep + "?PublisherName=dover"
        res2 = requests.post(ep2, headers={'x-api-key': f'{au.API_KEY}'})
        self.assertGreater(len(res2.json()["data"]), 0)
        print(res2.json())
        self.assertTrue(res2.status_code == 200)
        ep3 = ep + "?Tags=science"
        print(f"QUERY={ep3}")
        res3 = requests.post(ep3, headers={'x-api-key': f'{au.API_KEY}'})
        self.assertGreater(len(res3.json()["data"]), 0)
        print(res3.json())
        self.assertTrue(res3.status_code == 200)
        ep4 = ep + "?note=bought"
        print(f"QUERY={ep4}")
        res4 = requests.post(ep4, headers={'x-api-key': f'{au.API_KEY}'})
        self.assertGreater(len(res4.json()["data"]), 0)
        print(res4.json())
        self.assertTrue(res4.status_code == 200)

    def test_tag_counts(self):
        ep = ENDPOINT + "/tag_counts/deleteme"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_update_tag_value(self):
        ep = ENDPOINT + "/update_tag_value/deleteme/delete_me"
        print(f"QUERY={ep}")
        res = requests.put(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_tags_search(self):
        ep = ENDPOINT + "/tags_search/apple"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        ep2 = ENDPOINT + "/tags_search/dog"
        res2 = requests.get(ep2, headers={'x-api-key': f'{au.API_KEY}'})
        print(res2.json())
        self.assertTrue(res2.status_code == 200)

    def test_tag_maintenance(self):
        ep = ENDPOINT + "/tag_maintenance"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_add_read_dates(self):
        book_id_list = self.book_id_list
        ep = ENDPOINT + "/add_read_dates"
        print(f"QUERY={ep}")
        with open(f"{EXAMPLES_PATH}/test_update_read_dates.json", "r") as infile:
            data = json.load(infile)
        for x, r in zip(data, book_id_list):
            x["BookId"] = r
        res = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_update_book_note_status(self):
        id = self.book_id_list[0]
        ep = ENDPOINT + "/update_book_note_status"
        print(f"QUERY={ep}")
        with open(f"{EXAMPLES_PATH}/test_update_book_note_status.json", "r") as infile:
            data = json.load(infile)
        data["BookId"] = int(id)
        res = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_summary_books_read_by_year(self):
        year = 2015
        ep = ENDPOINT + f"/summary_books_read_by_year/{year}"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        ep1 = ENDPOINT + "/summary_books_read_by_year"
        print(f"QUERY={ep1}")
        res1 = requests.get(ep1, headers={'x-api-key': f'{au.API_KEY}'})
        print(res1.json())
        self.assertTrue(res1.status_code == 200)

    def test_books_read(self):
        year = 2015
        ep = ENDPOINT + f"/books_read/{year}"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        ep1 = ENDPOINT + "/books_read"
        print(f"QUERY={ep1}")
        res1 = requests.get(ep1, headers={'x-api-key': f'{au.API_KEY}'})
        print(res1.json())
        self.assertTrue(res1.status_code == 200)

    def test_add_tags(self):
        book_ids = self.book_id_list
        ep = ENDPOINT + "/add_tag"
        print(f"QUERY={ep}")
        for book_id in book_ids:
            res = requests.put(ep + f"/{book_id}/deleteme", headers={'x-api-key': f'{au.API_KEY}'})
            print(res.json())
            self.assertTrue(res.status_code == 200)

    def test_tags(self):
        id = 2
        ep = ENDPOINT + f"/tags/{id}"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_status_read(self):
        id = 1696
        ep = ENDPOINT + f"/status_read/{id}"
        print(f"QUERY={ep}")
        res = requests.get(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)

    def test_add_image_with_valid_url(self):
        """Test adding an image with a valid URL"""
        book_id = self.book_id_list[0]
        ep = ENDPOINT + "/add_image"
        print(f"QUERY={ep}")

        # Use a valid test image URL
        data = {
            "BookId": int(book_id),
            "Name": "test_image.jpg",
            "Url": "https://httpbin.org/image/jpeg",
            "ImageType": "cover-face"
        }

        res = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        self.assertIn("add_image", res.json())
        self.assertIn("ImageId", res.json()["add_image"])

    def test_add_image_with_invalid_url(self):
        """Test adding an image with an invalid URL returns error"""
        book_id = self.book_id_list[0]
        ep = ENDPOINT + "/add_image"
        print(f"QUERY={ep}")

        data = {
            "BookId": int(book_id),
            "Name": "test_image.jpg",
            "Url": "https://invalid-url-that-does-not-exist-12345.com/image.jpg",
            "ImageType": "cover-face"
        }

        res = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 400)
        self.assertIn("error", res.json())

    def test_add_image_missing_book_id(self):
        """Test adding an image without BookId returns error"""
        ep = ENDPOINT + "/add_image"
        print(f"QUERY={ep}")

        data = {
            "Name": "test_image.jpg",
            "Url": "https://httpbin.org/image/jpeg",
            "ImageType": "cover-face"
        }

        res = requests.post(ep, json=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 400)
        self.assertIn("error", res.json())

    def test_add_image_no_api_key(self):
        """Test adding an image without API key returns 401"""
        book_id = self.book_id_list[0]
        ep = ENDPOINT + "/add_image"
        print(f"QUERY={ep}")

        data = {
            "BookId": int(book_id),
            "Name": "test_image.jpg",
            "Url": "https://httpbin.org/image/jpeg",
            "ImageType": "cover-face"
        }

        res = requests.post(ep, json=data)
        print(res.status_code)
        self.assertTrue(res.status_code == 401)

    def test_upload_image(self):
        """Test uploading an image file"""
        ep = ENDPOINT + "/upload_image"
        print(f"QUERY={ep}")

        # Create a small test image in memory (1x1 pixel PNG)
        test_image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        files = {'file': ('test_upload.png', BytesIO(test_image_data), 'image/png')}

        res = requests.post(ep, files=files, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        self.assertIn("upload_image", res.json())
        self.assertEqual(res.json()["upload_image"]["status"], "success")
        self.assertIn("filename", res.json()["upload_image"])
        self.assertIn("path", res.json()["upload_image"])

    def test_upload_image_with_custom_filename(self):
        """Test uploading an image file with custom filename"""
        ep = ENDPOINT + "/upload_image"
        print(f"QUERY={ep}")

        # Create a small test image in memory
        test_image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        files = {'file': ('original.png', BytesIO(test_image_data), 'image/png')}
        data = {'filename': 'custom_test_name.png'}

        res = requests.post(ep, files=files, data=data, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 200)
        self.assertEqual(res.json()["upload_image"]["filename"], "custom_test_name.png")

    def test_upload_image_no_file(self):
        """Test uploading without a file returns error"""
        ep = ENDPOINT + "/upload_image"
        print(f"QUERY={ep}")

        res = requests.post(ep, headers={'x-api-key': f'{au.API_KEY}'})
        print(res.json())
        self.assertTrue(res.status_code == 400)
        self.assertIn("error", res.json())

    def test_upload_image_no_api_key(self):
        """Test uploading image without API key returns 401"""
        ep = ENDPOINT + "/upload_image"
        print(f"QUERY={ep}")

        test_image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        files = {'file': ('test.png', BytesIO(test_image_data), 'image/png')}

        res = requests.post(ep, files=files)
        print(res.status_code)
        self.assertTrue(res.status_code == 401)

    @classmethod
    def tearDownClass(cls):
        print("""For DB Cleanup:

        USE book_collection;
        DELETE FROM tag_labels where label="delete_me";
        DELETE FROM books WHERE PublisherName="Printerman";
        DELETE FROM books_read WHERE ReadDate="1945-10-19";
        DELETE FROM images WHERE Name LIKE "test_%";
        DELETE FROM images WHERE Name LIKE "custom_test%";

        # Also delete test uploaded files from filesystem if needed:
        # rm /var/www/html/resources/books/test_upload.png
        # rm /var/www/html/resources/books/custom_test_name.png
        """)


if __name__ == "__main__":
    unittest.main()
