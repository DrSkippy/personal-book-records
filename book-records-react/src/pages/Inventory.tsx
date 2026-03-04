import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import BookDetailPanel from '../components/books/BookDetailPanel';
import { useBooksSearch } from '../hooks/useBooksSearch';
import { updateBookNoteStatus } from '../api/books';
import { toObjects } from '../lib/utils';
import { formatDisplay } from '../lib/dates';
import type { Book } from '../types';

export default function Inventory() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [optimisticRecycled, setOptimisticRecycled] = useState<Record<number, 0 | 1>>({});

  const { data, isLoading, error } = useBooksSearch({ Location: 'Main Collection' });
  const books = data ? toObjects<Book>(data) : [];

  const handleRecycleToggle = async (book: Book) => {
    const current = optimisticRecycled[book.BookId] !== undefined
      ? optimisticRecycled[book.BookId]
      : book.Recycled;
    const newValue: 0 | 1 = current === 1 ? 0 : 1;
    setOptimisticRecycled(prev => ({ ...prev, [book.BookId]: newValue }));
    try {
      await updateBookNoteStatus({ BookId: book.BookId, Recycled: newValue });
      queryClient.invalidateQueries({ queryKey: ['books-search'] });
    } catch {
      // revert on failure
      setOptimisticRecycled(prev => ({ ...prev, [book.BookId]: current }));
    }
  };

  const allBookIds = books.map((b) => b.BookId);

  return (
    <PageLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">
            Inventory — Main Collection
          </h1>
          {allBookIds.length > 0 && (
            <button
              onClick={() => navigate('/read/update', { state: { bookIds: allBookIds } })}
              className="bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber"
            >
              Update Read Notes
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-gray-200 rounded animate-pulse" />)}
          </div>
        ) : error ? (
          <p className="text-red-500">Failed to load inventory.</p>
        ) : books.length === 0 ? (
          <p className="text-slate text-sm p-4 bg-white rounded-lg">No books in Main Collection.</p>
        ) : (
          <div className="w-full border border-gray-300 rounded-xl overflow-hidden shadow-lg">
            <table className="w-full border-separate border-spacing-0">
              <thead>
                <tr className="bg-primary text-white">
                  <th className="px-3 py-3 text-left text-sm font-semibold">ID</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Title</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Author</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Year</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Type</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Last Read</th>
                  <th className="px-3 py-3 text-left text-sm font-semibold">Recycled</th>
                </tr>
              </thead>
              <tbody>
                {books.map((book, i) => {
                  const recycled = optimisticRecycled[book.BookId] !== undefined
                    ? optimisticRecycled[book.BookId]
                    : book.Recycled;
                  return (
                    <tr
                      key={book.BookId}
                      onClick={() => setSelectedId(selectedId === book.BookId ? null : book.BookId)}
                      className={`cursor-pointer transition-colors ${
                        selectedId === book.BookId
                          ? 'bg-primary/20'
                          : i % 2 === 0 ? 'bg-accent-light hover:bg-accent/30' : 'bg-white hover:bg-surface'
                      }`}
                    >
                      <td className="px-3 py-2.5 text-sm">
                        <button
                          onClick={(e) => { e.stopPropagation(); navigate(`/books/${book.BookId}`); }}
                          className="text-slate font-bold hover:bg-umber hover:text-surface px-1"
                        >
                          {book.BookId}
                        </button>
                      </td>
                      <td className="px-3 py-2.5 text-sm">{book.Title}</td>
                      <td className="px-3 py-2.5 text-sm">{book.Author}</td>
                      <td className="px-3 py-2.5 text-sm">{book.CopyrightDate?.slice(0, 4) || ''}</td>
                      <td className="px-3 py-2.5 text-sm">{book.CoverType || ''}</td>
                      <td className="px-3 py-2.5 text-sm">{formatDisplay((book as unknown as Record<string, unknown>)['ReadDate'] as string)}</td>
                      <td className="px-3 py-2.5 text-sm">
                        <input
                          type="checkbox"
                          checked={recycled === 1}
                          onChange={(e) => { e.stopPropagation(); handleRecycleToggle(book); }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-4 h-4 cursor-pointer"
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {selectedId && (
          <BookDetailPanel bookId={selectedId} onClose={() => setSelectedId(null)} />
        )}
      </div>
    </PageLayout>
  );
}
