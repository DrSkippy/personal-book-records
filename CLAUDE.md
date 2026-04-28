# CLAUDE.md

## Project Layout

```
personal-book-records/
├── book-records-react/     # React/Vite/TypeScript SPA frontend (v0.2.0)
├── tools/                  # Python backend (API, MCP, CLI)
│   ├── book_service/
│   │   ├── books/          # Flask REST API (port 8084, v0.18.0)
│   │   ├── booksmcp/       # FastMCP server (port 3005)
│   │   ├── booksdb/        # DB layer (api_util.py, config.py)
│   │   ├── config/         # configuration.json (gitignored)
│   │   └── test_books/     # Integration tests
│   ├── bookdbtool/         # CLI REPL tools
│   ├── test/               # Unit/mock tests
│   ├── Makefile            # All build/run/test targets
│   └── pyproject.toml      # Poetry project
├── docker-compose.yml      # Root compose: pulls from local registry, starts both services
└── books.drskippy.app      # Single nginx config (port 83): SPA + /api/ + /mcp/ + /ollama/
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

**Critical pattern:** `__all__` in `api_util.py` must include `pymysql` and `datetime` — these are re-exported for use in other modules that do `from booksdb.api_util import *`.

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
`configuration.json` is mounted as a read-only volume — config changes only need a container restart, not a rebuild.

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
VITE_OLLAMA_BASE_URL=    # e.g. https://books.drskippy.app/ollama
VITE_OLLAMA_MODEL=
VITE_OLLAMA_API_KEY=
```

API calls are same-origin via the `/api/` nginx prefix — no CORS headers needed.

**Structure:**
- `src/api/` — axios API clients (`client.ts` wraps all book-service calls, `ollama.ts` handles AI chat)
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

The AI Chat page (`/ai-chat`) uses an OpenAI-compatible `/v1/chat/completions` endpoint with tool-calling support.

**Local LM servers:**
| Server | URL | Auth |
|---|---|---|
| Primary (LM Studio) | `http://192.168.1.91:1234` | Bearer token required |
| Secondary | `http://192.168.1.91:5434` | — |

**Current model:** `openai/gpt-oss-20b`

**Auth:** Bearer token set via `VITE_OLLAMA_API_KEY` in `.env.local`. Applied as `Authorization: Bearer <token>` header in `src/api/ollama.ts`.

**Tools available to the model (9):** `search_books`, `get_book_details`, `get_recent_books`, `get_books_read_by_year`, `get_reading_summary`, `get_tags_for_book`, `search_books_by_tag`, `get_tag_counts`, `get_reading_estimates`.

**Conversation loop:** Up to 10 tool-call iterations per user message. History maintained in `ollamaHistoryRef` for the session; reset on "Clear".

## Database

- **Database:** `book_collection` (MySQL)
- **Tables:** `books`, `books_read`, `tag_labels`, `books_tags`, `complete_date_estimates`, `daily_page_records`, `images`
- **Key columns:** `BookId`, `IsbnNumber`, `IsbnNumber13`, `BookNote`, `TagId`, `RecordId`, `Page`, `ImageId`, `Name`, `Url`, `ImageType`, `LastUpdate`
- CASCADE foreign keys handle child record deletion when a book is deleted
- `Category` column was dropped in the Feb 2026 migration
- Valid locations: `Main Collection`, `Bedroom`, `Storage`, `Oversized`, `Pets`, `Woodwork`, `Reference`, `Birding`, `DOWNLOAD`

## nginx Deployment

Single config file (`books.drskippy.app`) handles everything on port 83:
- `/api/` → book-service:8084 (strips prefix)
- `/mcp/` → booksmcp:3005 (strips prefix)
- `/ollama/` → LM Studio at 192.168.1.91:1234 (strips prefix)
- `/` → React SPA (`dist/`) with SPA fallback

```bash
sudo cp books.drskippy.app /etc/nginx/sites-available/books.drskippy.app
sudo nginx -t && sudo systemctl reload nginx
```

The React `dist/` must be built first (`npm run build` inside `book-records-react/`). The previous separate configs (`book-service.drskippy.app`, `booksmcp.lambda-dual.home.lan`) have been removed.
