# Getting Started with Book Service API

This guide will help you make your first API calls and understand the basics of authentication and request formatting.

## Prerequisites

- Access to a running Book Service API instance
- An API key (configured in `configuration.json` or `API_KEY` environment variable)
- Command-line tool (`curl`) or API client (Postman, Insomnia)

## Authentication Setup

### Step 1: Obtain Your API Key

The API key is configured when the service is deployed. Check your `configuration.json` file or ask your system administrator.

### Step 2: Include API Key in Requests

All requests (except `/favicon.ico`) must include the `x-api-key` header:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/endpoint
```

## Your First Requests

### Test Connection and Authentication

Verify your API key works:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

**Expected Response (200 OK)**:
```json
{
  "version": "0.16.2",
  "configuration": {
    "user": "books_user",
    "db": "book_collection",
    "host": "192.168.1.90",
    "port": 3306,
    "passwd": "******"
  },
  "isbn_configuration": {
    "url_isbn": "https://api.isbndb.com/book/",
    "key": "******"
  },
  "date": "2024-01-15T10:30"
}
```

### Get Valid Locations

See where books can be stored:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/valid_locations
```

**Response**:
```json
{
  "data": [
    ["Main Collection"],
    ["Bedroom"],
    ["Storage"]
  ],
  "header": ["Location"]
}
```

### Search for Books

Search by author:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8084/books_search?Author=Tolkien"
```

**Response**:
```json
{
  "data": [
    [1234, "The Hobbit", "Tolkien, J.R.R.", "1937-01-01", 300, "Main Collection", 0],
    [1235, "The Lord of the Rings", "Tolkien, J.R.R.", "1954-01-01", 1178, "Main Collection", 0]
  ],
  "header": ["BookId", "Title", "Author", "CopyrightDate", "Pages", "Location", "Recycled"]
}
```

### Get Recently Updated Books

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/recent/5
```

### Get Complete Book Record

Retrieve all information about a book:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/complete_record/1234
```

**Response**:
```json
{
  "book": [{
    "BookId": 1234,
    "Title": "The Hobbit",
    "Author": "Tolkien, J.R.R.",
    "CopyrightDate": "1937-01-01",
    "IsbnNumber": "0345339681",
    "IsbnNumber13": "9780345339683",
    "PublisherName": "Del Rey",
    "CoverType": "Soft",
    "Pages": 300,
    "BookNote": "",
    "Recycled": 0,
    "Location": "Main Collection"
  }],
  "reads": [{
    "DateRead": "2024-01-15",
    "ReadNote": "Re-read for book club"
  }],
  "tags": [["fantasy", "classics"]],
  "img": [["https://example.com/cover.jpg"]]
}
```

## Making POST Requests

POST requests require a JSON body with `Content-Type: application/json` header.

### Add a New Book

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{
    "Title": "Foundation",
    "Author": "Asimov, Isaac",
    "CopyrightDate": "1951",
    "IsbnNumber": "0553293354",
    "IsbnNumber13": "9780553293357",
    "PublisherName": "Spectra",
    "CoverType": "Soft",
    "Pages": 255,
    "Location": "Main Collection",
    "BookNote": "",
    "Recycled": 0
  }]' \
  http://localhost:8084/add_books
```

**Response**:
```json
{
  "add_books": [{
    "BookId": 2912,
    "Title": "Foundation",
    "Author": "Asimov, Isaac",
    "CopyrightDate": "1951-01-01",
    "IsbnNumber": "0553293354",
    "IsbnNumber13": "9780553293357",
    "PublisherName": "Spectra",
    "CoverType": "Soft",
    "Pages": 255,
    "Location": "Main Collection",
    "BookNote": "",
    "Recycled": 0
  }]
}
```

### Record a Reading Date

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{
    "BookId": 2912,
    "ReadDate": "2024-01-20",
    "ReadNote": "Excellent foundation for the series"
  }]' \
  http://localhost:8084/add_read_dates
```

**Response**:
```json
{
  "update_read_dates": [{
    "BookId": 2912,
    "ReadDate": "2024-01-20",
    "ReadNote": "Excellent foundation for the series"
  }],
  "error": []
}
```

## Common Request Patterns

### Query Parameters (GET)

Use query parameters for search filters:

```bash
# Single parameter
/books_search?Author=Tolkien

# Multiple parameters
/books_search?Author=Tolkien&Recycled=0

# Wildcard search (% character)
/books_search?Title=%Lord%
```

### Path Parameters

Use path segments for resource IDs:

```bash
# Get book 1234
/complete_record/1234

# Get 20 recent books
/recent/20

# Navigate to next book
/complete_record/1234/next
```

### Request Body (POST/PUT)

Send JSON in request body:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}' \
  http://localhost:8084/endpoint
```

## Troubleshooting

### 401 Unauthorized

**Problem**: Missing or invalid API key

**Solution**: Verify header is correct:
```bash
curl -v -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

Check that:
- Header name is exactly `x-api-key` (lowercase)
- API key matches the configured value
- No extra spaces or characters

### 400 Bad Request

**Problem**: Invalid request payload or missing required fields

**Example Error**:
```json
{
  "error": "Missing required field: BookId"
}
```

**Solution**:
- Check request body format matches expected schema
- Ensure all required fields are present
- Verify field names match exactly (case-sensitive)

### Empty Data Array

**Problem**: Query returns no results

**Example**:
```json
{
  "data": [],
  "header": ["BookId", "Title", "Author"]
}
```

**Solution**:
- This is not an error - the query was successful but returned no matching records
- Verify your search criteria
- Check if books exist in the database

### Connection Refused

**Problem**: Cannot connect to API server

**Solution**:
- Verify the server is running
- Check the correct port (8084 for local, 9999 for Docker)
- Ensure no firewall blocking the connection

## Next Steps

- Explore [Common Workflows](./common-workflows.md) for real-world usage examples
- Review [Data Models](./data-models.md) to understand the schema
- Check [Error Handling](./error-handling.md) for comprehensive error reference
