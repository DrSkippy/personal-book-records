import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import BookTable from '../components/books/BookTable';
import BookDetailPanel from '../components/books/BookDetailPanel';
import { useBooksSearch } from '../hooks/useBooksSearch';
import { searchByTag } from '../api/tags';
import { getCompleteRecordsByIds } from '../api/books';
import { toObjects } from '../lib/utils';
import type { Book, CompleteRecord } from '../types';
import { Search, Plus } from 'lucide-react';

export default function BookSearch() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [author, setAuthor] = useState(searchParams.get('author') || '');
  const [title, setTitle] = useState(searchParams.get('title') || '');
  const [tags, setTags] = useState(searchParams.get('tags') || '');
  const [location, setLocation] = useState(searchParams.get('location') || '');

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const tagParam = searchParams.get('tags');

  const queryParams = {
    ...(searchParams.get('author') && { Author: searchParams.get('author')! }),
    ...(searchParams.get('title') && { Title: searchParams.get('title')! }),
    ...(searchParams.get('isbn') && { IsbnNumber: searchParams.get('isbn')! }),
    ...(searchParams.get('location') && { Location: searchParams.get('location')! }),
    ...(searchParams.get('recycled') && { Recycled: searchParams.get('recycled')! }),
    ...(searchParams.get('BookId') && { BookId: Number(searchParams.get('BookId')) }),
  };

  // Tag search: single query that fetches BookIds then full records
  const { data: tagBooksData, isLoading: tagBooksLoading } = useQuery({
    queryKey: ['tag-books', tagParam],
    queryFn: async () => {
      const tagResponse = await searchByTag(tagParam!);
      const bookIds = tagResponse.data?.map((row: (string | number | null)[]) => row[0] as number) ?? [];
      if (bookIds.length === 0) return [];
      return getCompleteRecordsByIds(bookIds);
    },
    enabled: !!tagParam,
    staleTime: 0,
  });

  // Regular (non-tag) search
  const { data, isLoading: searchLoading, error, refetch } = useBooksSearch(
    tagParam ? {} : queryParams
  );

  const isLoading = tagParam ? tagBooksLoading : searchLoading;

  const books: Book[] = tagParam
    ? (tagBooksData ?? []).map((r: CompleteRecord) => toObjects<Book>(r.book)[0]).filter(Boolean)
    : (data ? toObjects<Book>(data) : []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (author) params.set('author', author);
    if (title) params.set('title', title);
    if (tags) params.set('tags', tags);
    if (location) params.set('location', location);
    setSearchParams(params);
    setSelectedId(null);
  };

  const columns = [
    {
      key: 'BookId',
      label: 'ID',
      render: (value: unknown) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/books/${value}`); }}
          className="text-slate font-bold hover:bg-umber hover:text-surface px-1"
        >
          {String(value || '')}
        </button>
      ),
    },
    { key: 'Title', label: 'Title' },
    { key: 'Author', label: 'Author' },
    { key: 'CopyrightDate', label: 'Year', render: (v: unknown) => v ? String(v).slice(0, 4) : '' },
    { key: 'Pages', label: 'Pages' },
    { key: 'ReadDate', label: 'Last Read' },
  ];

  return (
    <PageLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">Search Books</h1>
          <Link
            to="/books/add"
            className="flex items-center gap-2 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber"
          >
            <Plus size={16} /> Add Book
          </Link>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="bg-surface rounded-lg p-4 shadow flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate mb-1">Author</label>
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="Author%"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate mb-1">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="Title%"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate mb-1">Tag</label>
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="tag-name"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate mb-1">Location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="Location"
            />
          </div>
          <button
            type="submit"
            className="flex items-center gap-2 bg-secondary text-white px-4 py-1.5 rounded-lg text-sm hover:bg-umber h-9"
          >
            <Search size={16} /> Search
          </button>
        </form>

        {/* Tag search note */}
        {tagParam && (
          <p className="text-sm text-slate bg-accent-light px-3 py-2 rounded">
            Showing books tagged: <strong>{tagParam}</strong>
          </p>
        )}

        {/* Results */}
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="text-red-500 text-sm p-4 bg-red-50 rounded-lg">
            <p>Search failed.</p>
            <button onClick={() => refetch()} className="mt-2 text-secondary underline">Retry</button>
          </div>
        ) : (
          <>
            {books.length > 0 && (
              <p className="text-sm text-slate">{books.length} book{books.length !== 1 ? 's' : ''} found.</p>
            )}
            <BookTable
              books={books}
              columns={columns}
              onRowClick={(id) => setSelectedId(selectedId === id ? null : id)}
              selectedId={selectedId}
            />
          </>
        )}

        {/* Detail Panel */}
        {selectedId && (
          <BookDetailPanel bookId={selectedId} onClose={() => setSelectedId(null)} />
        )}
      </div>
    </PageLayout>
  );
}
