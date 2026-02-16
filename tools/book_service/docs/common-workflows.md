# Common Workflows

This guide demonstrates real-world usage patterns for typical book management tasks.

## Table of Contents

1. [Browse Book Collection](#1-browse-book-collection)
2. [Add New Books](#2-add-new-books)
3. [Track Reading Progress](#3-track-reading-progress)
4. [Manage Tags](#4-manage-tags)
5. [Work with Images](#5-work-with-images)
6. [Reading Progress Estimation](#6-reading-progress-estimation)
7. [Generate Visualizations](#7-generate-visualizations)

## 1. Browse Book Collection

### Search by Single Criterion

**By Author**:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8084/books_search?Author=Tolkien"
```

**By Title** (with wildcards):
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8084/books_search?Title=%Foundation%"
```

**By ISBN**:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8084/books_search?IsbnNumber13=9780345339683"
```

### Search by Multiple Criteria

Find books by Asimov that are still in collection:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8084/books_search?Author=Asimov&Recycled=0"
```

### Get Recently Updated Books

Last 10 updates (default):
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/recent
```

Last 25 updates:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/recent/25
```

### Navigate Through Books

Get complete record for book 1234:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/complete_record/1234
```

Navigate to next book:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/complete_record/1234/next
```

Navigate to previous book:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/complete_record/1234/prev
```

Get a window of 20 books around book 1234:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/complete_records_window/1234/20
```

## 2. Add New Books

### Manual Entry

Add a single book (note: request body is an array):

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{
    "Title": "1984",
    "Author": "Orwell, George",
    "CopyrightDate": "1949",
    "IsbnNumber": "0451524934",
    "IsbnNumber13": "9780451524935",
    "PublisherName": "Signet Classic",
    "CoverType": "Soft",
    "Pages": 328,
    "Location": "Main Collection",
    "BookNote": "Dystopian classic",
    "Recycled": 0
  }]' \
  http://localhost:8084/add_books
```

Add multiple books in batch:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "Title": "Brave New World",
      "Author": "Huxley, Aldous",
      "CopyrightDate": "1932",
      "IsbnNumber": "0060850523",
      "PublisherName": "Harper Perennial",
      "CoverType": "Soft",
      "Pages": 268,
      "Location": "Main Collection",
      "Recycled": 0
    },
    {
      "Title": "Fahrenheit 451",
      "Author": "Bradbury, Ray",
      "CopyrightDate": "1953",
      "IsbnNumber": "1451673310",
      "PublisherName": "Simon & Schuster",
      "CoverType": "Soft",
      "Pages": 249,
      "Location": "Main Collection",
      "Recycled": 0
    }
  ]' \
  http://localhost:8084/add_books
```

### ISBN Lookup and Import

Look up and add books automatically by ISBN:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"isbn_list": ["0060929480", "9780345339683"]}' \
  http://localhost:8084/books_by_isbn
```

This automatically populates Title, Author, Publisher, and other metadata from the ISBN database.

### Update Book Information

Update any fields of an existing book:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "BookNote": "Signed by author at convention",
    "Pages": 310
  }' \
  http://localhost:8084/update_book_record
```

### Mark Book as Recycled/Donated

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "BookNote": "Donated to local library",
    "Recycled": 1
  }' \
  http://localhost:8084/update_book_note_status
```

## 3. Track Reading Progress

### Record Reading Dates

Add single reading date:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[{
    "BookId": 1234,
    "ReadDate": "2024-01-15",
    "ReadNote": "Re-read for book club discussion"
  }]' \
  http://localhost:8084/add_read_dates
```

Add multiple reading dates (batch):

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "BookId": 1234,
      "ReadDate": "2024-01-15",
      "ReadNote": "First reading"
    },
    {
      "BookId": 1235,
      "ReadDate": "2024-01-20",
      "ReadNote": "Sequel - excellent continuation"
    }
  ]' \
  http://localhost:8084/add_read_dates
```

### Update Reading Note

Modify the note for a specific reading:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "ReadDate": "2024-01-15",
    "ReadNote": "Updated note: discussed themes of power and corruption"
  }' \
  http://localhost:8084/update_edit_read_note
```

### View Reading History

**All books read**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/books_read
```

**Books read in 2024**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/books_read/2024
```

**Check if specific book has been read**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/status_read/1234
```

### View Reading Statistics

**Summary for all years**:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/summary_books_read_by_year
```

Expected response:
```json
{
  "data": [
    [2024, 45, 12500],
    [2023, 52, 15000],
    [2022, 48, 13200]
  ],
  "header": ["year", "books read", "pages read"]
}
```

**Summary for specific year (2024)**:
```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/summary_books_read_by_year/2024
```

## 4. Manage Tags

### Add Tags to Books

Add single tag:

```bash
curl -X PUT \
  -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/add_tag/1234/science-fiction
```

Note: Tags are automatically converted to lowercase and trimmed.

### Search Books by Tag

Find all science-fiction books:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/tags_search/science-fiction
```

### View Tags for a Book

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/tags/1234
```

Response:
```json
{
  "tags": ["science-fiction", "classics", "award-winner"]
}
```

### Get Tag Usage Statistics

**All tags with counts**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/tag_counts
```

**Tags starting with "sci"**:
```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/tag_counts/sci
```

### Rename Tag Globally

Rename "sci-fi" to "science-fiction" across all books:

```bash
curl -X PUT \
  -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/update_tag_value/sci-fi/science-fiction
```

Response:
```json
{
  "data": {
    "tag_update": "sci-fi >> science-fiction",
    "updated_tags": 45
  }
}
```

### Normalize All Tags

Clean up all tags (lowercase, trim whitespace):

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/tag_maintenance
```

## 5. Work with Images

### Add Image Metadata

Add image URL for a book:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "BookId": 1234,
    "Name": "hobbit_cover.jpg",
    "Url": "https://example.com/images/hobbit_cover.jpg",
    "ImageType": "cover-face"
  }' \
  http://localhost:8084/add_image
```

Note: For HTTP/HTTPS URLs, the API validates that the URL is accessible and returns an image content-type.

### Upload Image File

Upload local image file:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -F "file=@/path/to/cover.jpg" \
  -F "filename=book_1234_cover.jpg" \
  http://localhost:8084/upload_image
```

Response:
```json
{
  "upload_image": {
    "status": "success",
    "filename": "book_1234_cover.jpg",
    "path": "/app/uploads/book_1234_cover.jpg"
  }
}
```

### Retrieve Images for a Book

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/images/1234
```

Response:
```json
{
  "BookId": 1234,
  "images": [
    {
      "ImageId": 1,
      "BookId": 1234,
      "Name": "hobbit_cover.jpg",
      "Url": "https://example.com/images/hobbit_cover.jpg",
      "ImageType": "cover-face"
    }
  ],
  "count": 1
}
```

## 6. Reading Progress Estimation

### Create Reading Estimate

Start tracking reading progress for book 1234 with 300 pages (starts today):

```bash
curl -X PUT \
  -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/add_book_estimate/1234/300
```

Or specify a custom start date:

```bash
curl -X PUT \
  -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/add_book_estimate/1234/300/2024-01-15
```

Response includes RecordId for tracking:
```json
{
  "add_book_estimate": {
    "BookId": "1234",
    "LastReadablePage": "300",
    "StartDate": "2024-01-15"
  }
}
```

### Record Daily Reading Progress

Add page progress for a specific date (RecordId from previous step):

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "RecordId": 75,
    "RecordDate": "2024-01-15",
    "Page": 50
  }' \
  http://localhost:8084/add_date_page
```

Continue tracking progress over time:

```bash
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "RecordId": 75,
    "RecordDate": "2024-01-16",
    "Page": 95
  }' \
  http://localhost:8084/add_date_page
```

### View Reading Progress

Get all estimate records for a book:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/record_set/1234
```

Get daily page records for an estimate:

```bash
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8084/date_page_records/75
```

Response:
```json
{
  "date_page_records": [
    ["2024-01-15", 50, 1],
    ["2024-01-16", 95, 2],
    ["2024-01-17", 140, 3]
  ],
  "RecordId": 75
}
```

Each entry is: `[date, page_number, day_count]`

## 7. Generate Visualizations

All visualization endpoints return PNG images.

### Year-over-Year Progress Comparison

Compare last 15 years (default):

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/image/year_progress_comparison.png \
  > year_comparison.png
```

Compare last 10 years:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/image/year_progress_comparison.png/10 \
  > year_comparison_10.png
```

This generates a line chart showing cumulative pages read by day of year, with the current year highlighted.

### All-Time Reading Statistics

Generate all-time statistics chart (highlights current year):

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/image/all_years.png \
  > all_years.png
```

Generate with specific year highlighted (e.g., 2023):

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8084/image/all_years.png/2023 \
  > all_years_2023.png
```

This generates a 3-panel chart:
1. Histogram of pages read distribution
2. Ranking of years by pages read
3. Bar chart of pages read by year

## Tips and Best Practices

### Batch Operations

When adding multiple records, use batch operations for better performance:

```bash
# Good: Single request with array
curl -X POST -d '[{...}, {...}, {...}]' /add_books

# Less efficient: Multiple requests
curl -X POST -d '[{...}]' /add_books
curl -X POST -d '[{...}]' /add_books
curl -X POST -d '[{...}]' /add_books
```

### Date Formats

- **CopyrightDate**: Accepts `YYYY` or `YYYY-MM-DD`
  - Year-only is automatically converted to `YYYY-01-01`
- **ReadDate**: Must be `YYYY-MM-DD`
- **RecordDate**: Must be `YYYY-MM-DD`

### Tag Naming

Tags are automatically normalized:
- Converted to lowercase
- Whitespace trimmed
- "Science Fiction" becomes "science fiction"
- Use consistent naming (e.g., "science-fiction" vs "sci-fi")

### Recycled Flag

Use the Recycled flag for soft deletes:
- `0` = Book is active in collection
- `1` = Book has been removed/donated (but record preserved)

This preserves reading history while marking books no longer in your possession.

### Search Wildcards

Use `%` wildcard in search queries:
- `Title=%Lord%` - matches "The Lord of the Rings", "Lord Jim", etc.
- `Author=King,%` - matches all authors with last name King
- `Title=Foundation%` - matches titles starting with "Foundation"
