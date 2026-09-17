# Data Models and Schema

This document describes the database schema, relationships, and business logic for the Book Service API.

## Database Overview

The Book Service API uses PostgreSQL 14+ (migrated from MySQL in May 2026; see
`tools/database/migrate_mysql_to_postgres.py`) with pgvector enabled, across 9 tables:

1. **books** - Core book metadata
2. **books_read** - Reading history
3. **tag_labels** - Tag definitions
4. **books_tags** - Book-tag relationships (many-to-many)
5. **images** - Book cover images
6. **complete_date_estimates** - Reading progress tracking
7. **daily_page_records** - Daily reading progress data
8. **book_note_embeddings** - pgvector embeddings of `BookNote`/`ReadNote`, for `/rag_search` and the `semantic_search_notes` chat tool
9. **embedding_index_state** - Single-row marker recording which `embed_host`/`embed_model`/`embed_dimensions` produced the vectors currently in `book_note_embeddings`

The canonical, always-current schema lives in `tools/database/schema_current.sql` and is applied via
`poetry run python database/setup_db.py` (idempotent — safe to re-run against an existing database).

## Entity Relationship Diagram

```mermaid
erDiagram
    BOOKS ||--o{ BOOKS-READ : "has"
    BOOKS ||--o{ BOOKS-TAGS : "has"
    BOOKS ||--o{ IMAGES : "has"
    BOOKS ||--o{ COMPLETE-DATE-ESTIMATES : "tracks"
    BOOKS ||--o{ BOOK-NOTE-EMBEDDINGS : "embeds"
    TAG-LABELS ||--o{ BOOKS-TAGS : "categorizes"
    COMPLETE-DATE-ESTIMATES ||--o{ DAILY-PAGE-RECORDS : "contains"

    BOOKS {
        int BookId PK
        varchar Title
        varchar Author
        timestamp CopyrightDate
        varchar IsbnNumber
        varchar IsbnNumber13
        varchar PublisherName
        varchar CoverType
        smallint Pages
        text BookNote
        smallint Recycled
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
        timestamp LastUpdate
    }

    COMPLETE-DATE-ESTIMATES {
        bigint RecordId PK
        int BookId FK
        timestamp StartDate
        bigint LastReadablePage
        timestamp EstimateDate
        timestamp EstimatedFinishDate
    }

    DAILY-PAGE-RECORDS {
        bigint RecordId FK
        timestamp RecordDate PK
        bigint Page
        timestamp LastUpdate
    }

    BOOK-NOTE-EMBEDDINGS {
        int id PK
        int bookid FK
        varchar source
        date read_date
        text content
        vector embedding
        timestamp updated_at
    }
```

## Table Definitions

### books

The central table storing book metadata.

**Schema**:
```sql
CREATE TABLE books (
    BookId        SERIAL         NOT NULL,
    Title         VARCHAR(200)   NOT NULL,
    Author        VARCHAR(200)   NOT NULL,
    CopyrightDate TIMESTAMP      DEFAULT NULL,
    IsbnNumber    VARCHAR(13)    DEFAULT NULL,
    PublisherName VARCHAR(50)    DEFAULT NULL,
    CoverType     VARCHAR(30)    DEFAULT NULL,
    Pages         SMALLINT       DEFAULT NULL,
    BookNote      TEXT           DEFAULT NULL,
    Recycled      SMALLINT       DEFAULT NULL,
    Location      VARCHAR(50)    NOT NULL,
    IsbnNumber13  VARCHAR(13)    DEFAULT NULL,
    LastUpdate    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (BookId)
);

CREATE INDEX idx_books_title    ON books (Title);
CREATE INDEX idx_books_author   ON books (Author);
CREATE INDEX idx_books_location ON books (Location);
```

`LastUpdate` is maintained by a `BEFORE UPDATE` trigger (`update_last_update()`), not a MySQL-style
`ON UPDATE CURRENT_TIMESTAMP` column default.

**Key Fields**:
- `BookId`: Auto-incrementing (`SERIAL`) primary key
- `Title`, `Author`: Required fields; plain B-tree indexes back `ILIKE` search (no MySQL-style `FULLTEXT` index in Postgres)
- `CopyrightDate`: Accepts year-only (`YYYY`) which is converted to `YYYY-01-01 00:00:00`
- `IsbnNumber`: ISBN-10 format
- `IsbnNumber13`: ISBN-13 format
- `CoverType`: Physical format (Hard, Soft, Digital); when `Digital`, `Location` must be `DOWNLOAD`
- `Recycled`: Soft delete flag (0=active, 1=removed/donated)
- `Location`: Required field, must be one of the valid locations (`GET /valid_locations`)
- `LastUpdate`: Automatically updated timestamp

**Business Logic**:
- Year-only copyright dates are automatically expanded to full timestamps
- Title and Author searches use `ILIKE` (case-insensitive) against the indexed columns
- Recycled flag enables soft deletes (preserves history while marking book as removed)

### books_read

Tracks reading history with dates and notes.

**Schema**:
```sql
CREATE TABLE books_read (
    BookId     INTEGER    NOT NULL,
    ReadDate   DATE       NOT NULL,
    ReadNote   TEXT       DEFAULT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (BookId, ReadDate),
    CONSTRAINT fk_books_read_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE
);
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
- Saving a non-empty `ReadNote` triggers an embedding refresh in `book_note_embeddings` (source `read_note`)

### tag_labels

Stores unique tag definitions.

**Schema**:
```sql
CREATE TABLE tag_labels (
    TagId  SERIAL       NOT NULL,
    Label  VARCHAR(50)  DEFAULT NULL,
    PRIMARY KEY (TagId),
    UNIQUE (Label)
);
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
    BookId     INTEGER    NOT NULL,
    TagId      INTEGER    NOT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (BookId, TagId),
    CONSTRAINT fk_books_tags_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_books_tags_tag FOREIGN KEY (TagId)
        REFERENCES tag_labels (TagId) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Key Fields**:
- Composite primary key: (`BookId`, `TagId`)
- `BookId`: References books table
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
    ImageId    SERIAL       NOT NULL,
    BookId     INTEGER      NOT NULL,
    Name       VARCHAR(255) DEFAULT NULL,
    Url        VARCHAR(255) DEFAULT NULL,
    ImageType  VARCHAR(64)  DEFAULT 'cover-face',
    LastUpdate TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ImageId),
    CONSTRAINT fk_images_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE
);
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
    RecordId             BIGSERIAL  NOT NULL,
    BookId               INTEGER    NOT NULL,
    StartDate            TIMESTAMP  NOT NULL,
    LastReadablePage     BIGINT     NOT NULL,
    EstimateDate         TIMESTAMP  DEFAULT NULL,
    EstimatedFinishDate  TIMESTAMP  DEFAULT NULL,
    PRIMARY KEY (RecordId),
    CONSTRAINT fk_complete_date_estimates_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Key Fields**:
- `RecordId`: Auto-incrementing (`BIGSERIAL`) primary key used to track daily progress
- `BookId`: Foreign key to books table
- `StartDate`: When reading estimate began
- `LastReadablePage`: Total readable pages in book
- `EstimateDate`: When estimate was calculated
- `EstimatedFinishDate`: Predicted completion date (based on reading pace)

**Business Logic**:
- Multiple reading sessions can exist for the same book (e.g., re-reads)
- RecordId is used to associate daily page records
- Completion estimates use linear regression on daily page progress
- `EstimateDate` is not rewritten when the book already has a `ReadDate` after the estimate's
  `StartDate` — otherwise viewing a finished book's record would incorrectly mark it "recently touched"

### daily_page_records

Tracks day-by-day reading progress.

**Schema**:
```sql
CREATE TABLE daily_page_records (
    RecordDate TIMESTAMP  NOT NULL,
    Page       BIGINT     NOT NULL,
    RecordId   BIGINT     NOT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (RecordDate, RecordId),
    CONSTRAINT fk_daily_page_records_record FOREIGN KEY (RecordId)
        REFERENCES complete_date_estimates (RecordId) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Key Fields**:
- Composite primary key: (`RecordDate`, `RecordId`)
- `RecordId`: Foreign key to complete_date_estimates
- `RecordDate`: Date of reading progress
- `Page`: Page number reached on this date

**Business Logic**:
- Each date can have only one page record per estimate session
- Used for calculating reading pace and estimated completion
- Page numbers should be cumulative (total pages read, not daily increment)

### book_note_embeddings

pgvector embeddings of `BookNote`/`ReadNote`, powering `POST /rag_search` and the chat
`semantic_search_notes` tool.

**Schema**:
```sql
CREATE TABLE book_note_embeddings (
    id         SERIAL       NOT NULL,
    bookid     INTEGER      NOT NULL,
    source     VARCHAR(20)  NOT NULL CHECK (source IN ('book_note', 'read_note')),
    read_date  DATE         DEFAULT NULL,
    content    TEXT         NOT NULL,
    embedding  vector(768),
    updated_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_bne_book FOREIGN KEY (bookid)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_bne_embedding_hnsw ON book_note_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE UNIQUE INDEX idx_bne_unique_book_note ON book_note_embeddings (bookid) WHERE source = 'book_note';
CREATE UNIQUE INDEX idx_bne_unique_read_note ON book_note_embeddings (bookid, read_date) WHERE source = 'read_note';
```

**Key Fields**:
- `source`: `book_note` (one row per book) or `read_note` (one row per book+`read_date`)
- `embedding`: vector dimension (768 by default) must match `ai_agent.embed_dimensions` in `configuration.json`
- HNSW index enables approximate cosine-similarity search with no separate training step

**Business Logic**:
- Saving a `BookNote` or `ReadNote` auto-triggers a re-embed of that row
- Bulk (re)indexing via `poetry run python database/index_notes.py [--rebuild]`
- Vector dimension is fixed at table-creation time; changing `embed_dimensions` requires recreating the table

### embedding_index_state

Single-row table recording which embedding model actually produced the vectors in
`book_note_embeddings`, so `book-service` and `booksmcp` can refuse to start against a
mismatched model rather than silently mixing embedding spaces.

**Schema**:
```sql
CREATE TABLE embedding_index_state (
    id               INTEGER   PRIMARY KEY DEFAULT 1,
    embed_host       TEXT      NOT NULL,
    embed_model      TEXT      NOT NULL,
    embed_dimensions INTEGER   NOT NULL,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT embedding_index_state_singleton CHECK (id = 1)
);
```

**Business Logic**:
- Written only by `index_notes.py --rebuild` (or `--mark-current` to seed a baseline without re-embedding), never by incremental indexing
- Checked at process startup against the configured `ai_agent.embed_host`/`embed_model`/`embed_dimensions`; mismatch is a fatal startup error, not a warning

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

4. **books → book_note_embeddings**
   - One book has one `book_note` embedding and up to one `read_note` embedding per `ReadDate`

5. **complete_date_estimates → daily_page_records**
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
- Auto-incrementing (`SERIAL`/`BIGSERIAL`) PKs for books, images, tag_labels, complete_date_estimates, book_note_embeddings

### Secondary Indexes
- `idx_books_title`, `idx_books_author`, `idx_books_location` on `books` (search/filter support; `ILIKE` for case-insensitive matches, not MySQL `FULLTEXT`)
- `idx_bne_embedding_hnsw` (HNSW, cosine ops) on `book_note_embeddings.embedding` for semantic search
- `idx_bne_unique_book_note` / `idx_bne_unique_read_note` (partial unique indexes) enforce one embedding per book-note / per book+read_date

### Composite Primary Keys
- books_read: (BookId, ReadDate)
- books_tags: (BookId, TagId)
- daily_page_records: (RecordDate, RecordId)

These composite keys ensure uniqueness while enabling efficient queries.

## Auto-Updated Fields

`LastUpdate` columns are maintained by a shared `update_last_update()` PL/pgSQL trigger function
(`BEFORE UPDATE`), applied per-table:

- `books.LastUpdate`
- `books_read.LastUpdate`
- `books_tags.LastUpdate`
- `images.LastUpdate`
- `daily_page_records.LastUpdate`

`book_note_embeddings.updated_at` and `embedding_index_state.updated_at` are set at insert/rebuild
time rather than via a trigger.

These timestamps help track data freshness (e.g. the `get_recently_edited_books`/`/recent` "recently
touched" ranking) and enable caching strategies.

## Database Size Considerations

The schema is designed to scale to tens of thousands of books and millions of reading records.
`BookId`, `TagId`, `ImageId`, `RecordId`, and `book_note_embeddings.id` are all Postgres
`SERIAL`/`BIGSERIAL` sequences rather than fixed MySQL `AUTO_INCREMENT` counters — actual current
row counts are best checked directly (`SELECT count(*) FROM ...`) rather than inferred from schema
defaults.
