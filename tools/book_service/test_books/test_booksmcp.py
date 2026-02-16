#!/usr/bin/env python3
"""
Test Suite for Books MCP Server (HTTP Transport)

This test suite validates the MCP server's HTTP endpoints and MCP tools
when deployed in Docker. It tests both direct HTTP access and MCP protocol
communication over SSE.

Requirements:
    - MCP server running on http://localhost:3005 (port 3005)
    - Install: pip install requests mcp

Usage:
    pytest test_booksmcp.py -v
    or
    python test_booksmcp.py
"""

import asyncio
import json
import sys
import time
import unittest
from typing import Optional, Any

import requests

# Try to import MCP client
try:
    from mcp import ClientSession, types
    from mcp.client.sse import sse_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    print("\n⚠ Warning: MCP client not available")
    print("  Install with: pip install mcp")
    print("  Some tests will be skipped.\n")


# ============================================================================
# Test HTTP Endpoints
# ============================================================================

class TestHTTPEndpoints(unittest.TestCase):
    """Test the HTTP endpoints directly (no MCP protocol)."""

    BASE_URL = "http://localhost:3005"

    @classmethod
    def setUpClass(cls):
        """Check if server is running."""
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
            cls.server_available = response.status_code == 200

            if cls.server_available:
                print(f"\n✓ MCP Server is running at {cls.BASE_URL}")
            else:
                print(f"\n✗ Server returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            cls.server_available = False
            print(f"\n✗ Cannot connect to {cls.BASE_URL}")
            print(f"  Error: {e}")
            print("\n  To start the server:")
            print("    make run-test-mcp-service\n")

    def setUp(self):
        """Skip test if server not available."""
        if not self.server_available:
            self.skipTest("MCP server not running")

    def test_01_health_endpoint(self):
        """Test GET /health endpoint returns OK."""
        response = requests.get(f"{self.BASE_URL}/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OK")
        print("  ✓ Health check passed")

    def test_02_info_endpoint(self):
        """Test GET /info endpoint returns server information."""
        response = requests.get(f"{self.BASE_URL}/info")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validate required fields
        self.assertIn("name", data)
        self.assertIn("version", data)
        self.assertIn("description", data)
        self.assertIn("transport", data)
        self.assertIn("tools", data)

        # Validate tools list
        self.assertIsInstance(data["tools"], list)
        self.assertGreater(len(data["tools"]), 0)

        # Validate tool structure
        for tool in data["tools"]:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)

        # Check for expected tools
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = [
            "search_books_by_title",
            "search_books_by_author",
            "search_books_by_isbn",
            "search_books_by_isbn13",
            "search_books_by_publisher",
            "search_books_by_location",
            "search_books_by_tags",
            "search_books_by_read_date"
        ]

        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names,
                         f"Expected tool '{expected_tool}' not found in tools list")

        print(f"  ✓ Info endpoint returned {len(data['tools'])} tools")

    def test_03_info_endpoint_examples(self):
        """Test that /info endpoint includes usage examples."""
        response = requests.get(f"{self.BASE_URL}/info")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validate examples field exists
        self.assertIn("examples", data)
        self.assertIsInstance(data["examples"], dict)
        self.assertGreater(len(data["examples"]), 0)

        # Validate example structure
        for example_name, example in data["examples"].items():
            self.assertIn("tool", example)
            self.assertIn("arguments", example)
            self.assertIsInstance(example["arguments"], dict)

        print(f"  ✓ Info endpoint includes {len(data['examples'])} examples")

    def test_04_invalid_endpoint(self):
        """Test that invalid endpoints return 404."""
        response = requests.get(f"{self.BASE_URL}/invalid_endpoint")

        self.assertEqual(response.status_code, 404)
        print("  ✓ Invalid endpoint returns 404")


# ============================================================================
# Test MCP Protocol Tools
# ============================================================================

@unittest.skipIf(not MCP_CLIENT_AVAILABLE, "MCP client not available")
class TestMCPTools(unittest.TestCase):
    """Test MCP tools via the MCP protocol endpoint."""

    BASE_URL = "http://localhost:3005"
    server_available = False
    session: Optional[Any] = None

    @classmethod
    def setUpClass(cls):
        """Check if server is running and establish MCP session."""
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
            cls.server_available = response.status_code == 200

            if cls.server_available:
                print(f"\n✓ MCP Server is running at {cls.BASE_URL}")
        except requests.exceptions.RequestException:
            cls.server_available = False
            print(f"\n✗ Cannot connect to {cls.BASE_URL}")

    def setUp(self):
        """Skip test if server not available."""
        if not self.server_available:
            self.skipTest("MCP server not running")

    async def _call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Helper method to call an MCP tool."""
        async with sse_client(f"{self.BASE_URL}/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Call the tool
                result = await session.call_tool(tool_name, arguments)

                # Extract content
                if result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            return json.loads(content_item.text)

                return None

    def test_01_list_tools(self):
        """Test that we can list available tools via MCP."""
        async def run_test():
            async with sse_client(f"{self.BASE_URL}/mcp") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # List tools
                    tools_list = await session.list_tools()

                    self.assertIsNotNone(tools_list)
                    self.assertGreater(len(tools_list.tools), 0)

                    # Check for expected tools
                    tool_names = [tool.name for tool in tools_list.tools]
                    expected_tools = [
                        "search_books_by_title",
                        "search_books_by_author",
                        "search_books_by_isbn"
                    ]

                    for expected_tool in expected_tools:
                        self.assertIn(expected_tool, tool_names)

                    print(f"  ✓ Listed {len(tools_list.tools)} MCP tools")

        asyncio.run(run_test())

    def test_02_search_books_by_title(self):
        """Test search_books_by_title tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_title", {"title": "Python"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["Title"], "Python")

            # Validate results structure
            self.assertIsInstance(result["results"], list)

            if result["count"] > 0:
                # Check first result has expected fields
                first_result = result["results"][0]
                # Common book fields that should be present
                expected_fields = ["Title", "Author"]
                for field in expected_fields:
                    self.assertIn(field, first_result)

            print(f"  ✓ search_books_by_title returned {result['count']} results")

        asyncio.run(run_test())

    def test_03_search_books_by_author(self):
        """Test search_books_by_author tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_author", {"author": "Martin"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["Author"], "Martin")

            # Validate results
            self.assertIsInstance(result["results"], list)

            print(f"  ✓ search_books_by_author returned {result['count']} results")

        asyncio.run(run_test())

    def test_04_search_books_by_isbn(self):
        """Test search_books_by_isbn tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_isbn", {"isbn": "0123456789"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["IsbnNumber"], "0123456789")

            print(f"  ✓ search_books_by_isbn returned {result['count']} results")

        asyncio.run(run_test())

    def test_05_search_books_by_isbn13(self):
        """Test search_books_by_isbn13 tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_isbn13", {"isbn13": "9780123456789"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["IsbnNumber13"], "9780123456789")

            print(f"  ✓ search_books_by_isbn13 returned {result['count']} results")

        asyncio.run(run_test())

    def test_06_search_books_by_publisher(self):
        """Test search_books_by_publisher tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_publisher", {"publisher": "O'Reilly"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["PublisherName"], "O'Reilly")

            print(f"  ✓ search_books_by_publisher returned {result['count']} results")

        asyncio.run(run_test())

    def test_07_search_books_by_location(self):
        """Test search_books_by_location tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_location", {"location": "Office"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["Location"], "Office")

            print(f"  ✓ search_books_by_location returned {result['count']} results")

        asyncio.run(run_test())

    def test_08_search_books_by_tags(self):
        """Test search_books_by_tags tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_tags", {"tags": "programming"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["Tags"], "programming")

            print(f"  ✓ search_books_by_tags returned {result['count']} results")

        asyncio.run(run_test())

    def test_09_search_books_by_read_date(self):
        """Test search_books_by_read_date tool."""
        async def run_test():
            result = await self._call_tool("search_books_by_read_date", {"read_date": "2024"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Validate query
            self.assertEqual(result["query"]["ReadDate"], "2024")

            print(f"  ✓ search_books_by_read_date returned {result['count']} results")

        asyncio.run(run_test())

    def test_10_empty_search_returns_valid_response(self):
        """Test that empty search string returns valid response."""
        async def run_test():
            result = await self._call_tool("search_books_by_title", {"title": "XXXNONEXISTENTXXX"})

            self.assertIsNotNone(result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Empty search should return 0 results, not an error
            self.assertEqual(result["count"], 0)
            self.assertEqual(len(result["results"]), 0)

            print("  ✓ Empty search returns valid empty response")

        asyncio.run(run_test())

    def test_11_special_characters_in_search(self):
        """Test search with special characters."""
        async def run_test():
            # Test with apostrophe (common in titles/authors)
            result = await self._call_tool("search_books_by_author", {"author": "O'Brien"})

            self.assertIsNotNone(result)
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            print("  ✓ Special characters handled correctly")

        asyncio.run(run_test())


# ============================================================================
# Test Response Format and Data Validation
# ============================================================================

@unittest.skipIf(not MCP_CLIENT_AVAILABLE, "MCP client not available")
class TestResponseFormat(unittest.TestCase):
    """Test that responses conform to expected format."""

    BASE_URL = "http://localhost:3005"
    server_available = False

    @classmethod
    def setUpClass(cls):
        """Check if server is running."""
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
            cls.server_available = response.status_code == 200
        except requests.exceptions.RequestException:
            cls.server_available = False

    def setUp(self):
        """Skip test if server not available."""
        if not self.server_available:
            self.skipTest("MCP server not running")

    async def _call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Helper method to call an MCP tool."""
        async with sse_client(f"{self.BASE_URL}/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                if result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            return json.loads(content_item.text)

                return None

    def test_01_response_structure(self):
        """Test that all search responses have consistent structure."""
        async def run_test():
            result = await self._call_tool("search_books_by_title", {"title": "test"})

            # Required fields
            self.assertIn("query", result)
            self.assertIn("count", result)
            self.assertIn("results", result)

            # Type validation
            self.assertIsInstance(result["query"], dict)
            self.assertIsInstance(result["count"], int)
            self.assertIsInstance(result["results"], list)

            # Count should match results length
            self.assertEqual(result["count"], len(result["results"]))

            print("  ✓ Response structure is consistent")

        asyncio.run(run_test())

    def test_02_json_format(self):
        """Test that responses are valid JSON."""
        async def run_test():
            result = await self._call_tool("search_books_by_author", {"author": "test"})

            # If we got here, JSON parsing succeeded
            self.assertIsNotNone(result)

            # Try to re-serialize
            json_str = json.dumps(result)
            self.assertIsInstance(json_str, str)

            # Validate it can be parsed again
            reparsed = json.loads(json_str)
            self.assertEqual(reparsed, result)

            print("  ✓ Responses are valid JSON")

        asyncio.run(run_test())

    def test_03_date_format(self):
        """Test that dates are formatted as strings."""
        async def run_test():
            # Search for books with read dates
            result = await self._call_tool("search_books_by_read_date", {"read_date": "2020"})

            if result["count"] > 0:
                for book in result["results"]:
                    if "ReadDate" in book and book["ReadDate"]:
                        # Should be a string in YYYY-MM-DD format
                        self.assertIsInstance(book["ReadDate"], str)
                        # Basic format check (YYYY-MM-DD)
                        parts = book["ReadDate"].split("-")
                        self.assertEqual(len(parts), 3)

            print("  ✓ Dates are formatted correctly")

        asyncio.run(run_test())


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run the test suite with proper formatting."""
    print("\n" + "="*80)
    print("BOOKS MCP SERVER - TEST SUITE")
    print("="*80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestHTTPEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPTools))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormat))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*80 + "\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
