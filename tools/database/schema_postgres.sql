-- book-collection database schema for PostgreSQL
-- Run this once against an existing PostgreSQL database named "book-collection".
--
-- Usage:
--   psql -U scott -h <host> -d book-collection < schema_postgres.sql

-- ============================================================================
-- Trigger function for auto-updating LastUpdate column
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

CREATE TRIGGER trg_images_update
BEFORE UPDATE ON images
FOR EACH ROW EXECUTE FUNCTION update_last_update();
