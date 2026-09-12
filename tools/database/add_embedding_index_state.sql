-- Adds embedding_index_state: a single-row marker recording which
-- embedding model/host produced the vectors currently stored in
-- book_note_embeddings. book-service and booksmcp check this against the
-- configured ai_agent.embed_* values at startup and refuse to start on a
-- mismatch, so a changed embedding model can't silently produce mixed-model
-- (meaningless) similarity search results.
--
-- Run against the book-collection database:
--   psql -U scott -h 192.168.1.90 -p 5434 -d book-collection < add_embedding_index_state.sql
--
-- After applying, seed the baseline for embeddings that already exist
-- (skip this if book_note_embeddings is empty):
--   poetry run python database/index_notes.py --mark-current

CREATE TABLE IF NOT EXISTS embedding_index_state (
    id               INTEGER      PRIMARY KEY DEFAULT 1,
    embed_host       TEXT         NOT NULL,
    embed_model      TEXT         NOT NULL,
    embed_dimensions INTEGER      NOT NULL,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT embedding_index_state_singleton CHECK (id = 1)
);
