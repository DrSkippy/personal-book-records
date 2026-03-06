import axios from 'axios';
import { searchBooks, getCompleteRecord, getRecentBooks } from './books';
import { getBooksRead, getYearlySummary } from './reads';
import { getTagsForBook, searchByTag, getTagCounts } from './tags';
import { getEstimates } from './estimates';

const ollamaClient = axios.create({
  baseURL: import.meta.env.VITE_OLLAMA_BASE_URL,
});

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_call_id?: string;
  tool_calls?: OllamaToolCall[];
}

export interface OllamaToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface OllamaChatResponse {
  choices: Array<{
    message: {
      role: string;
      content: string | null;
      tool_calls?: OllamaToolCall[];
    };
    finish_reason: string;
  }>;
}

const tools = [
  {
    type: 'function',
    function: {
      name: 'search_books',
      description: 'Search the book collection by author, title, location, ISBN, or BookId. Returns a list of matching books.',
      parameters: {
        type: 'object',
        properties: {
          Author: { type: 'string', description: 'Author name (partial match supported)' },
          Title: { type: 'string', description: 'Book title (partial match supported)' },
          Location: { type: 'string', description: 'Shelf location (e.g. Main Collection, Bedroom, Storage)' },
          IsbnNumber: { type: 'string', description: 'ISBN-10' },
          IsbnNumber13: { type: 'string', description: 'ISBN-13' },
          BookId: { type: 'number', description: 'Exact book ID' },
          BookNote: { type: 'string', description: 'Search within book notes/annotations (partial match supported)' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_book_details',
      description: 'Get the full record for a specific book including metadata, reads, tags, and images.',
      parameters: {
        type: 'object',
        properties: {
          bookId: { type: 'number', description: 'The BookId of the book' },
        },
        required: ['bookId'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_recent_books',
      description: 'Get recently updated books from the collection.',
      parameters: {
        type: 'object',
        properties: {
          limit: { type: 'number', description: 'Number of recent books to return (default 10)' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_books_read_by_year',
      description: 'Get books that were read in a given year. Omit year to get all read books across all years.',
      parameters: {
        type: 'object',
        properties: {
          year: { type: 'number', description: 'Year (e.g. 2023). Omit for all years.' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_reading_summary',
      description: 'Get a yearly reading summary showing pages and books read per year.',
      parameters: {
        type: 'object',
        properties: {
          year: { type: 'number', description: 'Specific year to filter to. Omit for all years.' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_tags_for_book',
      description: 'Get all tags associated with a specific book.',
      parameters: {
        type: 'object',
        properties: {
          bookId: { type: 'number', description: 'The BookId of the book' },
        },
        required: ['bookId'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'search_books_by_tag',
      description: 'Find all books that have a specific tag label.',
      parameters: {
        type: 'object',
        properties: {
          tag: { type: 'string', description: 'Exact tag label to search for (e.g. "birding", "fiction")' },
        },
        required: ['tag'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_tag_counts',
      description: 'Get the count of books for each tag. Optionally filter by a prefix.',
      parameters: {
        type: 'object',
        properties: {
          prefix: { type: 'string', description: 'Optional prefix to filter tag names' },
        },
        required: [],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_reading_estimates',
      description: 'Get reading estimate sessions for a specific book.',
      parameters: {
        type: 'object',
        properties: {
          bookId: { type: 'number', description: 'The BookId of the book' },
        },
        required: ['bookId'],
      },
    },
  },
];

export async function executeTool(name: string, args: Record<string, unknown>): Promise<string> {
  try {
    let result: unknown;
    switch (name) {
      case 'search_books':
        result = await searchBooks(args as Record<string, string | number>);
        break;
      case 'get_book_details':
        result = await getCompleteRecord(args.bookId as number);
        break;
      case 'get_recent_books':
        result = await getRecentBooks(args.limit as number | undefined);
        break;
      case 'get_books_read_by_year':
        result = await getBooksRead(args.year as number | undefined);
        break;
      case 'get_reading_summary':
        result = await getYearlySummary(args.year as number | undefined);
        break;
      case 'get_tags_for_book':
        result = await getTagsForBook(args.bookId as number);
        break;
      case 'search_books_by_tag':
        result = await searchByTag(args.tag as string);
        break;
      case 'get_tag_counts':
        result = await getTagCounts(args.prefix as string | undefined);
        break;
      case 'get_reading_estimates':
        result = await getEstimates(args.bookId as number);
        break;
      default:
        return JSON.stringify({ error: `Unknown tool: ${name}` });
    }
    return JSON.stringify(result);
  } catch (err) {
    return JSON.stringify({ error: String(err) });
  }
}

export async function ollamaChat(messages: OllamaMessage[]): Promise<OllamaChatResponse> {
  const response = await ollamaClient.post<OllamaChatResponse>('/v1/chat/completions', {
    model: import.meta.env.VITE_OLLAMA_MODEL,
    messages,
    tools,
    stream: false,
  });
  return response.data;
}
