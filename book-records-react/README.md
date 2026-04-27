# Book Records — React Frontend

React/Vite/TypeScript SPA for the personal book collection. Connects to the Flask book-service REST API.

## Stack

- Vite + React 19 + TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form + Zod
- Recharts
- Axios

## Setup

```bash
npm install
cp .env.local.example .env.local   # fill in values
npm run dev                         # dev server (localhost:5173)
npm run build                       # production build → dist/
npm run lint
```

## Environment Variables (`.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Book service REST API base URL |
| `VITE_API_KEY` | API key (`x-api-key` header) |
| `VITE_RESOURCE_BASE_URL` | Static resources base URL (images) |
| `VITE_OLLAMA_BASE_URL` | OpenAI-compatible chat API base URL (e.g. LM Studio) |
| `VITE_OLLAMA_MODEL` | Model name (e.g. `openai/gpt-oss-20b`) |
| `VITE_OLLAMA_API_KEY` | Bearer token for AI chat API |

## Pages & Routes

| Route | Page | Description |
|---|---|---|
| `/` | Browse Collection (Dashboard) | Recently updated books, search form, add-by-ISBN, yearly reading report table (sortable) |
| `/books` | Search & Reports | Full book search by author/title/tag/location; inline detail panel |
| `/books/add` | Add Book | Add a new book (manual or pre-filled from ISBN lookup) |
| `/books/:id` | Book Detail | Full record: metadata, read dates, tags, images, reading estimates, prev/next navigation |
| `/books/:id/edit` | Edit Book | Edit book metadata |
| `/read/add/:id` | Add Read Date | Record a new read date for a book |
| `/read/update` | Batch Update Read Notes | Edit `ReadNote` across multiple books at once |
| `/year/:year` | Books Read — Year | Books read in a given year (or all years via `/year/all`); sortable columns |
| `/inventory` | Inventory | Main Collection books with recycled-flag toggle; inline detail panel |
| `/carousel/:id` | Book Carousel | Full-screen carousel starting at a given book ID; left/right navigation |
| `/progress` | Yearly Progress | Cumulative-pages chart (last 15 years) + all-years bar chart |
| `/estimates/:id` | Reading Estimates | Estimated finish dates and reading sessions for a book |
| `/estimates/add/:id` | Add Estimate | Start a new reading session/estimate |
| `/estimates/:id/progress` | Add Page Progress | Log daily page progress for an active estimate |
| `/ai-chat` | AI Chat | Conversational assistant backed by a local LM; uses 9 book-service tools |

## Key Features

### Browse Collection (Dashboard)
- **Recently Updated** list (last 20 books)
- **Search** by author, title, or tag — navigates to Search & Reports
- **Add by ISBN** — pre-fills the Add Book form via ISBN lookup
- **Yearly Reading Reports** table — sortable by Year, Pages, or Books (click column header; ▲/▼ indicator shows active sort)

### Book Detail
- Inline prev/next navigation between books
- Inline `BookNote` editing (saved without leaving the page)
- Tag management (add/remove tags)
- Image gallery
- Reading estimates panel
- Delete with confirmation

### AI Chat
- OpenAI-compatible `/v1/chat/completions` endpoint with tool-calling
- Up to 10 tool-call iterations per user message
- Tools available: `search_books`, `get_book_details`, `get_recent_books`, `get_books_read_by_year`, `get_reading_summary`, `get_tags_for_book`, `search_books_by_tag`, `get_tag_counts`, `get_reading_estimates`
- Markdown rendering toggle
- Session history reset via "Clear" button

### Book Carousel
- Window-based loading (fetches `n` books centered on current ID)
- Backward navigation wraps to the last book in the collection
- Forward navigation stops at the end (no wrap)
- Duplicate-slide prevention when wrapping across collection boundaries

### Add / Edit Book Form
- When `CoverType` is `Digital`, the Location dropdown shows only `DOWNLOAD`
- All other cover types exclude `DOWNLOAD` from the dropdown

### Notes Display
- `BookNote` and `ReadNote` fields render `\n` characters as line breaks everywhere they appear read-only

### Yearly Progress
- Cumulative pages by day-of-year chart (last 15 years, click a line to navigate to that year's book list)
- All-years summary bar chart

## UI Version

Injected from `package.json` at build time via `define: { __APP_VERSION__ }` in `vite.config.ts`. Displayed in the nav bar alongside the live API version.

## Changelog

### v0.2.0
- **Yearly Reading Reports**: columns are now sortable (Year, Pages, Books) with ▲/▼ direction indicator

### v0.1.0
- **Carousel fixes**: corrected right-boundary infinite scroll (no longer collapses to 1 slide at end of collection); backward navigation wraps to last book; removed ring-buffer corruption of `maxIdRef`; single left-arrow click now immediately shows newly loaded book
- **Add Book form**: location dropdown filters to `DOWNLOAD` only when Cover Type is `Digital`; `DOWNLOAD` added as a valid location
- **Notes display**: `\n` characters in `BookNote` and `ReadNote` now render as line breaks everywhere notes are displayed read-only
- **Navigation bar**: UI version displayed alongside API version
- **AI Chat**: Bearer token authentication support (`VITE_OLLAMA_API_KEY`); updated to `openai/gpt-oss-20b` model; markdown rendering toggle
