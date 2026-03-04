import { useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useCompleteRecord } from '../../hooks/useCompleteRecord';
import { useReadingEstimates } from '../../hooks/useReadingEstimates';
import TagBadge from '../tags/TagBadge';
import TagEditor from '../tags/TagEditor';
import ImageGallery from '../images/ImageGallery';
import EstimateList from '../estimates/EstimateList';
import { toObjects } from '../../lib/utils';
import { formatDisplay } from '../../lib/dates';
import { updateBookNoteStatus, deleteBook } from '../../api/books';
import type { Book, ReadRecord } from '../../types';
import { Edit, Trash2, Plus, Calendar } from 'lucide-react';
import { useState } from 'react';

interface BookDetailPanelProps {
  bookId: number;
  onClose?: () => void;
}

export default function BookDetailPanel({ bookId, onClose }: BookDetailPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: record, isLoading, error } = useCompleteRecord(bookId);
  const { data: estimatesData } = useReadingEstimates(bookId);
  const [noteText, setNoteText] = useState<string | undefined>(undefined);
  const [savingNote, setSavingNote] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (panelRef.current) {
      panelRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [bookId]);

  if (isLoading) {
    return (
      <div ref={panelRef} className="mt-4 p-6 bg-white rounded-xl border border-gray-300 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
      </div>
    );
  }

  if (error || !record) {
    return (
      <div ref={panelRef} className="mt-4 p-6 bg-white rounded-xl border border-red-300">
        <p className="text-red-500">Failed to load book details.</p>
      </div>
    );
  }

  const books = toObjects<Book>(record.book);
  const book = books[0];
  if (!book) return null;

  const reads = toObjects<ReadRecord>(record.reads);
  const tags: string[] = record.tags.data[0] ? (record.tags.data[0] as string[]) : [];
  const images = record.img.data[0] ? (record.img.data[0] as string[]) : [];

  const currentNote = noteText !== undefined ? noteText : (book.BookNote || '');

  // Parse estimates
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

  // Build image objects
  const imageObjects = images.map((url, i) => ({
    ImageId: i,
    Url: url,
    Name: null,
    ImageType: 'cover-face',
  }));

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
    <div ref={panelRef} className="mt-4 bg-white rounded-xl border border-gray-300 shadow-lg p-6">
      {onClose && (
        <button onClick={onClose} className="mb-4 text-slate text-sm hover:text-secondary">✕ Close</button>
      )}

      {/* Metadata */}
      <div className="flex gap-6 mb-6">
        <div className="shrink-0">
          {images[0] ? (
            <img src={images[0]} alt={book.Title} className="w-36 h-auto rounded-lg" onError={(e) => { (e.target as HTMLImageElement).src = `${import.meta.env.VITE_RESOURCE_BASE_URL}/default.webp`; }} />
          ) : (
            <div className="w-36 bg-surface rounded-lg flex items-center justify-center text-slate text-xs py-8">No image</div>
          )}
        </div>
        <div className="flex-1 text-sm space-y-1">
          <h2 className="text-xl font-bold text-secondary">{book.Title}</h2>
          <p className="text-slate"><span className="font-medium">Author:</span> {book.Author}</p>
          {book.CopyrightDate && <p className="text-slate"><span className="font-medium">Year:</span> {book.CopyrightDate.slice(0, 4)}</p>}
          {book.Pages && <p className="text-slate"><span className="font-medium">Pages:</span> {book.Pages}</p>}
          {book.PublisherName && <p className="text-slate"><span className="font-medium">Publisher:</span> {book.PublisherName}</p>}
          {book.CoverType && <p className="text-slate"><span className="font-medium">Cover:</span> {book.CoverType}</p>}
          <p className="text-slate"><span className="font-medium">Location:</span> {book.Location}</p>
          {book.IsbnNumber && <p className="text-slate"><span className="font-medium">ISBN:</span> {book.IsbnNumber}</p>}
          <div className="flex gap-2 mt-3">
            <Link to={`/books/${book.BookId}/edit`} className="flex items-center gap-1 bg-secondary text-white px-3 py-1 rounded text-xs hover:bg-umber">
              <Edit size={12} /> Edit
            </Link>
            <button onClick={() => setShowDeleteConfirm(true)} className="flex items-center gap-1 bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-700">
              <Trash2 size={12} /> Delete
            </button>
          </div>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="mb-4 p-4 bg-red-50 rounded-lg border border-red-300">
          <p className="text-sm text-red-700 mb-3">Delete "{book.Title}"? This cannot be undone.</p>
          <div className="flex gap-2">
            <button onClick={handleDelete} className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-700">Delete</button>
            <button onClick={() => setShowDeleteConfirm(false)} className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300">Cancel</button>
          </div>
        </div>
      )}

      {/* Tags */}
      <div className="mb-4 border-t border-gray-100 pt-4">
        <h3 className="text-sm font-semibold text-umber mb-2">Tags</h3>
        <div className="flex flex-wrap gap-1 mb-2">
          {tags.length ? tags.map((t) => <TagBadge key={t} tag={t} />) : <span className="text-slate text-xs">(no tags)</span>}
        </div>
        <TagEditor bookId={book.BookId} existingTags={tags} />
      </div>

      {/* Read History */}
      <div className="mb-4 border-t border-gray-100 pt-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-umber">Read History</h3>
          <Link to={`/read/add/${book.BookId}`} className="flex items-center gap-1 text-secondary text-xs font-bold hover:bg-umber hover:text-surface px-1">
            <Calendar size={12} /> Add Read Date
          </Link>
        </div>
        {reads.length === 0 ? (
          <p className="text-slate text-sm">Never read.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="bg-primary text-white"><th className="px-3 py-2 text-left">Date</th><th className="px-3 py-2 text-left">Note</th></tr></thead>
            <tbody>
              {reads.map((r, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-accent-light' : ''}>
                  <td className="px-3 py-2">{formatDisplay(r.DateRead)}</td>
                  <td className="px-3 py-2">{r.ReadNote || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Book Note */}
      <div className="mb-4 border-t border-gray-100 pt-4">
        <h3 className="text-sm font-semibold text-umber mb-2">Book Note</h3>
        <textarea
          value={currentNote}
          onChange={(e) => setNoteText(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button
          onClick={handleSaveNote}
          disabled={savingNote}
          className="mt-2 bg-secondary text-white px-3 py-1 rounded text-sm hover:bg-umber disabled:opacity-50"
        >
          {savingNote ? 'Saving...' : 'Save Note'}
        </button>
      </div>

      {/* Estimates */}
      <div className="mb-4 border-t border-gray-100 pt-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-umber">Reading Estimates</h3>
          <Link to={`/estimates/add/${book.BookId}`} className="flex items-center gap-1 text-secondary text-xs font-bold hover:bg-umber hover:text-surface px-1">
            <Plus size={12} /> Add Estimate
          </Link>
        </div>
        <EstimateList sessions={estimateSessions} bookId={book.BookId} />
      </div>

      {/* Images */}
      <div className="border-t border-gray-100 pt-4">
        <h3 className="text-sm font-semibold text-umber mb-2">Images</h3>
        <ImageGallery bookId={book.BookId} images={imageObjects} />
      </div>
    </div>
  );
}
