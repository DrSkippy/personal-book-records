import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import BookForm from '../components/books/BookForm';
import { addBooks, lookupByIsbn } from '../api/books';
import type { BookFormValues } from '../lib/validation';
import { Search } from 'lucide-react';

export default function AddBook() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isbnInput, setIsbnInput] = useState(searchParams.get('isbn') || '');
  const [prefilled, setPrefilled] = useState<Partial<BookFormValues> | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    const isbn = searchParams.get('isbn');
    if (isbn) {
      handleIsbnLookup(isbn);
    }
  }, []);

  const handleIsbnLookup = async (isbn: string) => {
    if (!isbn) return;
    setLookupLoading(true);
    setLookupError('');
    try {
      const result = await lookupByIsbn([isbn]);
      const book = result.book_records?.[0];
      if (book) {
        setPrefilled({
          Title: book.Title || '',
          Author: book.Author || '',
          CopyrightDate: book.CopyrightDate || '',
          IsbnNumber: book.IsbnNumber || '',
          IsbnNumber13: book.IsbnNumber13 || '',
          PublisherName: book.PublisherName || '',
          Pages: book.Pages || undefined,
          CoverType: book.CoverType || undefined,
          Location: 'Main Collection',
        });
      } else {
        setLookupError('No book found for this ISBN.');
      }
    } catch {
      setLookupError('Failed to look up ISBN. Please try again.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleSubmit = async (values: BookFormValues) => {
    setIsSubmitting(true);
    setSubmitError('');
    try {
      const result = await addBooks([values]);
      const newBook = result.add_books?.[0];
      if (newBook?.BookId) {
        navigate(`/books/${newBook.BookId}`);
      } else {
        navigate('/books');
      }
    } catch {
      setSubmitError('Failed to add book. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">Add Book</h1>

      {/* ISBN Lookup */}
      <div className="bg-surface rounded-lg p-4 shadow mb-6">
        <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg mb-4">ISBN Lookup</h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={isbnInput}
            onChange={(e) => setIsbnInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleIsbnLookup(isbnInput)}
            placeholder="Enter ISBN-10 or ISBN-13"
            className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
          <button
            onClick={() => handleIsbnLookup(isbnInput)}
            disabled={lookupLoading || !isbnInput}
            className="flex items-center gap-2 bg-secondary text-white px-4 py-1.5 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
          >
            <Search size={16} />
            {lookupLoading ? 'Looking up...' : 'Look Up'}
          </button>
        </div>
        {lookupError && <p className="text-red-500 text-sm mt-2">{lookupError}</p>}
        {prefilled && (
          <p className="text-green-600 text-sm mt-2">✓ Book metadata found. Form pre-populated below.</p>
        )}
      </div>

      {submitError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-300 rounded text-red-600 text-sm">{submitError}</div>
      )}

      <BookForm
        defaultValues={prefilled || undefined}
        key={JSON.stringify(prefilled)}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        submitLabel="Add Book"
        onCancel={() => navigate(-1)}
      />
    </PageLayout>
  );
}
