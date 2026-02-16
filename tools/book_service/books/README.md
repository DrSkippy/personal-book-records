# REST API Service

Flask-based REST API for managing and querying the book collection database.

## Overview

- **Version**: 0.16.2
- **Framework**: Flask 3.1.2
- **Port**: 8084
- **Authentication**: API key via `x-api-key` header
- **Endpoints**: 50+ endpoints for books, reading history, tags, and visualizations

## Quick Start

```bash
# Run locally (from tools directory)
make run-local-book-service

# Or with Docker
make build-book-service
cd book_service/books
docker-compose up -d

# Test
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
```

## Key Features

- **Book Management**: Add, update, search books
- **Reading History**: Track books read, dates, notes
- **Tagging System**: Flexible categorization
- **Image Management**: Upload and manage book covers
- **Visualizations**: Generate reading progress charts
- **ISBN Integration**: Look up books by ISBN
- **Reading Estimates**: Track reading progress

## Use Cases Supported

1. View API configuration and version
2. List valid book locations
3. Add new book records
4. Update read dates for books
5. Report on books/pages read by year
6. List books read in a specific year
7. Search books by read/recycled status (Alpha by Author)
8. Update notes on books
9. Update recycled status
10. Add tags to book records
11. Search for books by tag
12. Generate reading progress visualizations

## Comprehensive Documentation

For complete API documentation including:
- **All 50+ endpoint details** with examples
- **Complete Makefile reference** (build, test, deploy)
- **Testing procedures**
- **Deployment workflows**
- **Troubleshooting**

**See**: `../../README.md` (tools/README.md) - Main documentation with complete API endpoint reference

## Configuration

The API uses `../config/configuration.json`:

```json
{
  "username": "mysql_user",
  "password": "mysql_password",
  "database": "book_collection",
  "host": "localhost",
  "port": 3306,
  "endpoint": "http://localhost:8084",
  "api_key": "your_api_key_here"
}
```

For Docker deployments, use `host.docker.internal` as the host to access MySQL on the host machine.

## Testing

```bash
# From tools directory

# Run all tests
make test-book-service

# Run with coverage
make test-coverage
```

See `../../README.md#testing` for detailed testing documentation.

## Deployment

### Local Testing

```bash
# Build test image
docker build -f ./books/Dockerfile . -t book-test

# Run on port 9999
docker run -p 127.0.0.1:9999:8084 book-test

# Test
curl -H "x-api-key: YOUR_KEY" http://localhost:9999/valid_locations
```

### Production (Docker Compose)

```bash
# From tools directory
make build-book-service
make push-book-service  # If using registry

# Deploy
cd book_service/books
export API_KEY=your_key_here
docker-compose up -d

# Verify
curl -H "x-api-key: $API_KEY" http://localhost:8084/configuration
```

See `../../README.md#deployment` for comprehensive deployment documentation including:
- Registry setup
- Multiple deployment methods
- Update workflows
- Health checks
- Troubleshooting

## Docker Configuration

### Dockerfile
- Base: `python:3.11-slim`
- Working directory: `/app`
- Port: 8084
- Entrypoint: `poetry run uwsgi --ini books/api.ini`

### docker-compose.yml
```yaml
services:
  book-service:
    image: localhost:5000/book-service:latest
    container_name: book-service
    ports:
      - "8084:8084"
    environment:
      - API_KEY=${API_KEY}
    volumes:
      - /var/www/html/resources/books:/app/uploads
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

## API Endpoints Quick Reference

For the complete endpoint reference with examples, see `../../README.md#tool-2-rest-api-service`

### Configuration
- GET `/configuration` - API version and settings
- GET `/valid_locations` - Valid book locations
- GET `/health` - Health check

### Books
- GET/POST `/books_search` - Search books
- GET `/recent` - Recently updated books
- GET `/complete_record/<book_id>` - Complete book details
- POST `/add_books` - Add new books
- POST `/update_book_record` - Update book fields
- DELETE `/delete_book/<book_id>` - Delete a book
- POST `/complete_record_window` - Get records by BookId list

### Reading History
- GET `/books_read/<year>` - Books read in year
- GET `/summary_books_read_by_year` - Reading statistics
- GET `/status_read/<book_id>` - Read status
- POST `/add_read_dates` - Add read dates

### Tags
- GET `/tags/<book_id>` - Tags for book
- GET `/tags_search/<match_str>` - Search by tag
- PUT `/add_tag/<book_id>/<tag>` - Add tag

### Visualizations
- GET `/image/year_progress_comparison.png` - Progress by year chart
- GET `/image/all_years.png` - All-time statistics

**Full endpoint reference**: See `../../README.md#complete-api-endpoint-reference`

## Related Documentation

- **Main README**: `../../README.md` - Comprehensive documentation
- **book_service Overview**: `../README.md` - Service directory overview
- **MCP Server**: `../booksmcp/README.md` - MCP API documentation
- **Test Suite**: `../../test/README.md` - Unit test documentation

## Version Information

- API Version: 0.16.2
- Flask: 3.1.2
- Python: 3.11+
- PyMySQL: 1.1.0+

---

For complete API documentation with all endpoints, examples, and workflows, see:
**`/var/www/html/personal-book-records/tools/README.md`**
