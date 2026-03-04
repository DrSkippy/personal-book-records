import { useParams, Link } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import EstimateList from '../components/estimates/EstimateList';
import { useReadingEstimates } from '../hooks/useReadingEstimates';
import { useBooksSearch } from '../hooks/useBooksSearch';
import { toObjects } from '../lib/utils';
import type { Book } from '../types';
import { Plus } from 'lucide-react';

export default function ReadingEstimates() {
  const { id } = useParams<{ id: string }>();
  const bookId = id ? parseInt(id) : null;

  const { data: bookData } = useBooksSearch(bookId ? { BookId: bookId } : {});
  const books = bookData ? toObjects<Book>(bookData) : [];
  const book = books[0];

  const { data: estimatesData, isLoading } = useReadingEstimates(bookId);

  if (!bookId) return <PageLayout><p className="text-red-500">Invalid book ID.</p></PageLayout>;

  const rs = estimatesData?.record_set;
  const sessions = rs
    ? (rs.RecordId as [string, number][]).map(([startDate, recordId], i) => ({
        recordId,
        startDate,
        lastReadablePage: book?.Pages || 0,
        estimatedFinishDate: (rs.Estimate as [string, string, string][])?.[i]?.[0] || null,
        earliestDate: (rs.Estimate as [string, string, string][])?.[i]?.[1] || null,
        latestDate: (rs.Estimate as [string, string, string][])?.[i]?.[2] || null,
      }))
    : [];

  return (
    <PageLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">
            Reading Estimates{book ? `: ${book.Title}` : ''}
          </h1>
          <Link
            to={`/estimates/add/${bookId}`}
            className="flex items-center gap-2 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber"
          >
            <Plus size={16} /> Add Estimate
          </Link>
        </div>

        {book && (
          <div className="p-3 bg-white rounded-lg border border-gray-200 text-sm">
            <p className="text-secondary font-semibold">{book.Title}</p>
            <p className="text-slate">{book.Author}</p>
            {book.Pages && <p className="text-slate">Pages: {book.Pages}</p>}
            <Link to={`/books/${bookId}`} className="text-secondary font-bold hover:bg-umber hover:text-surface px-1 text-xs">
              ← Back to Book
            </Link>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-gray-200 rounded animate-pulse" />)}
          </div>
        ) : (
          <EstimateList sessions={sessions} bookId={bookId} />
        )}
      </div>
    </PageLayout>
  );
}
