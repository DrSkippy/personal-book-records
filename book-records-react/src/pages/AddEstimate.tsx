import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import { useBooksSearch } from '../hooks/useBooksSearch';
import { addEstimate } from '../api/estimates';
import { toObjects } from '../lib/utils';
import { todayApi } from '../lib/dates';
import type { Book } from '../types';

export default function AddEstimate() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const bookId = id ? parseInt(id) : null;

  const { data: bookData } = useBooksSearch(bookId ? { BookId: bookId } : {});
  const books = bookData ? toObjects<Book>(bookData) : [];
  const book = books[0];

  const [startDate, setStartDate] = useState(todayApi());
  const [pages, setPages] = useState(book?.Pages?.toString() || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!bookId) return <PageLayout><p className="text-red-500">Invalid book ID.</p></PageLayout>;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(pages);
    if (!pageNum || pageNum <= 0) {
      setError('Please enter a valid page count.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      await addEstimate(bookId, pageNum, startDate);
      queryClient.invalidateQueries({ queryKey: ['estimates', bookId] });
      navigate(`/estimates/${bookId}`);
    } catch {
      setError('Failed to add estimate. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">Add Reading Estimate</h1>

      {book && (
        <div className="mb-4 p-3 bg-white rounded-lg border border-gray-200">
          <p className="text-secondary font-semibold">{book.Title}</p>
          <p className="text-slate text-sm">{book.Author}</p>
          {book.Pages && <p className="text-slate text-sm">Pages: {book.Pages}</p>}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-surface rounded-md p-8 space-y-4 max-w-md">
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Start Date *</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
            className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Total Readable Pages *</label>
          <input
            type="number"
            value={pages}
            onChange={(e) => setPages(e.target.value)}
            min={1}
            required
            placeholder={book?.Pages?.toString() || 'Enter page count'}
            className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
          {book?.Pages && (
            <p className="text-xs text-slate mt-1">Suggested: {book.Pages} pages</p>
          )}
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber disabled:opacity-50"
          >
            {isSubmitting ? 'Adding...' : 'Start Estimate'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/books/${bookId}`)}
            className="bg-surface border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>
      </form>
    </PageLayout>
  );
}
