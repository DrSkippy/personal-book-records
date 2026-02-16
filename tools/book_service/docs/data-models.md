# Data Models and Schema

This document describes the database schema, relationships, and business logic for the Book Service API.

## Database Overview

The Book Service API uses MySQL 8.0+ with 7 primary tables:

1. **books** - Core book metadata
2. **books_read** - Reading history
3. **tag_labels** - Tag definitions
4. **books_tags** - Book-tag relationships (many-to-many)
5. **images** - Book cover images
6. **complete_date_estimates** - Reading progress tracking
7. **daily_page_records** - Daily reading progress data

## Entity Relationship Diagram

```mermaid
erDiagram
    BOOKS ||--o{ BOOKS-READ : "has"
    BOOKS ||--o{ BOOKS-TAGS : "has"
    BOOKS ||--o{ IMAGES : "has"
    BOOKS ||--o{ COMPLETE-DATE-ESTIMATES : "tracks"
    TAG-LABELS ||--o{ BOOKS-TAGS : "categorizes"
    COMPLETE-DATE-ESTIMATES ||--o{ DAILY-PAGE-RECORDS : "contains"

    BOOKS {
        int BookId PK
        varchar Title
        varchar Author
        datetime CopyrightDate
        varchar IsbnNumber
        varchar IsbnNumber13
        varchar PublisherName
        varchar CoverType
        smallint Pages
        mediumtext BookNote
        tinyint Recycled
        varchar Location
        timestamp LastUpdate
    }

    BOOKS-READ {
        int BookId FK
        date ReadDate PK
        text ReadNote
        timestamp LastUpdate
    }

    TAG-LABELS {
        int TagId PK
        varchar Label UNIQUE
    }

    BOOKS-TAGS {
        int BookId PK
        int TagId PK-FK
        timestamp LastUpdate
    }

    IMAGES {
        int ImageId PK
        int BookId FK
        varchar Name
        varchar Url
        varchar ImageType
    }

    COMPLETE-DATE-ESTIMATES {
        bigint RecordId PK
        bigint BookId FK
        datetime StartDate
        bigint LastReadablePage
        datetime EstimateDate
        datetime EstimatedFinishDate
    }

    DAILY-PAGE-RECORDS {
        bigint RecordId FK
        datetime RecordDate PK
        bigint Page
        timestamp LastUpdate
    }
```

## Table Definitions

### books

The central table storing book metadata.

**Schema**:
```sql
CREATE TABLE books (
  BookId int NOT NULL AUTO_INCREMENT,
  Title varchar(200) NOT NULL,
  Author varchar(200) NOT NULL,
  CopyrightDate datetime DEFAULT NULL,
  IsbnNumber varchar(13) DEFAULT NULL,
  PublisherName varchar(50) DEFAULT NULL,
  CoverType varchar(30) DEFAULT NULL,
  Pages smallint DEFAULT NULL,
  BookNote mediumtext,
  Recycled tinyint(1) DEFAULT NULL,
  Location varchar(50) NOT NULL,
  IsbnNumber13 varchar(13) DEFAULT NULL,
  LastUpdate timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (BookId),
  KEY Location_idx (Location),
  FULLTEXT KEY Author_idx (Author),
  FULLTEXT KEY Title_idx (Title)
) ENGINE=InnoDB AUTO_INCREMENT=2912 DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- `BookId`: Auto-incrementing primary key
- `Title`, `Author`: Required fields with fulltext indexes for searching
- `CopyrightDate`: Accepts year-only (`YYYY`) which is converted to `YYYY-01-01 00:00:00`
- `IsbnNumber`: ISBN-10 format
- `IsbnNumber13`: ISBN-13 format
- `CoverType`: Physical format (Hard, Soft, Digital)
- `Recycled`: Soft delete flag (0=active, 1=removed/donated)
- `Location`: Required field, must match a valid location
- `LastUpdate`: Automatically updated timestamp

**Business Logic**:
- Year-only copyright dates are automatically expanded to full datetime
- Title and Author have fulltext indexes for efficient searching
- Recycled flag enables soft deletes (preserves history while marking book as removed)

### books_read

Tracks reading history with dates and notes.

**Schema**:
```sql
CREATE TABLE books_read (
  BookId int unsigned NOT NULL,
  ReadDate date NOT NULL,
  ReadNote text CHARACTER SET utf8mb4,
  LastUpdate timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (BookId, ReadDate),
  CONSTRAINT fk_books_read_book FOREIGN KEY (BookId) REFERENCES books (BookId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- Composite primary key: (`BookId`, `ReadDate`)
  - Allows tracking multiple readings of the same book
  - Each reading date must be unique per book
- `ReadNote`: Optional text field for reading-specific notes

**Business Logic**:
- A book can be read multiple times (multiple ReadDate entries)
- Each reading can have its own note
- The same book with the same date cannot be inserted twice

### tag_labels

Stores unique tag definitions.

**Schema**:
```sql
CREATE TABLE tag_labels (
  TagId int NOT NULL AUTO_INCREMENT,
  Label varchar(50) DEFAULT NULL,
  PRIMARY KEY (TagId),
  UNIQUE KEY tag_labels_UN (Label)
) ENGINE=InnoDB AUTO_INCREMENT=6911 DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- `TagId`: Auto-incrementing primary key
- `Label`: Unique tag text (enforced by unique constraint)

**Business Logic**:
- Labels are automatically converted to lowercase and trimmed
- Duplicate labels are prevented by unique constraint
- Normalization ensures consistency (e.g., "Science Fiction" → "science fiction")

### books_tags

Many-to-many relationship between books and tags.

**Schema**:
```sql
CREATE TABLE books_tags (
  BookId int NOT NULL,
  TagId int NOT NULL,
  LastUpdate timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (BookId, TagId),
  CONSTRAINT fk_books_tags_book FOREIGN KEY (BookId) REFERENCES books (BookId) ON DELETE CASCADE,
  CONSTRAINT fk_books_tags_tag FOREIGN KEY (TagId) REFERENCES tag_labels (TagId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- Composite primary key: (`BookId`, `TagId`)
- `BookId`: References books table (INT)
- `TagId`: References tag_labels table

**Business Logic**:
- A book can have multiple tags
- A tag can be applied to multiple books
- The same tag cannot be applied to the same book twice (enforced by PK)

### images

Stores image metadata for book covers.

**Schema**:
```sql
CREATE TABLE images (
  ImageId int NOT NULL AUTO_INCREMENT,
  BookId int NOT NULL,
  Name varchar(255) DEFAULT NULL,
  Url varchar(255) DEFAULT NULL,
  ImageType varchar(64) DEFAULT 'cover-face',
  PRIMARY KEY (ImageId),
  CONSTRAINT fk_images_book FOREIGN KEY (BookId) REFERENCES books (BookId) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- `ImageId`: Auto-incrementing primary key
- `BookId`: Foreign key to books table
- `Name`: Image filename
- `Url`: Image URL (can be HTTP/HTTPS or local path)
- `ImageType`: Image classification (defaults to "cover-face")

**Business Logic**:
- A book can have multiple images
- For HTTP/HTTPS URLs, API validates:
  - URL is accessible (returns 200 status)
  - Content-Type header indicates an image (starts with "image/")
- Local file paths are not validated
- Uploaded files are stored in `/app/uploads/` with secure filenames

### complete_date_estimates

Tracks reading session metadata for progress estimation.

**Schema**:
```sql
CREATE TABLE complete_date_estimates (
  BookId bigint unsigned NOT NULL,
  StartDate datetime NOT NULL,
  LastReadablePage bigint NOT NULL,
  EstimateDate datetime DEFAULT NULL,
  EstimatedFinishDate datetime DEFAULT NULL,
  RecordId bigint unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (RecordId),
  CONSTRAINT fk_estimates_book FOREIGN KEY (BookId) REFERENCES books (BookId) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- `RecordId`: Auto-incrementing primary key used to track daily progress
- `BookId`: Foreign key to books table
- `StartDate`: When reading estimate began
- `LastReadablePage`: Total readable pages in book
- `EstimateDate`: When estimate was calculated
- `EstimatedFinishDate`: Predicted completion date (based on reading pace)

**Business Logic**:
- Multiple reading sessions can exist for the same book (e.g., re-reads)
- RecordId is used to associate daily page records
- Completion estimates use linear regression on daily page progress

### daily_page_records

Tracks day-by-day reading progress.

**Schema**:
```sql
CREATE TABLE daily_page_records (
  RecordDate datetime NOT NULL,
  Page bigint NOT NULL,
  RecordId bigint unsigned NOT NULL,
  LastUpdate timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (RecordId, RecordDate),
  CONSTRAINT fk_daily_pages_record FOREIGN KEY (RecordId) REFERENCES complete_date_estimates (RecordId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Fields**:
- Composite primary key: (`RecordId`, `RecordDate`)
- `RecordId`: Foreign key to complete_date_estimates
- `RecordDate`: Date of reading progress
- `Page`: Page number reached on this date

**Business Logic**:
- Each date can have only one page record per estimate session
- Used for calculating reading pace and estimated completion
- Page numbers should be cumulative (total pages read, not daily increment)

## Relationships

### One-to-Many Relationships

1. **books → books_read**
   - One book can have multiple reading dates
   - Enables tracking re-reads

2. **books → images**
   - One book can have multiple images (cover, spine, etc.)

3. **books → complete_date_estimates**
   - One book can have multiple reading sessions
   - Useful for long books read over multiple attempts

4. **complete_date_estimates → daily_page_records**
   - One reading session has multiple daily progress entries

### Many-to-Many Relationships

1. **books ↔ tag_labels** (via books_tags)
   - Books can have multiple tags
   - Tags can apply to multiple books
   - Junction table: `books_tags`
   - Foreign key constraints with CASCADE ensure referential integrity

## Data Constraints and Validation

### Required Fields

**books**:
- Title (max 200 chars)
- Author (max 200 chars)
- Location (max 50 chars, must be valid)

**books_read**:
- BookId (must exist in books)
- ReadDate (date format YYYY-MM-DD)

**images**:
- BookId (must exist in books)

### Field Constraints

**CoverType** (recommended values):
- "Hard"
- "Soft"
- "Digital"

**Recycled**:
- 0 = Active in collection
- 1 = Removed/donated

**Pages**:
- smallint (max 32,767)
- Should be positive integer

**IsbnNumber**:
- varchar(13) for ISBN-10 format
- Typically 10 digits

**IsbnNumber13**:
- varchar(13) for ISBN-13 format
- Typically 13 digits

**Tag Label**:
- max 50 chars
- Automatically lowercase and trimmed
- Must be unique

## API Response Patterns

### Standard Query Response

Most GET endpoints return this format:

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

- `data`: Array of arrays (rows)
- `header`: Column names matching data array positions
- `error`: Array of error messages (empty if successful)

### Complete Record Response

The `/complete_record/{book_id}` endpoint returns a structured object:

```json
{
  "book": [{ BookRecord }],
  "reads": [{ DateRead, ReadNote }],
  "tags": [["tag1", "tag2"]],
  "img": [["url1", "url2"]]
}
```

### Mutation Response

POST/PUT endpoints return operation-specific objects:

```json
{
  "add_books": [{ inserted records with BookId }],
  "error": "error message if any"
}
```

## Indexes

### Primary Keys
- All tables have primary keys for fast lookups
- Auto-incrementing PKs for books, images, tag_labels, complete_date_estimates

### Secondary Indexes
- `Location_idx` on books.Location (frequent filter)
- Fulltext indexes on Author and Title (text search optimization)

### Composite Primary Keys
- books_read: (BookId, ReadDate)
- books_tags: (BookId, TagId)
- daily_page_records: (RecordId, RecordDate)

These composite keys ensure uniqueness while enabling efficient queries.

## Auto-Updated Fields

Several fields automatically update via database triggers:

- `books.LastUpdate` - Updates on any row modification
- `books_read.LastUpdate` - Updates on any row modification
- `books_tags.LastUpdate` - Updates on any row modification
- `daily_page_records.LastUpdate` - Updates on any row modification

These timestamps help track data freshness and enable caching strategies.

## Database Size Considerations

Based on the auto-increment values:
- books: ~2,900+ books
- tag_labels: ~6,900+ unique tags
- complete_date_estimates: ~75+ reading sessions
- images: ~10+ image records

The schema is designed to scale to tens of thousands of books and millions of reading records.
