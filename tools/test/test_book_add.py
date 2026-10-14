import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import urlsplit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

_tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
json.dump({
    "username": "user", "password": "pass", "database": "db",
    "host": "localhost", "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/book/{}", "key": "isbn-key"},
    "api_key": "test-key",
    # Must match test_chat_endpoint.py: whichever test module loads first wins
    # BOOKDB_CONFIG for the whole pytest session.
    "ai_agent": {
        "chat_host": "http://chat-host:1234",
        "chat_model": "test-model",
        "chat_api_key": "test-chat-key",
    },
}, _tmp_config)
_tmp_config.close()
os.environ.setdefault("BOOKDB_CONFIG", _tmp_config.name)

from booksdb import book_add, isbn_com
from booksdb.isbn_com import Endpoint

LOCATIONS = ["Main Collection", "Bedroom", "Storage", "Oversized", "Pets", "Woodwork",
             "Reference", "Birding", "DOWNLOAD"]
# isbndb responses recorded 2026-10-14 for the titles in the first-use assessment
# (books added from a photo of a to-be-read stack), trimmed to the fields the code reads.
FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "isbndb_add_book.json")


def _candidate(**kw):
    c = {"Title": "The Emerald Mile", "Author": "Fedarko, Kevin", "IsbnNumber": "1439159866",
         "IsbnNumber13": "9781439159866", "PublisherName": "Simon and Schuster", "Pages": 448,
         "CopyrightDate": "2014-07-01", "CoverType": "Soft", "binding": "Paperback", "language": "en",
         "title_long": "", "binding_class": "physical"}
    c.update(kw)
    c.setdefault("score", book_add.score_candidate(c, "The Emerald Mile"))
    return c


def _conn_returning(rows, one=(99,)):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.fetchone.return_value = one
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


# Other test modules may have set BOOKDB_CONFIG first with a different isbndb URL; pin it
# so replayed request paths match the fixture keys.
ISBN_CONF = {"url_isbn": "https://example.com/book/{}", "key": "isbn-key"}


class _Replay:
    """Stands in for requests.get, answering from the recorded isbndb fixture."""

    def __init__(self):
        with open(FIXTURE) as f:
            self.responses = json.load(f)
        self.calls = []

    def __call__(self, url, headers=None, params=None, timeout=None):
        key = urlsplit(url).path + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
        self.calls.append(key)
        rec = self.responses.get(key, {"status": 404, "json": {"errorMessage": "Not Found"}})
        resp = MagicMock(status_code=rec["status"])
        resp.json.return_value = rec["json"]
        resp.raise_for_status.side_effect = None if rec["status"] < 400 else isbn_com.requests.HTTPError(str(rec["status"]))
        return resp


##########################################################################
# Normalization
##########################################################################

class TestNormalizeIsbn(unittest.TestCase):
    def test_isbn10_with_hyphens_derives_isbn13(self):
        self.assertEqual(book_add.normalize_isbn("0-593-31507-3"), ("0593315073", "9780593315071"))

    def test_isbn13_derives_isbn10(self):
        self.assertEqual(book_add.normalize_isbn("978-1-4391-5986-6"), ("1439159866", "9781439159866"))

    def test_979_prefix_has_no_isbn10(self):
        self.assertEqual(book_add.normalize_isbn("9791234567896"), (None, "9791234567896"))

    def test_x_check_digit(self):
        self.assertEqual(book_add.normalize_isbn("080442957x")[0], "080442957X")

    def test_bad_checksum_or_length_is_invalid(self):
        self.assertEqual(book_add.normalize_isbn("9781439159867"), (None, None))
        self.assertEqual(book_add.normalize_isbn("1234"), (None, None))
        self.assertEqual(book_add.normalize_isbn(None), (None, None))


class TestAuthors(unittest.TestCase):
    def test_normalize_author(self):
        cases = {
            "Kevin Fedarko": "Fedarko, Kevin",
            "Fedarko, Kevin": "Fedarko, Kevin",
            "Ludwig van Beethoven": "van Beethoven, Ludwig",
            "Martin Luther King Jr.": "King, Martin Luther Jr.",
            "Brad Graham and Kathy McGowan": "Graham, Brad and Kathy McGowan",
            "Acemoglu, Daron and Simon Johnson": "Acemoglu, Daron and Simon Johnson",
            "Daron Acemoglu; Simon Johnson": "Acemoglu, Daron and Simon Johnson",
            "Herzog, Werner,, 1942-": "Herzog, Werner",
            "Plato": "Plato",
            "  Erica   Thompson ": "Thompson, Erica",
            "": "",
        }
        for given, expected in cases.items():
            self.assertEqual(book_add.normalize_author(given), expected, given)

    def test_author_list_in_collection_form(self):
        self.assertEqual(book_add.normalize_author(["Acemoglu, Daron", "Johnson, Simon"]),
                         "Acemoglu, Daron and Simon Johnson")
        self.assertEqual(book_add.normalize_author(["Claude Cohen-Tannoudji", "Jacques Dupont-Roc",
                                                    "Gilbert Grynberg"]),
                         "Cohen-Tannoudji, Claude, Jacques Dupont-Roc and Gilbert Grynberg")

    def test_author_match(self):
        self.assertEqual(book_add._author_match("John Vernon Moore", "Moore, Lucy"), "conflict")
        self.assertEqual(book_add._author_match("Daron Acemoglu", "Acemoglu, Daron and Simon Johnson"), "match")
        self.assertEqual(book_add._author_match("D. Acemoglu", "Acemoglu, Daron"), "match")
        self.assertEqual(book_add._author_match("Smith", "Moore, Lucy"), "none")


class TestTitles(unittest.TestCase):
    def test_titles_match(self):
        self.assertTrue(book_add.titles_match("The Emerald Mile", "The Emerald Mile The Epic Story"))
        self.assertTrue(book_add.titles_match("Rigor of Angels", "The rigor of angels: Borges, Heisenberg"))
        self.assertTrue(book_add.titles_match("The Lost Elements", "Lost Elements, The: The periodic table's shadow side"))
        self.assertFalse(book_add.titles_match("It", "Ithaca"))
        self.assertFalse(book_add.titles_match("Dune", "Children of Dune"))
        self.assertFalse(book_add.titles_match("", "Dune"))

    def test_normalize_title_moves_trailing_article(self):
        self.assertEqual(book_add.normalize_title("Lost Elements, The: The periodic table's shadow side"),
                         "The Lost Elements: The periodic table's shadow side")
        self.assertEqual(book_add.normalize_title("  Gene,  The. "), "The Gene")

    def test_full_title(self):
        self.assertEqual(book_add.full_title("Power and Progress",
                                             "Power and progress: our thousand-year struggle over technology"),
                         "Power and Progress: Our Thousand-Year Struggle over Technology")
        self.assertEqual(book_add.full_title("The Emerald Mile", "The Emerald Mile The Epic Story of the Ride"),
                         "The Emerald Mile: The Epic Story of the Ride")
        self.assertEqual(book_add.full_title("Dune", "Dune Messiah"), "Dune: Messiah")
        self.assertEqual(book_add.full_title("Dune: A Novel", "Dune: whatever"), "Dune: A Novel")
        self.assertEqual(book_add.full_title("Influence", "Influence at work"), "Influence: At Work")
        self.assertEqual(book_add.full_title("Short", "Short: " + "x" * 300), "Short")
        self.assertEqual(book_add.full_title("Power", "Other title: sub"), "Power")


class TestCandidates(unittest.TestCase):
    def test_binding_mapping(self):
        f = Endpoint.binding_to_cover_type
        self.assertEqual(f("Hardcover"), "Hard")
        self.assertEqual(f("Mass Market Paperback"), "Soft")
        self.assertEqual(f("Kindle Edition"), "Digital")
        self.assertEqual(f(None), "")
        self.assertEqual(book_add._binding_class("Audio CD"), "audio")
        self.assertEqual(book_add._binding_class("Preloaded Digital Audio Player"), "audio")
        self.assertEqual(book_add._binding_class("ePub"), "digital")
        self.assertEqual(book_add._binding_class(None), "unknown")

    def test_to_candidate_cleans_isbndb_values(self):
        cand = book_add._to_candidate(Endpoint({}), {
            "title": "Lost elements, the", "authors": ["Herzog, Werner,, 1942-"], "isbn13": "9781439159866",
            "publisher": "Recorded Books,", "pages": 20, "binding": "Paperback", "language": "en"})
        self.assertEqual(cand["Title"], "The Lost elements")
        self.assertEqual(cand["Author"], "Herzog, Werner")
        self.assertEqual(cand["PublisherName"], "Recorded Books")
        self.assertIsNone(cand["Pages"])
        self.assertEqual(cand["pages_dropped"], 20)
        imprint = book_add._to_candidate(Endpoint({}), {"title": "T", "publisher":
                                                        "Harper Business, an imprint of HarperCollins Publishers"})
        self.assertEqual(imprint["PublisherName"], "Harper Business")

    def test_scoring_order(self):
        physical = _candidate()
        kindle = _candidate(binding="Kindle Edition", binding_class="digital", CoverType="Digital")
        audio = _candidate(binding="Audio CD", binding_class="audio", CoverType=None)
        foreign = _candidate(language="fra", IsbnNumber13="9782226031525")
        bundle = _candidate(Title="The Emerald Mile Leader's Edition Success Package")
        scores = [book_add.score_candidate(c, "The Emerald Mile") for c in (physical, kindle, foreign, audio, bundle)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertGreater(scores[0], book_add.MIN_CONFIDENT_SCORE)

    def test_rank_keeps_isbndb_order_among_ties_and_dedupes(self):
        a, b = _candidate(IsbnNumber13="9780000000001"), _candidate(IsbnNumber13="9780000000002")
        ranked = book_add._rank([a, b, dict(a)], "The Emerald Mile")
        self.assertEqual([c["IsbnNumber13"] for c in ranked], ["9780000000001", "9780000000002"])


##########################################################################
# isbndb lookups (isbndb replayed from the recorded fixture)
##########################################################################

class TestLookupMetadata(unittest.TestCase):
    def setUp(self):
        self.replay = _Replay()
        for p in (patch.object(isbn_com.requests, "get", self.replay), patch.object(book_add, "isbn_conf", ISBN_CONF)):
            p.start()
            self.addCleanup(p.stop)

    def test_isbn_lookup(self):
        res = book_add.lookup_metadata(isbn="0-385-49532-3")
        self.assertEqual(res["source"], "isbn")
        cand = res["candidates"][0]
        self.assertEqual(cand["IsbnNumber13"], "9780385495325")
        self.assertEqual(cand["Author"], "Singh, Simon")

    def test_invalid_isbn(self):
        res = book_add.lookup_metadata(isbn="123")
        self.assertEqual(res["candidates"], [])
        self.assertIn("Not a valid ISBN", res["error"])

    def test_semicolon_joined_authors_still_match(self):
        """isbndb lists "Daron Acemoglu; Simon Johnson" -- the 3.4.0 parser read the surname as
        Johnson and filtered the right book out."""
        res = book_add.lookup_metadata(title="Power and Progress", author="Daron Acemoglu", limit=20)
        self.assertEqual(res["search"], "search")
        self.assertIn("9781541702530", [c["IsbnNumber13"] for c in res["candidates"]])

    def test_fallback_chain_when_nothing_matches(self):
        res = book_add.lookup_metadata(title="The Witches of Abiquiu", author="Gutierrez")
        self.assertEqual(res["candidates"], [])
        self.assertEqual(len(self.replay.calls), 3)  # search, title column, title + surname text

    def test_rate_limit_retry(self):
        ok = MagicMock(status_code=200)
        ok.json.return_value = {"books": []}
        with patch.object(isbn_com.requests, "get", side_effect=[MagicMock(status_code=429), ok]) as get, \
                patch.object(isbn_com.time, "sleep") as sleep:
            self.assertEqual(Endpoint({"url_isbn": "https://x/book/{}"}).search_books_by_title("T"), [])
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once()


@patch.object(book_add.api_util, "get_valid_locations", return_value=(LOCATIONS, None, ["Location"], None))
@patch.object(book_add, "find_duplicates", return_value=[])
class TestAcceptance(unittest.TestCase):
    """The assessment's suggested acceptance tests, replayed from recorded isbndb data."""

    def setUp(self):
        for p in (patch.object(isbn_com.requests, "get", _Replay()), patch.object(book_add, "isbn_conf", ISBN_CONF)):
            p.start()
            self.addCleanup(p.stop)

    def test_1_code_book_never_digital(self, *_):
        res = book_add.resolve_book({"Title": "The Code Book", "Author": "Simon Singh", "CoverType": "Soft"})
        self.assertEqual(res["status"], "needs_review")  # three equally likely paperbacks
        self.assertEqual(res["record"]["Location"], "Main Collection")
        shown = res["candidates"][:book_add.COMPACT_CANDIDATES]
        self.assertTrue(all(c["CoverType"] == "Soft" for c in shown))
        self.assertIn("9780385495325", [c["IsbnNumber13"] for c in shown])  # the Anchor paperback

    def test_2_hundredth_meridian_not_the_cassette(self, *_):
        res = book_add.resolve_book({"Title": "Beyond the Hundredth Meridian", "Author": "Wallace Stegner"})
        self.assertNotIn("9785557119832", [c["IsbnNumber13"] for c in res["candidates"][:3]])
        self.assertTrue(all(c["binding_class"] == "physical" for c in res["candidates"][:3]))

    def test_3_author_conflict(self, *_):
        res = book_add.resolve_book({"Title": "Into the Canyon", "Author": "John Vernon Moore", "CoverType": "Hard"})
        self.assertEqual(res["status"], "needs_review")
        self.assertIn("author_conflict", [r["reason"] for r in res["review"]])
        self.assertNotIn("IsbnNumber13", res["record"])  # nothing filled from the conflicting edition

    def test_4_power_and_progress_found(self, *_):
        res = book_add.resolve_book({"Title": "Power and Progress", "Author": "Daron Acemoglu", "CoverType": "Hard"})
        self.assertTrue(res["candidates"])
        self.assertNotIn("no_match", [r["reason"] for r in res["review"]])

    def test_6_cover_type_filters_candidates(self, *_):
        res = book_add.resolve_book({"Title": "The Lost Elements", "Author": "Marco Fontani", "CoverType": "Hard"})
        self.assertEqual(res["status"], "ready")
        self.assertEqual(res["record"]["CoverType"], "Hard")
        self.assertEqual(res["record"]["Title"], "The Lost Elements: The Periodic Table's Shadow Side")

    def test_7_compact_response_size(self, *_):
        for fields in ({"Title": "The Lost Elements", "Author": "Marco Fontani", "CoverType": "Hard"},
                       {"Title": "Power and Progress", "Author": "Daron Acemoglu", "CoverType": "Hard"}):
            size = len(json.dumps(book_add.summarize(book_add.resolve_book(fields))))
            self.assertLess(size, 1500, fields)

    def test_8_guessed_digital_never_moves_location(self, *_):
        cands = [_candidate(binding="Kindle Edition", binding_class="digital", CoverType="Digital")]
        with patch.object(book_add, "lookup_metadata", return_value={"source": "title_search", "candidates": cands}):
            res = book_add.resolve_book({"Title": "The Emerald Mile", "Author": "Kevin Fedarko"})
        self.assertEqual(res["record"]["Location"], "Main Collection")
        self.assertNotEqual(res["record"].get("CoverType"), "Digital")

    def test_bundle_edition_goes_to_review(self, *_):
        res = book_add.resolve_book({"Title": "It's the Manager", "Author": "Jim Clifton", "CoverType": "Hard"})
        self.assertEqual(res["status"], "needs_review")

    def test_co_authors_added_from_isbndb(self, *_):
        res = book_add.resolve_book({"Title": "First Impressions", "Author": "David Weber", "CoverType": "Hard"})
        self.assertEqual(res["status"], "ready")
        self.assertIn("deBuys", res["record"]["Author"].replace("DeBuys", "deBuys"))
        self.assertEqual(res["sources"]["Author"], "isbndb")

    def test_no_match_needs_review(self, *_):
        res = book_add.resolve_book({"Title": "The Witches of Abiquiu", "Author": "Gutierrez", "CoverType": "Soft"})
        self.assertEqual(res["status"], "needs_review")
        self.assertEqual([r["reason"] for r in res["review"]], ["no_match"])


##########################################################################
# Duplicates
##########################################################################

class TestFindDuplicates(unittest.TestCase):
    def test_match_kinds(self):
        rows = [
            (1, "Emerald Mile", "Fedarko, Kevin", "Soft", "Main Collection", "1439159866", ""),  # ISBN-10 only
            (2, "The Emerald Mile: The Epic Story", "Fedarko, Kevin", "Hard", "Main Collection", None, None),
            (3, "Other Book", "Fedarko, Kevin", "Hard", "Main Collection", None, None),  # surname only
            (4, "Emerald Mile, The", "Someone, Else", "Hard", "Main Collection", None, None),
        ]
        conn, cursor = _conn_returning(rows)
        with patch.object(book_add.psycopg2, "connect", return_value=conn):
            dups = book_add.find_duplicates({"Title": "The Emerald Mile", "Author": "Fedarko, Kevin",
                                             "IsbnNumber13": "9781439159866", "IsbnNumber": "1439159866"},
                                            exclude_id=9)
        self.assertEqual([(d["BookId"], d["match"]) for d in dups],
                         [(1, "isbn"), (2, "title_author"), (4, "title_only")])
        sql, params = cursor.execute.call_args[0]
        self.assertIn("Title ILIKE", sql)
        self.assertEqual(params[-1], 9)
        conn.close.assert_called_once()

    def test_nothing_to_match_on(self):
        self.assertEqual(book_add.find_duplicates({}), [])


@patch.object(book_add.api_util, "get_valid_locations", return_value=(LOCATIONS, None, ["Location"], None))
class TestResolveBook(unittest.TestCase):
    def resolve(self, fields, candidates=None, source="isbn", duplicates=None, lookup=True):
        info = {"source": source, "candidates": candidates or []}
        with patch.object(book_add, "lookup_metadata", return_value=info) as mock_lookup, \
                patch.object(book_add, "find_duplicates", return_value=duplicates or []):
            res = book_add.resolve_book(fields, lookup=lookup)
        return res, mock_lookup

    def test_isbn_path_fills_blanks_caller_wins(self, _):
        res, _ = self.resolve({"IsbnNumber13": "978-1-4391-5986-6", "Title": "My Title", "Pages": "500"},
                              [_candidate()])
        rec = res["record"]
        self.assertEqual(res["status"], "ready")
        self.assertEqual(rec["Title"], "My Title")
        self.assertEqual(rec["Pages"], 500)
        self.assertEqual(rec["PublisherName"], "Simon and Schuster")
        self.assertEqual(rec["IsbnNumber"], "1439159866")
        self.assertEqual(rec["Location"], "Main Collection")
        self.assertEqual(res["sources"]["PublisherName"], "isbndb")
        self.assertEqual(res["sources"]["Location"], "default")

    def test_isbn_path_digital_moves_to_download(self, _):
        res, _ = self.resolve({"IsbnNumber13": "9781439159866"},
                              [_candidate(CoverType="Digital", binding="Kindle Edition", binding_class="digital")])
        self.assertEqual(res["record"]["Location"], "DOWNLOAD")

    def test_isbn_path_author_mismatch_warns(self, _):
        res, _ = self.resolve({"IsbnNumber13": "9781439159866", "Author": "Someone Else"}, [_candidate()])
        self.assertEqual(res["record"]["Author"], "Else, Someone")
        self.assertTrue(any("isbndb lists" in w for w in res["warnings"]))

    def test_isbn_not_on_isbndb_uses_caller_fields(self, _):
        res, _ = self.resolve({"IsbnNumber13": "9781439159866", "Title": "T", "Author": "A"})
        self.assertEqual(res["status"], "ready")
        self.assertTrue(any("no record for this ISBN" in w for w in res["warnings"]))

    def test_title_search_single_clear_edition_is_ready(self, _):
        res, mock_lookup = self.resolve({"Title": "The Emerald Mile", "Author": "Kevin Fedarko", "CoverType": "Soft"},
                                        [_candidate()], source="title_search")
        mock_lookup.assert_called_once_with(title="The Emerald Mile", author="Kevin Fedarko", limit=20)
        self.assertEqual(res["status"], "ready")
        self.assertEqual(res["record"]["IsbnNumber13"], "9781439159866")
        self.assertTrue(any("title search" in w for w in res["warnings"]))

    def test_hard_and_soft_without_cover_type_needs_review(self, _):
        cands = [_candidate(), _candidate(IsbnNumber13="9781439159859", CoverType="Hard", binding="Hardcover")]
        res, _ = self.resolve({"Title": "The Emerald Mile", "Author": "Kevin Fedarko"}, cands, source="title_search")
        self.assertEqual(res["status"], "needs_review")
        self.assertNotIn("IsbnNumber13", res["record"])

    def test_close_editions_from_different_publishers_need_review(self, _):
        cands = [_candidate(), _candidate(IsbnNumber13="9780000000002", PublisherName="Other Press")]
        res, _ = self.resolve({"Title": "The Emerald Mile", "Author": "Kevin Fedarko", "CoverType": "Soft"},
                              cands, source="title_search")
        self.assertEqual(res["status"], "needs_review")
        self.assertIn("equally likely", res["message"])

    def test_review_beats_confirm_second_copy_but_not_duplicate(self, _):
        cands = [_candidate(Author="Moore, Lucy")]
        dup = {"BookId": 7, "Title": "T", "Author": "Moore, Lucy", "CoverType": "Soft", "match": "title_author"}
        res, _ = self.resolve({"Title": "The Emerald Mile", "Author": "John Moore", "CoverType": "Hard"},
                              cands, source="title_search", duplicates=[dup])
        self.assertEqual(res["status"], "needs_review")
        dup["CoverType"] = "Hard"
        res, _ = self.resolve({"Title": "The Emerald Mile", "Author": "John Moore", "CoverType": "Hard"},
                              cands, source="title_search", duplicates=[dup])
        self.assertEqual(res["status"], "duplicate")

    def test_digital_goes_to_download(self, _):
        res, _ = self.resolve({"Title": "T", "Author": "A", "CoverType": "digital", "Location": "Bedroom"},
                              source="title_search")
        self.assertEqual(res["record"]["Location"], "DOWNLOAD")

    def test_download_requires_digital(self, _):
        res, _ = self.resolve({"Title": "T", "Author": "A", "CoverType": "Hard", "Location": "DOWNLOAD"})
        self.assertEqual(res["status"], "invalid")

    def test_unknown_location_and_cover_invalid(self, _):
        res, _ = self.resolve({"Title": "T", "Author": "A", "Location": "Garage", "CoverType": "Scroll"})
        self.assertEqual(res["status"], "invalid")
        self.assertEqual(len(res["errors"]), 2)

    def test_missing_author_invalid(self, _):
        res, _ = self.resolve({"Title": "T"})
        self.assertEqual(res["status"], "invalid")
        self.assertIn("Author is required", res["message"])

    def test_bad_values_dropped_with_warnings(self, _):
        res, _ = self.resolve({"Title": "T" * 250, "Author": "A", "IsbnNumber": "123", "Pages": "lots",
                               "CopyrightDate": "someday"})
        rec = res["record"]
        self.assertEqual(len(rec["Title"]), 200)
        self.assertNotIn("Pages", rec)
        self.assertNotIn("CopyrightDate", rec)
        self.assertNotIn("IsbnNumber", rec)

    def test_duplicate_rules(self, _):
        isbn_dup = {"BookId": 7, "Author": "A", "CoverType": "Soft", "match": "isbn"}
        same = {"BookId": 7, "Author": "A", "CoverType": "Soft; 22x28", "match": "title_author"}
        cases = [
            ({"IsbnNumber13": "9781439159866", "Title": "T", "Author": "A", "CoverType": "Hard"}, isbn_dup, "duplicate"),
            ({"Title": "T", "Author": "A", "CoverType": "Soft"}, same, "duplicate"),
            ({"Title": "T", "Author": "A"}, same, "duplicate"),
            ({"Title": "T", "Author": "A", "CoverType": "Hard"}, same, "confirm_second_copy"),
        ]
        for fields, dup, expected in cases:
            res, _ = self.resolve(fields, duplicates=[dict(dup)], lookup=False)
            self.assertEqual(res["status"], expected, fields)

    def test_guessed_isbn_match_is_not_a_hard_duplicate(self, _):
        dup = {"BookId": 7, "Author": "Fedarko, Kevin", "CoverType": "Soft", "match": "isbn"}
        res, _ = self.resolve({"Title": "The Emerald Mile", "Author": "Kevin Fedarko", "CoverType": "Hard"},
                              [_candidate(CoverType="Hard", binding="Hardcover")], source="title_search",
                              duplicates=[dup])
        self.assertEqual(res["status"], "confirm_second_copy")

    def test_title_only_match_warns(self, _):
        dup = {"BookId": 1164, "Title": "The Witches of Abiquiu", "Author": "Ebright, Malcolm",
               "CoverType": "Soft", "match": "title_only"}
        res, _ = self.resolve({"Title": "The Witches of Abiquiu", "Author": "Gutierrez"}, duplicates=[dup],
                              lookup=False)
        self.assertEqual(res["status"], "ready")
        self.assertTrue(any("Possible duplicate" in w for w in res["warnings"]))


##########################################################################
# Summaries, add, batches, update
##########################################################################

class TestSummarize(unittest.TestCase):
    def test_compact_drops_empties_and_trims_candidates(self):
        result = {"status": "needs_review", "message": "m", "record": {"Title": "T"}, "sources": {},
                  "missing": [], "warnings": ["w"], "review": [{"reason": "edition_choice"}],
                  "duplicates": [], "candidates": [_candidate()] * 5, "lookup": {"search": "title"}}
        out = book_add.summarize(result)
        self.assertNotIn("missing", out)
        self.assertNotIn("lookup", out)
        self.assertEqual(len(out["candidates"]), 3)
        self.assertIsInstance(out["candidates"][0], str)
        verbose = book_add.summarize(result, verbose=True)
        self.assertEqual(verbose["search"], "title")
        self.assertEqual(len(verbose["candidates"]), 5)


class TestAddBook(unittest.TestCase):
    def _resolved(self, status, **record):
        rec = {"Title": "T", "Author": "A", "Location": "Main Collection", "Recycled": 0}
        rec.update(record)
        return {"status": status, "message": "m", "record": rec}

    def test_ready_is_inserted(self):
        with patch.object(book_add, "resolve_book", return_value=self._resolved("ready")), \
                patch.object(book_add, "add_book_record", return_value=99) as mock_add:
            res = book_add.add_book({"Title": "T"})
        mock_add.assert_called_once()
        self.assertEqual((res["status"], res["BookId"]), ("added", 99))

    def test_refused_statuses_not_inserted(self):
        for status in ("duplicate", "invalid", "needs_review", "confirm_second_copy"):
            with patch.object(book_add, "resolve_book", return_value=self._resolved(status)), \
                    patch.object(book_add, "add_book_record") as mock_add:
                res = book_add.add_book({"Title": "T"}, confirm_second_copy=(status != "confirm_second_copy"))
            mock_add.assert_not_called()
            self.assertEqual(res["status"], status)

    def test_confirmed_second_copy_is_inserted(self):
        with patch.object(book_add, "resolve_book", return_value=self._resolved("confirm_second_copy")), \
                patch.object(book_add, "add_book_record", return_value=5):
            self.assertEqual(book_add.add_book({"Title": "T"}, confirm_second_copy=True)["status"], "added")

    def test_accept_as_is_skips_lookup(self):
        with patch.object(book_add, "resolve_book", return_value=self._resolved("ready")) as mock_resolve, \
                patch.object(book_add, "add_book_record", return_value=5):
            book_add.add_book({"Title": "T"}, accept_as_is=True)
        mock_resolve.assert_called_once_with({"Title": "T"}, lookup=False)

    def test_add_book_record_inserts_commits_and_embeds_note(self):
        conn, cursor = _conn_returning([])
        with patch.object(book_add.psycopg2, "connect", return_value=conn), \
                patch.object(book_add.api_util, "upsert_book_note_embedding") as mock_embed:
            book_id = book_add.add_book_record({"Title": "T", "Author": "A", "Location": "Main Collection",
                                                "CopyrightDate": "1999", "BookNote": " note "})
        self.assertEqual(book_id, 99)
        self.assertEqual(cursor.execute.call_args[0][1][2], "1999-01-01 00:00:00")
        conn.commit.assert_called_once()
        mock_embed.assert_called_once_with(conn, 99, "note")


class TestBatches(unittest.TestCase):
    def test_limits(self):
        self.assertIn("error", book_add.check_books([]))
        self.assertIn("error", book_add.add_books([{"Title": "T"}] * (book_add.MAX_BATCH + 1)))

    def test_check_books_rows_and_in_batch_repeat(self):
        def fake(fields):
            return {"status": "ready", "message": "Ready to add.", "record": dict(fields), "warnings": []}
        with patch.object(book_add, "resolve_book", side_effect=fake):
            out = book_add.check_books([{"Title": "Dune", "Author": "Frank Herbert"},
                                        {"Title": "Emma", "Author": "Jane Austen"},
                                        {"Title": "Dune: Deluxe", "Author": "Herbert, Frank"}])
        self.assertEqual(out["by_status"], {"ready": 3})
        self.assertEqual(out["items"][2]["warnings"], ["Same book as item 0 in this batch"])

    def test_add_books_passes_flags_and_isolates_errors(self):
        calls = []

        def fake(fields, confirm_second_copy=False, accept_as_is=False):
            calls.append((fields, confirm_second_copy, accept_as_is))
            if fields["Title"] == "Boom":
                raise RuntimeError("db down")
            return {"status": "added", "message": "m", "record": fields, "BookId": 1}
        with patch.object(book_add, "add_book", side_effect=fake):
            out = book_add.add_books([{"Title": "A", "confirm_second_copy": True}, {"Title": "Boom"},
                                      {"Title": "C", "accept_as_is": True}])
        self.assertEqual(calls[0], ({"Title": "A"}, True, False))
        self.assertEqual(calls[2], ({"Title": "C"}, False, True))
        self.assertEqual(out["by_status"], {"added": 2, "error": 1})


CURRENT = ("First Impressions", "Weber, David J.", None, None, "9780300215045", "Yale University Press",
           "Hard", 339, "Main Collection", None, 0)


@patch.object(book_add.api_util, "get_valid_locations", return_value=(LOCATIONS, None, ["Location"], None))
class TestUpdateBook(unittest.TestCase):
    def test_locations_are_ui_list_plus_in_use(self, mock_locations):
        mock_locations.return_value = (["Main Collection", "Astronomy"], None, ["Location"], None)
        locs = book_add.list_locations()["locations"]
        self.assertIn("Bedroom", locs)  # in the UI list, though no book uses it
        self.assertIn("Astronomy", locs)  # in use, though not in the UI list


    def _run(self, fields, dry_run=False, duplicates=None):
        conn, cursor = _conn_returning([], one=CURRENT)
        with patch.object(book_add.psycopg2, "connect", return_value=conn), \
                patch.object(book_add, "find_duplicates", return_value=duplicates or []), \
                patch.object(book_add.api_util, "upsert_book_note_embedding") as embed:
            res = book_add.update_book(3038, fields, dry_run=dry_run)
        return res, cursor, embed

    def test_update_changed_fields_only(self, _):
        res, cursor, _ = self._run({"Author": ["David J. Weber", "William deBuys"], "Pages": None})
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["changes"], {"Author": {"before": "Weber, David J.",
                                                     "after": "Weber, David J. and William deBuys"}})
        sql, params = cursor.execute.call_args[0]
        self.assertTrue(sql.startswith("UPDATE books SET Author = %s WHERE BookId = %s"))
        self.assertEqual(params, ["Weber, David J. and William deBuys", 3038])

    def test_dry_run_writes_nothing(self, _):
        res, cursor, _ = self._run({"Pages": "350"}, dry_run=True)
        self.assertEqual(res["status"], "dry_run")
        self.assertEqual(res["changes"]["Pages"], {"before": 339, "after": 350})
        self.assertFalse(any("UPDATE" in str(c) for c in cursor.execute.call_args_list))

    def test_validation_and_isbn_clash(self, _):
        res, _, _ = self._run({"Location": "DOWNLOAD"})
        self.assertEqual(res["status"], "invalid")
        res, _, _ = self._run({"IsbnNumber13": "9781439159866"}, duplicates=[{"BookId": 5, "match": "isbn"}])
        self.assertIn("Another book already has this ISBN", res["message"])

    def test_clear_optional_field_and_refresh_note_embedding(self, _):
        res, _, embed = self._run({"PublisherName": "", "BookNote": "New note"})
        self.assertEqual(res["changes"]["PublisherName"]["after"], None)
        embed.assert_called_once()

    def test_unchanged_and_missing(self, _):
        res, _, _ = self._run({"Pages": 339})
        self.assertEqual(res["status"], "unchanged")
        conn, _ = _conn_returning([], one=None)
        with patch.object(book_add.psycopg2, "connect", return_value=conn):
            self.assertEqual(book_add.update_book(1, {"Pages": 3})["status"], "invalid")


class TestReadDateSearch(unittest.TestCase):
    """search_books_by_read_date("2026-10") failed with "operator does not exist: date ~~* unknown"
    (reported in the add-book assessment): ReadDate is a date column, so ILIKE needs a text cast."""

    def test_partial_read_date_casts_to_text(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value  # books_search_utility doesn't use the cursor as a context manager
        cursor.fetchall.return_value = []
        with patch.object(book_add.api_util.psycopg2, "connect", return_value=conn):
            book_add.api_util.books_search_utility({"ReadDate": "2026-10"})
        sql, params = cursor.execute.call_args[0]
        self.assertIn("b.ReadDate::text ILIKE %s", sql)
        self.assertIn("%2026-10%", params)


if __name__ == "__main__":
    unittest.main()
