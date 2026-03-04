import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import BookForm from '../components/books/BookForm';
import { useCompleteRecord } from '../hooks/useCompleteRecord';
import { updateBook, deleteBook } from '../api/books';
import { toObjects } from '../lib/utils';
import type { Book } from '../types';
import type { BookFormValues } from '../lib/validation';
import { Trash2 } from 'lucide-react';

export default function EditBook() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const bookId = id ? parseInt(id) : null;

  const { data: record, isLoading, error } = useCompleteRecord(bookId);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (!bookId) return <PageLayout><p className="text-red-500">Invalid book ID.</p></PageLayout>;

  if (isLoading) {
    return (
      <PageLayout>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </PageLayout>
    );
  }

  if (error || !record) {
    return (
      <PageLayout>
        <p className="text-red-500">Failed to load book.</p>
      </PageLayout>
    );
  }

  const books = toObjects<Book>(record.book);
  const book = books[0];
  if (!book) return <PageLayout><p className="text-red-500">Book data not found.</p></PageLayout>;

  const defaultValues: Partial<BookFormValues> = {
    Title: book.Title,
    Author: book.Author,
    CopyrightDate: book.CopyrightDate?.slice(0, 10) || '',
    IsbnNumber: book.IsbnNumber || '',
    IsbnNumber13: book.IsbnNumber13 || '',
    PublisherName: book.PublisherName || '',
    CoverType: book.CoverType || undefined,
    Pages: book.Pages || undefined,
    BookNote: book.BookNote || '',
    Recycled: book.Recycled || 0,
    Location: book.Location,
  };

  const handleSubmit = async (values: BookFormValues) => {
    setIsSubmitting(true);
    try {
      await updateBook({ ...values, BookId: book.BookId });
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
      queryClient.invalidateQueries({ queryKey: ['books-search'] });
      queryClient.invalidateQueries({ queryKey: ['recent'] });
      navigate(`/books/${bookId}`);
    } catch {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    await deleteBook(book.BookId);
    queryClient.invalidateQueries({ queryKey: ['books-search'] });
    queryClient.invalidateQueries({ queryKey: ['recent'] });
    navigate('/books');
  };

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">
        Edit Book: {book.Title}
      </h1>

      <BookForm
        defaultValues={defaultValues}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        submitLabel="Save Changes"
        onCancel={() => navigate(`/books/${bookId}`)}
      />

      <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-sm font-semibold text-red-700 mb-2">Danger Zone</h3>
        {showDeleteConfirm ? (
          <div>
            <p className="text-sm text-red-600 mb-3">Permanently delete "{book.Title}"? This cannot be undone.</p>
            <div className="flex gap-2">
              <button onClick={handleDelete} className="bg-red-500 text-white px-4 py-2 rounded text-sm hover:bg-red-700">
                Confirm Delete
              </button>
              <button onClick={() => setShowDeleteConfirm(false)} className="bg-gray-200 text-gray-700 px-4 py-2 rounded text-sm">
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700"
          >
            <Trash2 size={14} /> Delete Book
          </button>
        )}
      </div>
    </PageLayout>
  );
}
