-- RAG: pgvector extension and note embeddings table
-- Run against the book-collection database:
--   psql -U scott -h 192.168.1.90 -p 5434 -d book-collection < add_pgvector.sql
--
-- The vector(768) dimension must match embed_dimensions in configuration.json.
-- To use a different model, change the dimension here and run a full re-index.

CREATE EXTENSION IF NOT EXISTS vector;

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
