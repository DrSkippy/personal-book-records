import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import TagBadge from '../components/tags/TagBadge';
import TagEditor from '../components/tags/TagEditor';
import ImageGallery from '../components/images/ImageGallery';
import EstimateList from '../components/estimates/EstimateList';
import { useCompleteRecord } from '../hooks/useCompleteRecord';
import { useReadingEstimates } from '../hooks/useReadingEstimates';
import { toObjects } from '../lib/utils';
import { formatDisplay } from '../lib/dates';
import { getCompleteRecordAdjacent, updateBookNoteStatus, deleteBook } from '../api/books';
import type { Book, ReadRecord } from '../types';
import { ChevronLeft, ChevronRight, Edit, Trash2, Calendar, Plus } from 'lucide-react';
import { DEFAULT_BOOK_IMAGE } from '../lib/constants';

export default function BookDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const bookId = id ? parseInt(id) : null;

  const { data: record, isLoading, error } = useCompleteRecord(bookId);
  const { data: estimatesData } = useReadingEstimates(bookId);

  const [noteText, setNoteText] = useState<string | undefined>(undefined);
  const [savingNote, setSavingNote] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [navigating, setNavigating] = useState(false);

  const handleNav = async (direction: 'next' | 'prev') => {
    if (!bookId || navigating) return;
    setNavigating(true);
    try {
      const adjacent = await getCompleteRecordAdjacent(bookId, direction);
      const books = toObjects<Book>(adjacent.book);
      if (books[0]) navigate(`/books/${books[0].BookId}`);
    } catch {
      // stay on current book
    } finally {
      setNavigating(false);
    }
  };

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
        <div className="p-6 bg-white rounded-xl border border-red-300">
          <p className="text-red-500 mb-2">Book not found or failed to load.</p>
          <Link to="/books" className="text-secondary font-bold hover:bg-umber hover:text-surface px-1">← Back to Search</Link>
        </div>
      </PageLayout>
    );
  }

  const books = toObjects<Book>(record.book);
  const book = books[0];
  if (!book) return <PageLayout><p className="text-red-500">Book data missing.</p></PageLayout>;

  const reads = toObjects<ReadRecord>(record.reads);
  const tags: string[] = record.tags.data[0] ? (record.tags.data[0] as string[]) : [];
  const images = record.img.data[0] ? (record.img.data[0] as string[]) : [];

  const currentNote = noteText !== undefined ? noteText : (book.BookNote || '');

  const estimateSessions = (() => {
    const rs = estimatesData?.record_set;
    if (!rs) return [];
    const recordIds: [string, number][] = rs.RecordId || [];
    const estimates: [string, string, string][] = rs.Estimate || [];
    return recordIds.map(([startDate, recordId], i) => ({
      recordId,
      startDate,
      lastReadablePage: book.Pages || 0,
      estimatedFinishDate: estimates[i]?.[0] || null,
      earliestDate: estimates[i]?.[1] || null,
      latestDate: estimates[i]?.[2] || null,
    }));
  })();

  const imageObjects = images.map((url, i) => ({ ImageId: i, Url: url, Name: null, ImageType: 'cover-face' }));

  const handleSaveNote = async () => {
    setSavingNote(true);
    try {
      await updateBookNoteStatus({ BookId: book.BookId, BookNote: currentNote });
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
    } finally {
      setSavingNote(false);
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
      {/* Nav buttons */}
      <div className="flex justify-between mb-4">
        <button
          onClick={() => handleNav('prev')}
          disabled={navigating}
          className="flex items-center gap-1 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
        >
          <ChevronLeft size={16} /> Prev Book
        </button>
        <button
          onClick={() => handleNav('next')}
          disabled={navigating}
          className="flex items-center gap-1 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
        >
          Next Book <ChevronRight size={16} />
        </button>
      </div>

      {/* Main content */}
      <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
        {/* Cover + Metadata */}
        <div className="flex flex-col md:flex-row gap-6">
          <div className="shrink-0">
            <img
              src={images[0] || DEFAULT_BOOK_IMAGE}
              alt={book.Title}
              className="w-full md:w-auto md:max-w-xs h-auto rounded-lg"
              onError={(e) => { (e.target as HTMLImageElement).src = DEFAULT_BOOK_IMAGE; }}
            />
          </div>
          <div className="flex-1 text-sm space-y-2">
            <h1 className="text-2xl font-bold text-secondary">{book.Title}</h1>
            <p className="text-slate"><span className="font-semibold">Author:</span> {book.Author}</p>
            {book.CopyrightDate && <p className="text-slate"><span className="font-semibold">Year:</span> {book.CopyrightDate.slice(0, 4)}</p>}
            {book.Pages && <p className="text-slate"><span className="font-semibold">Pages:</span> {book.Pages}</p>}
            {book.PublisherName && <p className="text-slate"><span className="font-semibold">Publisher:</span> {book.PublisherName}</p>}
            {book.CoverType && <p className="text-slate"><span className="font-semibold">Cover:</span> {book.CoverType}</p>}
            <p className="text-slate"><span className="font-semibold">Location:</span> {book.Location}</p>
            {book.IsbnNumber && <p className="text-slate"><span className="font-semibold">ISBN-10:</span> {book.IsbnNumber}</p>}
            {book.IsbnNumber13 && <p className="text-slate"><span className="font-semibold">ISBN-13:</span> {book.IsbnNumber13}</p>}
            <p className="text-slate"><span className="font-semibold">Book ID:</span> {book.BookId}</p>
            {book.Recycled === 1 && <span className="inline-block bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded">Recycled</span>}
            <div className="flex gap-2 mt-4">
              <Link
                to={`/books/${book.BookId}/edit`}
                className="flex items-center gap-1 bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber"
              >
                <Edit size={14} /> Edit Book
              </Link>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-1 bg-red-500 text-white px-3 py-2 rounded-lg text-sm hover:bg-red-700"
              >
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        </div>

        {showDeleteConfirm && (
          <div className="p-4 bg-red-50 rounded-lg border border-red-300">
            <p className="text-sm text-red-700 mb-3">Permanently delete "{book.Title}"? All related records will be removed.</p>
            <div className="flex gap-2">
              <button onClick={handleDelete} className="bg-red-500 text-white px-4 py-2 rounded text-sm hover:bg-red-700">Delete</button>
              <button onClick={() => setShowDeleteConfirm(false)} className="bg-gray-200 text-gray-700 px-4 py-2 rounded text-sm hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        )}

        {/* Tags */}
        <div className="border-t border-gray-100 pt-4">
          <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg mb-3">Tags</h2>
          <div className="flex flex-wrap gap-1 mb-3">
            {tags.length ? tags.map((t) => <TagBadge key={t} tag={t} />) : <span className="text-slate text-sm">(no tags)</span>}
          </div>
          <TagEditor bookId={book.BookId} existingTags={tags} />
        </div>

        {/* Read History */}
        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg">Read History</h2>
            <Link
              to={`/read/add/${book.BookId}`}
              className="flex items-center gap-1 bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber"
            >
              <Calendar size={14} /> Add Read Date
            </Link>
          </div>
          {reads.length === 0 ? (
            <p className="text-slate text-sm">Never read.</p>
          ) : (
            <div className="border border-gray-300 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-primary text-white">
                  <tr><th className="px-3 py-2 text-left text-sm">Date</th><th className="px-3 py-2 text-left text-sm">Note</th></tr>
                </thead>
                <tbody>
                  {reads.map((r, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-accent-light' : ''}>
                      <td className="px-3 py-2 text-sm">{formatDisplay(r.DateRead)}</td>
                      <td className="px-3 py-2 text-sm whitespace-pre-line">{r.ReadNote || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Book Note */}
        <div className="border-t border-gray-100 pt-4">
          <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg mb-3">Book Note</h2>
          <textarea
            value={currentNote}
            onChange={(e) => setNoteText(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={handleSaveNote}
            disabled={savingNote}
            className="mt-2 bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
          >
            {savingNote ? 'Saving...' : 'Save Note'}
          </button>
        </div>

        {/* Reading Estimates */}
        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg">Reading Estimates</h2>
            <Link
              to={`/estimates/add/${book.BookId}`}
              className="flex items-center gap-1 bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber"
            >
              <Plus size={14} /> Add Estimate
            </Link>
          </div>
          <EstimateList sessions={estimateSessions} bookId={book.BookId} />
        </div>

        {/* Images */}
        <div className="border-t border-gray-100 pt-4">
          <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-lg mb-3">Images</h2>
          <ImageGallery bookId={book.BookId} images={imageObjects} />
        </div>
      </div>
    </PageLayout>
  );
}
