# Error Handling and Troubleshooting

This guide covers HTTP status codes, error response formats, and solutions to common problems.

## HTTP Status Codes

The API uses standard HTTP status codes to indicate success or failure:

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| **200 OK** | Success | Request completed successfully |
| **204 No Content** | Success (no body) | `/favicon.ico` endpoint only |
| **400 Bad Request** | Client error | Invalid request payload or missing required fields |
| **401 Unauthorized** | Authentication failure | Missing or invalid `x-api-key` header |
| **500 Internal Server Error** | Server error | Database errors or unexpected exceptions |

## Error Response Formats

### Standard Error Response

Most endpoints return errors in this format:

```json
{
  "error": "Error description"
}
```

Or as an array:

```json
{
  "error": ["Error message 1", "Error message 2"]
}
```

### Query Endpoint Errors

Query endpoints include errors alongside data:

```json
{
  "data": [...],
  "header": [...],
  "error": ["Error message"]
}
```

### Mutation Endpoint Errors

POST/PUT endpoints return errors in operation-specific format:

```json
{
  "add_books": [],
  "error": "Database error: ..."
}
```

Or per-record errors:

```json
{
  "update_read_dates": [
    { "BookId": 1234, "ReadDate": "2024-01-15", "ReadNote": "..." },
    { "error": "Duplicate entry for key 'PRIMARY'" }
  ],
  "error": []
}
```

## Common Error Scenarios

### 401 Unauthorized

#### Missing API Key Header

**Request**:
```bash
curl http://localhost:8084/configuration
```

**Response**: 401 Unauthorized (empty body or error message)

**Solution**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

#### Incorrect API Key

**Error**: Same as missing header - returns 401

**Solution**:
- Verify API key matches configuration
- Check `configuration.json` or environment variable `API_KEY`
- Ensure no extra spaces or special characters

**Debugging**:
```bash
# Use -v flag to see headers
curl -v -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration

# Check for header in request
> x-api-key: YOUR_API_KEY
```

### 400 Bad Request

#### Missing Required Fields

**Request**:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234
  }' \
  http://localhost:8084/update_book_note_status
```

**Response**: 400 Bad Request
```json
{
  "error": "Missing required fields: BookId, BookNote OR Recycled"
}
```

**Solution**: Include at least one of BookNote or Recycled:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "BookNote": "Updated note"
  }' \
  http://localhost:8084/update_book_note_status
```

#### Invalid JSON Syntax

**Request**:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{invalid json}' \
  http://localhost:8084/add_books
```

**Response**: 400 Bad Request or 500 Internal Server Error

**Solution**: Validate JSON syntax:
```bash
# Use a JSON validator
echo '{"field": "value"}' | python -m json.tool

# Or use jq
echo '{"field": "value"}' | jq .
```

#### Image URL Not Accessible

**Request**:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "name": "cover.jpg",
    "url": "https://example.com/missing.jpg",
    "type": "cover-face"
  }' \
  http://localhost:8084/add_image
```

**Response**: 400 Bad Request
```json
{
  "error": "Image URL not accessible (status 404): https://example.com/missing.jpg"
}
```

**Solution**: Verify URL is accessible and returns an image:
```bash
# Test URL accessibility
curl -I https://example.com/cover.jpg

# Check Content-Type header
HTTP/1.1 200 OK
Content-Type: image/jpeg
```

#### URL Not an Image

**Response**: 400 Bad Request
```json
{
  "error": "URL does not appear to be an image (content-type: text/html)"
}
```

**Solution**: Ensure URL points to an actual image file with image/* content-type

### 500 Internal Server Error

#### Database Connection Failure

**Symptom**: All requests return 500 errors

**Solution**:
- Check database is running
- Verify connection settings in `configuration.json`
- Test database connectivity:
  ```bash
  mysql -h <host> -u <user> -p <database>
  ```

#### Database Constraint Violation

**Example - Duplicate Read Date**:
```json
{
  "error": "Duplicate entry '1234-2024-01-15' for key 'PRIMARY'"
}
```

**Explanation**: Trying to add the same book + date combination twice

**Solution**: Check if record already exists:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/status_read/1234
```

#### Foreign Key Constraint

**Example**:
```json
{
  "error": "Cannot add or update a child row: a foreign key constraint fails"
}
```

**Explanation**: Referenced book doesn't exist

**Solution**: Verify BookId exists:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/complete_record/1234
```

## Non-Error Responses That Look Like Errors

### Empty Data Array

**Response**:
```json
{
  "data": [],
  "header": ["BookId", "Title", "Author"],
  "error": []
}
```

**Explanation**: This is NOT an error - the query was successful but returned no matching records

**When This Occurs**:
- Searching for non-existent author
- Filtering by criteria with no matches
- Book has no tags/images/reads

### "No records found"

**Response**:
```json
{
  "date_page_records": [],
  "RecordId": 75,
  "error": "No records found."
}
```

**Explanation**: Informational message, not a fatal error

**When This Occurs**:
- Reading estimate exists but no daily pages recorded yet
- Valid RecordId with no progress data

## Field-Specific Errors

### Date Format Errors

**Symptom**: Database error about invalid date

**Solution**: Use correct format:
- `CopyrightDate`: `YYYY` or `YYYY-MM-DD`
- `ReadDate`: `YYYY-MM-DD`
- `RecordDate`: `YYYY-MM-DD`

**Valid**:
```json
{
  "CopyrightDate": "1951",
  "ReadDate": "2024-01-15"
}
```

**Invalid**:
```json
{
  "CopyrightDate": "01/15/1951",  // Wrong format
  "ReadDate": "2024-1-15"         // Missing leading zero
}
```

### ISBN Lookup Failure

**Request**:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"isbn_list": ["0000000000"]}' \
  http://localhost:8084/books_by_isbn
```

**Response**: 200 OK (request succeeded)
```json
{
  "book_records": []
}
```

**Explanation**: ISBN lookup found no results (not an error, just empty results)

**Check Server Logs**: Error message logged:
```
[ERROR] No records found for isbn 0000000000.
```

### Invalid Location

**Request**:
```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{
    "Title": "Test Book",
    "Author": "Test Author",
    "Location": "InvalidLocation"
  }]' \
  http://localhost:8084/add_books
```

**Response**: Record may be added, but invalid location is stored

**Best Practice**: Check valid locations first:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/valid_locations
```

### Page Number Constraints

**Maximum Pages**: `smallint` limit is 32,767

**Invalid**:
```json
{
  "Pages": 50000  // Exceeds smallint max
}
```

**Error**: Database error about out-of-range value

## Debugging Strategies

### 1. Verify Authentication

Always test authentication first:

```bash
curl -v -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

Look for:
- `< HTTP/1.1 200 OK` (not 401)
- Response body with version information

### 2. Check JSON Syntax

Validate JSON before sending:

```bash
# Using Python
echo '[{"Title": "Test"}]' | python -m json.tool

# Using jq
echo '[{"Title": "Test"}]' | jq .
```

### 3. Examine Request Headers

Use `-v` flag to see request/response headers:

```bash
curl -v \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  http://localhost:8084/endpoint
```

Verify:
- `> x-api-key: YOUR_API_KEY` in request
- `> Content-Type: application/json` for POST/PUT
- `< HTTP/1.1 200 OK` in response

### 4. Test with Known Good Data

Use example payloads from repository:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @example_json_payloads/test_add_books.json \
  http://localhost:8084/add_books
```

### 5. Check Server Logs

API logs to Flask app logger at DEBUG level. Check logs for:
- Authentication failures
- Database errors
- Query execution details

Example log messages:
```
[INFO] File uploaded successfully: /books/uploads/cover.jpg
[ERROR] x-api-key missing or incorrect.
[ERROR] (1062, "Duplicate entry '1234-2024-01-15' for key 'PRIMARY'")
[DEBUG] Inserting read date for BookId: 1234
```

### 6. Isolate the Problem

Test incrementally:

1. **Authentication**: `/configuration`
2. **Simple GET**: `/recent`
3. **Parameterized GET**: `/recent/5`
4. **Search GET**: `/books_search?Author=Test`
5. **Simple POST**: `/add_books` with minimal fields
6. **Complex POST**: Full book record with all fields

## Error Prevention Checklist

### Before Making Requests

- [ ] API key is configured and correct
- [ ] API service is running and accessible
- [ ] Database is running and accessible
- [ ] JSON payload is syntactically valid
- [ ] All required fields are included
- [ ] Date formats are correct (YYYY-MM-DD)
- [ ] Referenced IDs exist (BookId, RecordId)
- [ ] Locations are from valid_locations list
- [ ] Image URLs are accessible (for add_image)

### For Batch Operations

- [ ] All records in array have required fields
- [ ] No duplicate keys (same book+date for reads)
- [ ] Page numbers are within smallint range
- [ ] ISBNs are valid format

### For Updates

- [ ] Record to update exists
- [ ] At least one field to update is provided
- [ ] BookId is included in request

## Getting Help

### Information to Provide

When reporting issues, include:

1. **API Version**: From `/configuration` endpoint
2. **Request Details**:
   - Full curl command (redact API key)
   - Request headers
   - Request body (if POST/PUT)
3. **Response Details**:
   - HTTP status code
   - Response headers
   - Response body
4. **Server Logs**: Relevant error messages
5. **Expected Behavior**: What should happen
6. **Actual Behavior**: What actually happened

### Example Issue Report

```
API Version: 0.16.2

Request:
curl -X POST \
  -H "x-api-key: [REDACTED]" \
  -H "Content-Type: application/json" \
  -d '[{"Title": "Test", "Author": "Test Author", "Location": "Main Collection"}]' \
  http://localhost:8084/add_books

Response Status: 500 Internal Server Error

Response Body:
{
  "add_books": [],
  "error": "Database error: ..."
}

Server Log:
[ERROR] (1048, "Column 'Title' cannot be null")

Expected: Book should be added with auto-generated BookId
Actual: 500 error with database constraint violation
```

## Testing Tools

### Recommended Tools

1. **curl** - Command-line HTTP client (used in examples)
2. **Postman** - GUI API testing tool
3. **Insomnia** - Alternative GUI client
4. **HTTPie** - User-friendly curl alternative
5. **jq** - JSON processor for response formatting

### Example with HTTPie

```bash
# Simpler syntax than curl
http GET localhost:8084/configuration x-api-key:YOUR_API_KEY

# POST with JSON
http POST localhost:8084/add_books x-api-key:YOUR_API_KEY < test_add_books.json
```

### Example with jq

```bash
# Pretty-print response
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/recent | jq .

# Extract specific field
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration | jq .version

# Filter data array
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/recent | jq '.data[]'
```
