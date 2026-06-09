-- book-collection: complete current-state schema
--
-- This is the canonical schema for a fresh install. Run setup_db.py instead
-- of this file directly — it handles the pgvector extension (which requires a
-- superuser) and verifies the result.
--
-- If running manually, a superuser must first enable pgvector:
--   psql -d book-collection -c "CREATE EXTENSION IF NOT EXISTS vector;"
-- Then run this file as the application user (scott):
--   psql -U scott -h <host> -p <port> -d book-collection < schema_current.sql

-- ============================================================================
-- Extensions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Trigger function for auto-updating LastUpdate columns
-- ============================================================================

CREATE OR REPLACE FUNCTION update_last_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.LastUpdate = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Parent tables (no FK dependencies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS books (
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

CREATE INDEX IF NOT EXISTS idx_books_title    ON books (Title);
CREATE INDEX IF NOT EXISTS idx_books_author   ON books (Author);
CREATE INDEX IF NOT EXISTS idx_books_location ON books (Location);

DROP TRIGGER IF EXISTS trg_books_update ON books;
CREATE TRIGGER trg_books_update
    BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_last_update();


CREATE TABLE IF NOT EXISTS tag_labels (
    TagId  SERIAL       NOT NULL,
    Label  VARCHAR(50)  DEFAULT NULL,
    PRIMARY KEY (TagId),
    UNIQUE (Label)
);

-- ============================================================================
-- Child tables (depend on books and/or tag_labels)
-- ============================================================================

CREATE TABLE IF NOT EXISTS books_read (
    BookId     INTEGER    NOT NULL,
    ReadDate   DATE       NOT NULL,
    ReadNote   TEXT       DEFAULT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (BookId, ReadDate),
    CONSTRAINT fk_books_read_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TRIGGER IF EXISTS trg_books_read_update ON books_read;
CREATE TRIGGER trg_books_read_update
    BEFORE UPDATE ON books_read
    FOR EACH ROW EXECUTE FUNCTION update_last_update();


CREATE TABLE IF NOT EXISTS books_tags (
    BookId     INTEGER    NOT NULL,
    TagId      INTEGER    NOT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (BookId, TagId),
    CONSTRAINT fk_books_tags_book FOREIGN KEY (BookId)
        REFERENCES books (BookId) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_books_tags_tag FOREIGN KEY (TagId)
        REFERENCES tag_labels (TagId) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TRIGGER IF EXISTS trg_books_tags_update ON books_tags;
CREATE TRIGGER trg_books_tags_update
    BEFORE UPDATE ON books_tags
    FOR EACH ROW EXECUTE FUNCTION update_last_update();


CREATE TABLE IF NOT EXISTS complete_date_estimates (
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

-- ============================================================================
-- Grandchild tables (depend on complete_date_estimates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_page_records (
    RecordDate TIMESTAMP  NOT NULL,
    Page       BIGINT     NOT NULL,
    RecordId   BIGINT     NOT NULL,
    LastUpdate TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (RecordDate, RecordId),
    CONSTRAINT fk_daily_page_records_record FOREIGN KEY (RecordId)
        REFERENCES complete_date_estimates (RecordId) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TRIGGER IF EXISTS trg_daily_page_records_update ON daily_page_records;
CREATE TRIGGER trg_daily_page_records_update
    BEFORE UPDATE ON daily_page_records
    FOR EACH ROW EXECUTE FUNCTION update_last_update();

-- ============================================================================
-- Additional child tables (depend on books)
-- ============================================================================

CREATE TABLE IF NOT EXISTS images (
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

DROP TRIGGER IF EXISTS trg_images_update ON images;
CREATE TRIGGER trg_images_update
    BEFORE UPDATE ON images
    FOR EACH ROW EXECUTE FUNCTION update_last_update();

-- ============================================================================
-- RAG: vector embeddings for book and reading notes
--
-- Dimension (768) must match embed_dimensions in configuration.json.
-- ============================================================================

CREATE TABLE IF NOT EXISTS book_note_embeddings (
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

-- HNSW index for fast cosine similarity search (no training step required)
CREATE INDEX IF NOT EXISTS idx_bne_embedding_hnsw
    ON book_note_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- One book_note embedding per book
CREATE UNIQUE INDEX IF NOT EXISTS idx_bne_unique_book_note
    ON book_note_embeddings (bookid)
    WHERE source = 'book_note';

-- One read_note embedding per (book, read_date)
CREATE UNIQUE INDEX IF NOT EXISTS idx_bne_unique_read_note
    ON book_note_embeddings (bookid, read_date)
    WHERE source = 'read_note';
