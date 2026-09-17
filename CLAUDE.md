# CLAUDE.md

## Project Layout

```
personal-book-records/
├── book-records-react/     # React/Vite/TypeScript SPA frontend (v0.5.0)
├── tools/                  # Python backend (API, MCP, CLI)
│   ├── book_service/
│   │   ├── books/          # Flask REST API (port 8084, v0.21.1)
│   │   ├── booksmcp/       # FastMCP server (port 3005, v3.3.1)
│   │   ├── booksdb/        # DB layer (api_util.py, config.py, chat_util.py)
│   │   ├── config/         # configuration.json (transcrypt-encrypted, committed)
│   │   └── test_books/     # Integration tests
│   ├── bookdbtool/         # CLI REPL tools
│   ├── test/               # Unit/mock tests
│   ├── Makefile            # All build/run/test targets
│   └── pyproject.toml      # Poetry project
├── docker-compose.yml      # Root compose: pulls from local registry, starts both services
└── books.drskippy.app      # Single nginx config (port 83): SPA + /api/ + /mcp/
```

## Backend (tools/)

**All Python commands use Poetry:**
```bash
cd tools
poetry run python ...
poetry run pytest ...
```

**Key files:**
- `book_service/books/api.py` — Flask app entry point
- `book_service/booksdb/api_util.py` — DB utilities, imported via `from booksdb.api_util import *`
- `book_service/booksdb/config.py` — DB config loader
- `book_service/booksmcp/server.py` — MCP server entry point

**Critical pattern:** `__all__` in `api_util.py` must include `psycopg2` and `datetime` — these are re-exported for use in other modules that do `from booksdb.api_util import *`.

**Docker builds run from `tools/` (repo root for book-service):**
```bash
cd tools
make build-all           # build book-service and booksmcp images
make push-all            # push both images to local registry (localhost:5000)
make build-test          # build test images
make run-test-all        # start containers (book-service:9999, mcp:3005)
make test                # run integration tests against containers
make stop-test-all       # tear down
make test-bookdbtool     # unit tests (no Docker)
```

**Deployment from repo root:**
```bash
docker compose up -d     # pulls from localhost:5000, starts book-service + booksmcp
```
`configuration.json` is baked into the image at build time (`COPY ./book_service/config/*`) — config changes require `make build-all push-all` and a redeploy, not just a container restart.

**Docker conventions:**
- Book service Dockerfile: `WORKDIR=/app`, `PYTHONPATH=/app`
- `books/` package copied to `/app/books/`; `api.ini` uses `module = books.api`
- Container names use IMAGE vars (no `:latest`); image tags use TAG vars
- Images are built in `tools/` and pushed to local registry `localhost:5000`

**Auth:** All API requests require `x-api-key` header.

**Carousel adjacent API behavior:**
- `GET /complete_record/<id>/next` — returns next book by ID; returns `{}` at end of collection (no forward wrap)
- `GET /complete_record/<id>/prev` — returns previous book by ID; wraps to `max(BookId)` at start of collection
- `GET /complete_records_window/<id>/<n>` — returns n books centered on id; fills deficit from opposite side (no ring-wrap to far end of collection)

## Frontend (book-records-react/)

**Stack:** Vite + React 19 + TypeScript + Tailwind CSS + TanStack Query + React Hook Form + Zod + Recharts

**Dev:**
```bash
cd book-records-react
npm run dev       # dev server
npm run build     # production build → dist/
npm run lint
```

**Config via `.env.local` (gitignored; copy from `.env.local.example`):**
```
VITE_API_BASE_URL=       # e.g. https://books.drskippy.app/api  (no trailing slash)
VITE_API_KEY=
VITE_RESOURCE_BASE_URL=
```

API calls are same-origin via the `/api/` nginx prefix — no CORS headers needed.

**Structure:**
- `src/api/` — axios API clients (`client.ts` wraps all book-service calls, `chat.ts` posts the conversation to `/api/chat`)
- `src/hooks/` — TanStack Query hooks, one per resource type
- `src/pages/` — route-level page components
- `src/components/` — shared UI components
- `src/types/index.ts` — all shared TypeScript types
- `src/lib/` — constants, date utils, validation schemas
- `src/vite-env.d.ts` — TypeScript declarations for Vite globals (`__APP_VERSION__`)

**UI version:** Injected from `package.json` at build time via `define: { __APP_VERSION__ }` in `vite.config.ts`. Displayed in the nav bar alongside the API version.

**Location / CoverType rule:** When `CoverType` is `"Digital"`, the location dropdown in `BookForm` shows only `"DOWNLOAD"`. All other cover types exclude `"DOWNLOAD"`. This is enforced in `BookForm.tsx` via `watch('CoverType')`.

**Notes display:** All read-only note fields (`BookNote`, `ReadNote`) use `whitespace-pre-line` so `\n` characters render as line breaks. The `BookNote` textarea inputs handle newlines natively.

## AI Chat

The AI Chat page (`/ai-chat`) holds no model configuration. It POSTs the running conversation to `POST /api/chat` (same-origin, via `VITE_API_BASE_URL`/`VITE_API_KEY`, see `src/api/chat.ts`); `book-service` (`tools/book_service/books/api.py`, `/chat` route) runs the full OpenAI-compatible tool-calling loop server-side and returns the result. The frontend never knows the chat model, host, or API key.

**Chat LLM server:** configured via `ai_agent.chat_host`/`chat_model`/`chat_api_key` in `tools/book_service/config/configuration.json` (or `AI_CHAT_HOST`/`AI_CHAT_MODEL`/`AI_CHAT_API_KEY` env overrides). Currently `http://192.168.1.91:1234`, model `openai/gpt-oss-20b` — the same physical LM Studio instance used for RAG embeddings (`ai_agent.embed_*`), though the two are configured independently and are not required to stay on the same host.

**Tool-calling loop:** implemented in `tools/book_service/booksdb/chat_util.py` (`run_chat_loop`), up to 10 iterations per request. `bookdbtool`'s CLI chat (`OllamaAgent` in `ai_tools.py`) is a separate consumer of the same `ai_agent.chat_*` config, with its own smaller 5-tool set.

**Tools available to the model (12):** `search_books`, `get_book_details`, `get_recently_edited_books`, `get_recently_read_books`, `get_books_read_by_year`, `get_reading_summary`, `get_tags_for_book`, `search_books_by_tag`, `get_tag_counts`, `get_reading_estimates`, `add_tag_to_book`, `semantic_search_notes`.

`get_recently_edited_books` ranks by `LastUpdate` (edits/tags/images/estimates — "recently touched"; calls `get_recently_touched`/the `/recent` REST endpoint under the hood). `get_recently_read_books` ranks by `books_read.ReadDate` ("recently finished"; calls `get_recently_read`/`/recently_read`). These are deliberately separate tools with non-overlapping names: the model previously conflated "recent" with "last edited" when asked about recently-read books, first by picking the wrong tool, then (even after a `get_recent_books` name/description fix) by calling the edit-ranked tool anyway and surfacing a stale `ReadDate` from a follow-up `get_book_details` call. Dropping "recent" entirely from the edit-ranked tool's name closes that gap.

**Conversation loop:** the frontend sends its accumulated history (user/assistant/tool turns, no system message — the server owns that) on every turn; the backend runs the loop to completion and returns the updated history plus a display trace (each tool call/result, then the final reply) in a single response. History lives in `historyRef` client-side for the session; reset on "Clear". There is no live/incremental reveal of tool calls mid-turn — the loading indicator covers the wait, and the full trace renders once the response arrives.

## Database

- **Database:** `book-collection` (PostgreSQL, port 5434) — migrated from MySQL in May 2026 (`tools/database/migrate_mysql_to_postgres.py`); driver is `psycopg2`, not `pymysql`
- **Tables:** `books`, `books_read`, `tag_labels`, `books_tags`, `complete_date_estimates`, `daily_page_records`, `images`, `book_note_embeddings`, `embedding_index_state`
- **Key columns:** `BookId`, `IsbnNumber`, `IsbnNumber13`, `BookNote`, `TagId`, `RecordId`, `Page`, `ImageId`, `Name`, `Url`, `ImageType`, `LastUpdate`
- CASCADE foreign keys handle child record deletion when a book is deleted
- `Category` column was dropped in the Feb 2026 migration (pre-dates the PostgreSQL move)
- `book_note_embeddings` holds pgvector embeddings of `BookNote`/`ReadNote` for `POST /rag_search` and the `semantic_search_notes` chat tool; `embedding_index_state` records which `embed_host`/`embed_model`/`embed_dimensions` the index was built with so a config change can't silently mix embedding spaces
- Valid locations: `Main Collection`, `Bedroom`, `Storage`, `Oversized`, `Pets`, `Woodwork`, `Reference`, `Birding`, `DOWNLOAD`

## nginx Deployment

Single config file (`books.drskippy.app`) handles everything on port 83:
- `/api/` → book-service:8084 (strips prefix)
- `/mcp/` → booksmcp:3005 (strips prefix)
- `/` → React SPA (`dist/`) with SPA fallback

The AI Chat page no longer needs a direct browser-to-LLM proxy (previously `/ollama/` → LM Studio at 192.168.1.91:1234) — chat now goes through `/api/chat`, so that location was removed.

```bash
sudo cp books.drskippy.app /etc/nginx/sites-available/books.drskippy.app
sudo nginx -t && sudo systemctl reload nginx
```

The React `dist/` must be built first (`npm run build` inside `book-records-react/`). The previous separate configs (`book-service.drskippy.app`, `booksmcp.lambda-dual.home.lan`) have been removed.
