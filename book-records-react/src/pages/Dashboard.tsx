import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import TwoColumnLayout from '../components/layout/TwoColumnLayout';
import BookTable from '../components/books/BookTable';
import { useRecentBooks } from '../hooks/useRecentBooks';
import { useYearlySummary } from '../hooks/useYearlySummary';
import { toObjects } from '../lib/utils';
import type { Book, YearlySummary } from '../types';
import { Search, Plus } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: recentData, isLoading: recentLoading, error: recentError, refetch: refetchRecent } = useRecentBooks(20);
  const { data: summaryData, isLoading: summaryLoading, error: summaryError, refetch: refetchSummary } = useYearlySummary();

  const [author, setAuthor] = useState('');
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [isbn, setIsbn] = useState('');

  const recentBooks = recentData ? toObjects<Book>(recentData) : [];
  const yearlySummary = summaryData ? toObjects<YearlySummary>(summaryData) : [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (author) params.set('author', author);
    if (title) params.set('title', title);
    if (tags) params.set('tags', tags);
    navigate(`/books?${params.toString()}`);
  };

  const handleIsbnSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isbn) navigate(`/books/add?isbn=${encodeURIComponent(isbn)}`);
  };

  const recentColumns = [
    {
      key: 'Title',
      label: 'Title',
      render: (value: unknown, row: Record<string, unknown>) => (
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/books/${row['BookId']}`); }}
          className="text-slate font-bold hover:bg-umber hover:text-surface px-1 text-left"
        >
          {String(value || '')}
        </button>
      ),
    },
    { key: 'LastUpdate', label: 'Last Update' },
  ];

  const leftContent = (
    <div className="space-y-6">
      {/* Recently Updated */}
      <div>
        <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg">Recently Updated</h2>
        <div className="bg-white rounded-b-lg shadow p-4">
          {recentLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-8 bg-gray-200 rounded animate-pulse" />
              ))}
            </div>
          ) : recentError ? (
            <div className="text-red-500 text-sm">
              <p>Failed to load recent books.</p>
              <button onClick={() => refetchRecent()} className="mt-2 text-secondary underline text-sm">Retry</button>
            </div>
          ) : recentBooks.length === 0 ? (
            <p className="text-slate text-sm">No recent books.</p>
          ) : (
            <BookTable
              books={recentBooks}
              columns={recentColumns}
              onRowClick={(id) => navigate(`/books/${id}`)}
            />
          )}
        </div>
      </div>

      {/* Search Form */}
      <div>
        <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg flex items-center gap-2">
          <Search size={18} /> Search Books
        </h2>
        <form onSubmit={handleSearch} className="bg-surface rounded-b-lg shadow p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate mb-1">Author</label>
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="e.g. Tolkien%"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate mb-1">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="e.g. Hobbit%"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate mb-1">Tag</label>
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="e.g. fantasy"
            />
          </div>
          <button type="submit" className="w-full bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber">
            Search
          </button>
        </form>
      </div>

      {/* Add Book by ISBN */}
      <div>
        <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg flex items-center gap-2">
          <Plus size={18} /> Add Book by ISBN
        </h2>
        <form onSubmit={handleIsbnSubmit} className="bg-surface rounded-b-lg shadow p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate mb-1">ISBN</label>
            <input
              value={isbn}
              onChange={(e) => setIsbn(e.target.value)}
              className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              placeholder="ISBN-10 or ISBN-13"
            />
          </div>
          <button type="submit" className="w-full bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber">
            Look Up & Add
          </button>
        </form>
      </div>
    </div>
  );

  const rightContent = (
    <div>
      <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg">Yearly Reading Reports</h2>
      <div className="bg-white rounded-b-lg shadow p-4">
        {summaryLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        ) : summaryError ? (
          <div className="text-red-500 text-sm">
            <p>Failed to load yearly summary.</p>
            <button onClick={() => refetchSummary()} className="mt-2 text-secondary underline text-sm">Retry</button>
          </div>
        ) : yearlySummary.length === 0 ? (
          <p className="text-slate text-sm">No reading history found.</p>
        ) : (
          <div className="w-full border border-gray-300 rounded-xl overflow-hidden shadow">
            <table className="w-full border-separate border-spacing-0">
              <thead>
                <tr className="bg-primary text-white">
                  <th className="px-3 py-3 text-left text-sm font-semibold">Year</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Pages</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Books</th>
                </tr>
              </thead>
              <tbody>
                {[...yearlySummary].sort((a, b) => b.year - a.year).map((row, i) => (
                  <tr key={row.year} className={i % 2 === 0 ? 'bg-accent-light' : 'bg-white'}>
                    <td className="px-3 py-2.5 text-sm">
                      <button
                        onClick={() => navigate(`/year/${row.year}`)}
                        className="text-slate font-bold hover:bg-umber hover:text-surface px-1"
                      >
                        {row.year}
                      </button>
                    </td>
                    <td className="px-3 py-2.5 text-sm">{(row['pages read'] || 0).toLocaleString()}</td>
                    <td className="px-3 py-2.5 text-sm">{row['books read'] || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">Book Collection</h1>
      <TwoColumnLayout left={leftContent} right={rightContent} />
    </PageLayout>
  );
}
