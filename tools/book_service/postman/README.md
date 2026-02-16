# Postman Collection for Book Service API

This directory contains a comprehensive Postman collection and environment files for testing the Book Service API.

## Files

- **book-service-api.postman_collection.json** - Main Postman collection with 40+ requests
- **Local-Development.postman_environment.json** - Environment for local development (port 8084)
- **Docker-Test.postman_environment.json** - Environment for Docker test instance (port 9999)
- **Production.postman_environment.json** - Template for production environment

## Quick Start

### 1. Import Collection

1. Open Postman
2. Click **Import** button
3. Select `book-service-api.postman_collection.json`
4. Collection will appear in left sidebar

### 2. Import Environment

1. Click **Import** button
2. Select environment file (e.g., `Local-Development.postman_environment.json`)
3. Select environment from dropdown in top-right corner

### 3. Configure API Key

1. Click environment name in top-right
2. Edit `api_key` variable
3. Enter your actual API key
4. Save changes

### 4. Run Requests

1. Select environment (e.g., "Local Development")
2. Navigate to any request in collection
3. Click **Send**

## Collection Structure

The collection is organized into 8 folders matching the API categories:

### 1. Configuration & Metadata (2 requests)
- Get API Configuration
- Get Valid Locations

### 2. Query Operations (7 requests)
- Get Recent Books (various limits)
- Search Books (single and multi-criteria)
- Get Complete Book Record
- Navigate to Next/Previous Book
- Get Books Window

### 3. Reading History (5 requests)
- Get All Books Read
- Get Books Read in Year
- Get Reading Summaries
- Get Read Status

### 4. Tag Management (7 requests)
- Get/Search Tags
- Add Tag to Book
- Rename Tag Globally
- Get Tag Counts
- Tag Maintenance

### 5. Mutation Operations (6 requests)
- Add Books (manual and ISBN)
- Add Read Dates
- Update Book Record
- Update Book Note/Status
- Update Read Note

### 6. Reading Estimates (5 requests)
- Get Record Set
- Get Daily Page Records
- Add Book Estimate
- Add Daily Page Progress

### 7. Image Management (3 requests)
- Get Images for Book
- Add Image Metadata
- Upload Image File

### 8. Visualization (4 requests)
- Year Progress Comparison Charts
- All Years Statistics Charts

## Environment Variables

Each environment includes these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | API base URL | `http://localhost:8084` |
| `api_key` | API authentication key | Your API key |

## Authentication

All requests use API key authentication configured at the collection level:

- **Header**: `x-api-key`
- **Value**: `{{api_key}}` (from environment variable)

The authentication is inherited by all requests automatically.

## Request Examples

### Get Configuration
```
GET {{base_url}}/configuration
```

### Search Books by Author
```
GET {{base_url}}/books_search?Author=Tolkien
```

### Add a Book
```
POST {{base_url}}/add_books
Content-Type: application/json

[{
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
}]
```

## Collection-Level Tests

The collection includes automatic tests that run for all requests:

### Status Code Check
```javascript
pm.test('Status code is 200', function() {
    pm.response.to.have.status(200);
});
```

### Response Time Check
```javascript
pm.test('Response time is less than 2000ms', function() {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});
```

## Customization

### Add Request-Specific Tests

Edit any request and add tests in the **Tests** tab:

```javascript
// Parse JSON response
const response = pm.response.json();

// Check specific field
pm.test('Response has version field', function() {
    pm.expect(response).to.have.property('version');
});

// Validate data structure
pm.test('Data is an array', function() {
    pm.expect(response.data).to.be.an('array');
});
```

### Add Pre-Request Scripts

Set up data before requests in the **Pre-request Script** tab:

```javascript
// Generate current date
const currentDate = new Date().toISOString().split('T')[0];
pm.environment.set('current_date', currentDate);

// Generate random book ID
const randomId = Math.floor(Math.random() * 1000) + 1;
pm.environment.set('random_book_id', randomId);
```

## Workflow Examples

### Complete Book Addition Workflow

1. **Get Valid Locations** - See available locations
2. **Add Books** - Add new book to collection
3. **Get Recent Books** - Verify book was added
4. **Add Tag to Book** - Categorize the book
5. **Add Read Dates** - Mark book as read

### Reading Progress Workflow

1. **Add Book Estimate** - Start tracking reading progress
2. **Add Daily Page Progress** - Record daily page count (repeat)
3. **Get Daily Page Records** - View progress over time
4. **Get Record Set** - See completion estimate

## Troubleshooting

### 401 Unauthorized

**Problem**: API key not configured or incorrect

**Solution**:
1. Check environment is selected (top-right dropdown)
2. Edit environment and set `api_key` variable
3. Verify API key matches server configuration

### Connection Refused

**Problem**: Server not running or wrong port

**Solution**:
1. Verify server is running
2. Check `base_url` in environment
3. Test with browser: `http://localhost:8084/configuration`

### Request Timeout

**Problem**: Request takes too long

**Solution**:
1. Check database is running and accessible
2. Increase timeout in Postman settings
3. Check server logs for errors

## Advanced Features

### Run Collection with Newman (CLI)

Install Newman:
```bash
npm install -g newman
```

Run collection:
```bash
newman run book-service-api.postman_collection.json \
  -e Local-Development.postman_environment.json
```

### Export Test Results

```bash
newman run book-service-api.postman_collection.json \
  -e Local-Development.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

## Tips

1. **Use Variables**: Store frequently used values (BookId, dates) in environment variables
2. **Chain Requests**: Use test scripts to extract IDs from responses and use in subsequent requests
3. **Save Responses**: Use Postman's example feature to save sample responses
4. **Folder-Level Tests**: Add tests at folder level to run for all requests in that category
5. **Mock Servers**: Create mock server from collection for frontend development

## Additional Resources

- [Main Documentation](../docs/README.md) - Complete API documentation
- [OpenAPI Specification](../openapi.yaml) - Machine-readable API spec
- [Getting Started Guide](../docs/getting-started.md) - Detailed setup instructions
- [Common Workflows](../docs/common-workflows.md) - Real-world usage examples
