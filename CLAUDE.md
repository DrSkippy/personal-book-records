# CLAUDE.md

## Project Layout

```
personal-book-records/
├── book-records-react/     # React/Vite/TypeScript SPA frontend
├── tools/                  # Python backend (API, MCP, CLI)
│   ├── book_service/
│   │   ├── books/          # Flask REST API (port 8084)
│   │   ├── booksmcp/       # FastMCP server (port 3005)
│   │   ├── booksdb/        # DB layer (api_util.py, config.py)
│   │   ├── config/         # configuration.json (gitignored)
│   │   └── test_books/     # Integration tests
│   ├── bookdbtool/         # CLI REPL tools
│   ├── test/               # Unit/mock tests
│   ├── Makefile            # All build/run/test targets
│   └── pyproject.toml      # Poetry project
└── books.drskippy.app      # nginx site config (deploy to /etc/nginx/sites-available/)
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
make build-test          # build test images
make run-test-all        # start containers (book-service:9999, mcp:3005)
make test                # run integration tests against containers
make stop-test-all       # tear down
make test-bookdbtool     # unit tests (no Docker)
```

**Docker conventions:**
- Book service Dockerfile: `WORKDIR=/app`, `PYTHONPATH=/app`
- `books/` package copied to `/app/books/`; `api.ini` uses `module = books.api`
- Container names use IMAGE vars (no `:latest`); image tags use TAG vars
- On `lambda-dual` host, images are pushed to local registry `localhost:5000`

**Auth:** All API requests require `x-api-key` header.

## Frontend (book-records-react/)

**Stack:** Vite + React 19 + TypeScript + Tailwind CSS + TanStack Query + React Hook Form + Zod + Recharts

**Dev:**
```bash
cd book-records-react
npm run dev       # dev server
npm run build     # production build → dist/
npm run lint
```

**Config via `.env.local` (gitignored):**
```
VITE_API_BASE_URL=
VITE_API_KEY=
VITE_RESOURCE_BASE_URL=
VITE_OLLAMA_BASE_URL=
VITE_OLLAMA_MODEL=
```

**Structure:**
- `src/api/` — axios API clients (`client.ts` wraps all book-service calls)
- `src/hooks/` — TanStack Query hooks, one per resource type
- `src/pages/` — route-level page components
- `src/components/` — shared UI components
- `src/types/index.ts` — all shared TypeScript types
- `src/lib/` — constants, date utils, validation schemas

## Database

- **Database:** `book_collection` (MySQL)
- **Tables:** `books`, `books_read`, `tag_labels`, `books_tags`, `complete_date_estimates`, `daily_page_records`, `images`
- **Key columns:** `BookId`, `IsbnNumber`, `IsbnNumber13`, `BookNote`, `TagId`, `RecordId`, `Page`, `ImageId`, `Name`, `Url`, `ImageType`, `LastUpdate`
- CASCADE foreign keys handle child record deletion when a book is deleted
- `Category` column was dropped in the Feb 2026 migration

## nginx Deployment

```bash
sudo cp books.drskippy.app /etc/nginx/sites-available/books.drskippy.app
sudo nginx -t && sudo systemctl reload nginx
```

The React `dist/` must be built first (`npm run build` inside `book-records-react/`).
