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
| `VITE_OLLAMA_BASE_URL` | Ollama/LM-compatible chat API base URL |
| `VITE_OLLAMA_MODEL` | Model name (e.g. `openai/gpt-oss-20b`) |
| `VITE_OLLAMA_API_KEY` | Bearer token for AI chat API |

## Changelog

### v0.1.0
- **Carousel fixes**: corrected right-boundary infinite scroll (no longer collapses to 1 slide at end of collection); backward navigation wraps to last book; removed ring-buffer corruption of `maxIdRef`; single left-arrow click now immediately shows newly loaded book
- **Add Book form**: location dropdown filters to `DOWNLOAD` only when Cover Type is `Digital`; `DOWNLOAD` added as a valid location
- **Notes display**: `\n` characters in `BookNote` and `ReadNote` now render as line breaks everywhere notes are displayed read-only
- **Navigation bar**: UI version displayed alongside API version
- **AI Chat**: Bearer token authentication support (`VITE_OLLAMA_API_KEY`); updated to `openai/gpt-oss-20b` model
