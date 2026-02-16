# Book Service API Documentation

**Version**: 0.16.2

## Overview

The Book Service API is a comprehensive REST API for managing personal book collections. It provides functionality for:

- **Book Catalog Management** - Add, update, search, and organize books
- **Reading History Tracking** - Record when books were read with personal notes
- **Tag System** - Flexible categorization with normalized tags
- **Reading Progress Estimation** - Track daily reading progress with completion predictions
- **Image Management** - Store and manage book cover images
- **Statistics & Visualization** - Generate reading statistics and progress charts
- **ISBN Integration** - Automatic book metadata lookup via ISBNdb.com

## Quick Start

### Base URLs

- **Local Development**: `http://localhost:8084`
- **Docker Test**: `http://localhost:9999`

### Authentication

All endpoints (except `/favicon.ico`) require API key authentication:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

### Your First API Call

Test your connection and authentication:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/configuration
```

Expected response:
```json
{
  "version": "0.16.2",
  "configuration": {
    "user": "...",
    "db": "book_collection",
    "host": "...",
    "port": 3306,
    "passwd": "******"
  },
  "isbn_configuration": {
    "url_isbn": "...",
    "key": "******"
  },
  "date": "2024-01-15T10:30"
}
```

## API Capabilities

### 50+ Endpoints Organized in 8 Categories

1. **Configuration & Metadata** (2 endpoints)
   - Get API configuration and version
   - List valid book locations

2. **Query Operations** (9 endpoints)
   - Search books by multiple criteria
   - Get recently updated books
   - Retrieve complete book records
   - Navigate through collection

3. **Reading History** (5 endpoints)
   - View books read by year
   - Get reading statistics
   - Check read status

4. **Tag Management** (8 endpoints)
   - Add tags to books
   - Search by tags
   - Rename tags globally
   - Get tag usage statistics

5. **Mutation Operations** (8 endpoints)
   - Add new books (manual or ISBN lookup)
   - Update book records
   - Add reading dates
   - Update notes and status

6. **Reading Estimates** (6 endpoints)
   - Create reading estimates
   - Track daily page progress
   - View completion predictions

7. **Image Management** (5 endpoints)
   - Add image metadata
   - Upload image files
   - Get images for books

8. **Visualization** (4 endpoints)
   - Year-over-year progress comparison charts
   - All-time reading statistics charts

## Response Format

All query endpoints return a consistent JSON structure:

```json
{
  "data": [
    [value1, value2, value3],
    [value4, value5, value6]
  ],
  "header": ["column1", "column2", "column3"],
  "error": []
}
```

Mutation endpoints return operation-specific objects:

```json
{
  "add_books": [...],
  "error": "error message if any"
}
```

## Documentation Sections

- **[Getting Started](./getting-started.md)** - Setup, authentication, and first requests
- **[Common Workflows](./common-workflows.md)** - Real-world usage examples
- **[Data Models](./data-models.md)** - Database schema and relationships
- **[Error Handling](./error-handling.md)** - Error codes and troubleshooting

## OpenAPI Specification

For complete API reference, see the [OpenAPI 3.1 specification](../openapi.yaml).

The OpenAPI spec can be used to:
- Generate interactive documentation (Swagger UI, ReDoc)
- Generate client SDKs (TypeScript, Python, etc.)
- Validate requests and responses
- Import into API testing tools (Postman, Insomnia)

## Technology Stack

- **Framework**: Flask (Python)
- **Database**: MySQL 8.0+
- **Authentication**: Header-based API key
- **Data Format**: JSON
- **Visualization**: Matplotlib/Pandas (PNG charts)

## Support

For issues, questions, or feature requests, please refer to the main project repository.
