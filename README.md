# personal-book-records

A personal book collection management system built around a MySQL database. The project provides four interfaces to the same data: a React web app, a REST API, an MCP server for AI integration, and a command-line REPL.

## Components

### React Frontend (`book-records-react/`)

A Vite + React + TypeScript SPA served via nginx at `https://books.drskippy.app` (Cloudflare Zero Trust tunnel). All configuration is via `.env.local`.

**Pages:**
- **Dashboard** — reading stats, recent books, yearly progress charts
- **Book Search** — search by title, author, location, ISBN, or tag
- **Book Detail** — full record with reads, tags, images, and estimates
- **Inventory** — full collection table with sorting and filtering
- **Books by Year** — books read in a given year
- **Progress** — daily page records and reading progress
- **Reading Estimates** — per-book estimate sessions and completion tracking
- **Carousel** — visual cover image browser
- **Add / Edit Book** — create and update book records
- **Add Read Date / Page Progress / Estimate** — logging forms
- **Batch Update Read Notes** — bulk-edit notes across read records
- **AI Chat** — Ollama-backed assistant with tool access to the collection

**Environment variables (`.env.local`):**
```
VITE_API_BASE_URL=       # REST API base URL
VITE_API_KEY=            # x-api-key header value
VITE_RESOURCE_BASE_URL=  # static image/resource base URL
VITE_OLLAMA_BASE_URL=    # Ollama server base URL
VITE_OLLAMA_MODEL=       # Ollama model name
```

---

### REST API (`tools/book_service/books/`)

Flask + uWSGI service running on port 8084. API key authenticated via `x-api-key` header. Full OpenAPI spec at `tools/openapi.yaml`.

See [`tools/README.md`](tools/README.md) for setup, endpoints, and deployment.

---

### MCP Server (`tools/book_service/booksmcp/`)

FastMCP server on port 3005 exposing the book collection to AI assistants (Claude, etc.) via the Model Context Protocol.

---

### CLI REPL (`tools/bookdbtool/`)

Interactive command-line tool for querying and managing the collection. Includes book search, estimate tools, ISBN lookup, AI tools, and visualization.

---

### nginx Config (`books.drskippy.app`)

Site config for serving the React build at port 83 behind the Cloudflare Zero Trust tunnel. Copy to `/etc/nginx/sites-available/` to deploy.

---

## Database

MySQL database `book_collection`. Schema and migration scripts in `tools/database/`. Key tables: `books`, `books_read`, `tag_labels`, `books_tags`, `complete_date_estimates`, `daily_page_records`, `images`.
