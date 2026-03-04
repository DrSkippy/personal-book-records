import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import { useBooksSearch } from '../hooks/useBooksSearch';
import { addReadDates } from '../api/reads';
import { toObjects } from '../lib/utils';
import { todayApi } from '../lib/dates';
import type { Book } from '../types';
import { useQueryClient } from '@tanstack/react-query';

export default function AddReadDate() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const bookId = id ? parseInt(id) : null;

  const { data: bookData } = useBooksSearch(bookId ? { BookId: bookId } : {});
  const books = bookData ? toObjects<Book>(bookData) : [];
  const book = books[0];

  const [readDate, setReadDate] = useState(todayApi());
  const [readNote, setReadNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!bookId) return <PageLayout><p className="text-red-500">Invalid book ID.</p></PageLayout>;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!readDate) return;
    setIsSubmitting(true);
    setError('');
    try {
      await addReadDates([{ BookId: bookId, ReadDate: readDate, ReadNote: readNote || undefined }]);
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
      queryClient.invalidateQueries({ queryKey: ['books-read'] });
      queryClient.invalidateQueries({ queryKey: ['yearly-summary'] });
      navigate(`/books/${bookId}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setError(msg || 'Failed to add read date. It may already exist for this date.');
      setIsSubmitting(false);
    }
  };

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">Add Read Date</h1>

      {book && (
        <div className="mb-4 p-3 bg-white rounded-lg border border-gray-200">
          <p className="text-secondary font-semibold">{book.Title}</p>
          <p className="text-slate text-sm">{book.Author}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-surface rounded-md p-8 space-y-4 max-w-md">
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Date Read *</label>
          <input
            type="date"
            value={readDate}
            onChange={(e) => setReadDate(e.target.value)}
            required
            className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Read Note</label>
          <textarea
            value={readNote}
            onChange={(e) => setReadNote(e.target.value)}
            rows={4}
            placeholder="Optional notes about this reading..."
            className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber disabled:opacity-50"
          >
            {isSubmitting ? 'Adding...' : 'Add Read Date'}
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
