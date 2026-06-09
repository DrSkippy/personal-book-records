# personal-book-records

A personal book collection management system built around a PostgreSQL database. The project provides four interfaces to the same data: a React web app, a REST API, an MCP server for AI integration, and a command-line REPL.

## From-Scratch Setup

Full stack on a single host running MySQL, Docker, and nginx.

### Prerequisites
- Docker and Docker Compose
- PostgreSQL running on the host
- nginx
- Node.js 18+ (for building the React frontend)

---

### Step 1 — Configure the backend

```bash
cp tools/book_service/config/configuration_example.json \
   tools/book_service/config/configuration.json
```

Edit `configuration.json`:

| Field | Value |
|-------|-------|
| `username` | PostgreSQL user |
| `password` | PostgreSQL password |
| `database` | `book-collection` |
| `host` | `host.docker.internal` (containers reach host PostgreSQL via this) |
| `port` | `5434` |
| `api_key` | A secret key — generate with `openssl rand -hex 20` |
| `isbn_com.key` | ISBNdb API key (optional, for ISBN lookups) |
| `ai_agent.embed_host` | LM Studio base URL, e.g. `http://192.168.1.91:1234` |
| `ai_agent.embed_model` | Embedding model name loaded in LM Studio |
| `ai_agent.embed_api_key` | LM Studio bearer token |
| `ai_agent.embed_dimensions` | Embedding vector dimension (must match model output, e.g. `768`) |

Then create the root `.env`:

```bash
cp .env.example .env
# Set API_KEY to the same value as api_key in configuration.json
```

---

### Step 2 — Start the backend containers

```bash
docker compose up -d --build
```

Starts `book-service` (port 8084) and `booksmcp` (port 3005). Configuration is mounted as a read-only volume — config changes only need `docker compose restart`, not a rebuild.

Verify:
```bash
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/valid_locations
curl http://localhost:3005/health
```

---

### Step 3 — Build the React frontend

```bash
cd book-records-react
cp .env.local.example .env.local
# Edit .env.local with API URL, key, and resource URL
npm ci && npm run build
```

Output goes to `book-records-react/dist/`.

---

### Step 4 — Configure nginx

One site config handles everything on port 83: the React SPA, REST API (`/api/`), MCP server (`/mcp/`), and Ollama proxy (`/ollama/`).

```bash
sudo cp books.drskippy.app /etc/nginx/sites-available/books.drskippy.app
sudo ln -sf /etc/nginx/sites-available/books.drskippy.app \
            /etc/nginx/sites-enabled/books.drskippy.app
sudo nginx -t && sudo systemctl reload nginx
```

Set `VITE_API_BASE_URL=https://books.drskippy.app/api` in `.env.local` (or `http://localhost:83/api` for local-only access).

---

### Step 5 — Initialize the database (first time only)

A PostgreSQL superuser must create the database and enable the pgvector extension:

```bash
createdb -U postgres -p 5434 book-collection
psql -U postgres -p 5434 -d "book-collection" -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Then apply the full schema as the application user:

```bash
cd tools
poetry run python database/setup_db.py
```

This creates all tables, triggers, indexes, and the vector embeddings table in one shot. It is idempotent — safe to re-run against an existing database.

After adding data, populate the RAG search index:

```bash
poetry run python database/index_notes.py
```

---

### Managing containers

```bash
docker compose up -d           # start (pulls from localhost:5000 registry)
docker compose down            # stop
docker compose logs -f         # tail logs
docker compose restart         # apply configuration.json changes (no rebuild)
make build-all && make push-all  # rebuild images and push to registry
```

---

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
- **AI Chat** — LM Studio-backed assistant with tool access to the collection and RAG semantic search over notes

**Environment variables (`.env.local`):**
```
VITE_API_BASE_URL=       # REST API base URL, e.g. https://books.example.com/api
VITE_API_KEY=            # x-api-key header value
VITE_RESOURCE_BASE_URL=  # static image/resource base URL
VITE_OLLAMA_BASE_URL=    # LM Studio base URL, e.g. https://books.example.com/ollama
VITE_OLLAMA_MODEL=       # Chat model name loaded in LM Studio
VITE_OLLAMA_API_KEY=     # LM Studio bearer token
```

---

### REST API (`tools/book_service/books/`)

Flask + uWSGI service running on port 8084. API key authenticated via `x-api-key` header. Full OpenAPI spec at `tools/book_service/openapi.yaml`.

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

PostgreSQL database `book-collection` (port 5434). Current-state schema in `tools/database/schema_current.sql`; apply via `setup_db.py`. Key tables: `books`, `books_read`, `tag_labels`, `books_tags`, `complete_date_estimates`, `daily_page_records`, `images`, `book_note_embeddings`.
