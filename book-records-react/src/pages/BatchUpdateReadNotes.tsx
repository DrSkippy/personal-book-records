import { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import { useCompleteRecord } from '../hooks/useCompleteRecord';
import { updateEditReadNote } from '../api/reads';
import { updateBookNoteStatus } from '../api/books';
import { toObjects } from '../lib/utils';
import type { Book, ReadRecord } from '../types';
import { ChevronLeft, ChevronRight, Save } from 'lucide-react';

export default function BatchUpdateReadNotes() {
  const location = useLocation();
  const queryClient = useQueryClient();

  const bookIds: number[] = location.state?.bookIds || [];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [bookNotes, setBookNotes] = useState<Record<number, string>>({});
  const [readNotes, setReadNotes] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  const currentId = bookIds[currentIndex] || null;
  const { data: record, isLoading } = useCompleteRecord(currentId);

  useEffect(() => {
    if (record && currentId) {
      const books = toObjects<Book>(record.book);
      const book = books[0];
      if (book && bookNotes[currentId] === undefined) {
        setBookNotes(prev => ({ ...prev, [currentId]: book.BookNote || '' }));
      }
      const reads = toObjects<ReadRecord>(record.reads);
      const latestRead = reads[reads.length - 1];
      if (latestRead && readNotes[currentId] === undefined) {
        setReadNotes(prev => ({ ...prev, [currentId]: latestRead.ReadNote || '' }));
      }
    }
  }, [record, currentId]);

  if (bookIds.length === 0) {
    return (
      <PageLayout>
        <div className="p-6 bg-white rounded-xl">
          <p className="text-slate mb-4">No books to update.</p>
          <Link to="/" className="text-secondary font-bold hover:bg-umber hover:text-surface px-1">← Go to Dashboard</Link>
        </div>
      </PageLayout>
    );
  }

  const books = record ? toObjects<Book>(record.book) : [];
  const book = books[0];
  const reads = record ? toObjects<ReadRecord>(record.reads) : [];
  const latestRead = reads[reads.length - 1];

  const currentBookNote = bookNotes[currentId!] ?? '';
  const currentReadNote = readNotes[currentId!] ?? '';

  const handleSave = async () => {
    if (!currentId || !book) return;
    setSaving(true);
    setSaveStatus('');
    try {
      const promises: Promise<unknown>[] = [
        updateBookNoteStatus({ BookId: currentId, BookNote: currentBookNote }),
      ];
      if (latestRead) {
        promises.push(updateEditReadNote({
          BookId: currentId,
          ReadDate: latestRead.DateRead,
          ReadNote: currentReadNote,
        }));
      }
      await Promise.all(promises);
      queryClient.invalidateQueries({ queryKey: ['complete-record', currentId] });
      setSaveStatus('Saved!');
      setTimeout(() => setSaveStatus(''), 2000);
    } catch {
      setSaveStatus('Save failed.');
    } finally {
      setSaving(false);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleNext = () => {
    if (currentIndex < bookIds.length - 1) setCurrentIndex(currentIndex + 1);
  };

  return (
    <PageLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">
            Update Read Notes ({currentIndex + 1} of {bookIds.length})
          </h1>
          <div className="flex gap-2">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="flex items-center gap-1 bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1 bg-primary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
            >
              <Save size={16} /> {saving ? 'Saving...' : 'Update Record'}
            </button>
            <button
              onClick={handleNext}
              disabled={currentIndex >= bookIds.length - 1}
              className="flex items-center gap-1 bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {saveStatus && (
          <div className={`px-4 py-2 rounded text-sm ${saveStatus === 'Saved!' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {saveStatus}
          </div>
        )}

        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/2" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
        ) : book ? (
          <div className="bg-white rounded-xl shadow p-6">
            <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
              <div>
                <p className="text-slate"><span className="font-semibold">Book ID:</span> {book.BookId}</p>
                <p className="text-slate"><span className="font-semibold">Title:</span> {book.Title}</p>
                <p className="text-slate"><span className="font-semibold">Author:</span> {book.Author}</p>
              </div>
              <div>
                {latestRead && (
                  <>
                    <p className="text-slate"><span className="font-semibold">Read Date:</span> {latestRead.DateRead}</p>
                  </>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-umber mb-2">Book Note</label>
                <textarea
                  value={currentBookNote}
                  onChange={(e) => setBookNotes(prev => ({ ...prev, [currentId!]: e.target.value }))}
                  rows={8}
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Notes about the book..."
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-umber mb-2">Read Note</label>
                <textarea
                  value={currentReadNote}
                  onChange={(e) => setReadNotes(prev => ({ ...prev, [currentId!]: e.target.value }))}
                  rows={8}
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Notes about this particular reading..."
                />
              </div>
            </div>
          </div>
        ) : null}

        {/* Progress dots */}
        <div className="flex gap-1 justify-center flex-wrap">
          {bookIds.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`w-3 h-3 rounded-full transition-colors ${
                i === currentIndex ? 'bg-primary' : 'bg-gray-300 hover:bg-slate'
              }`}
            />
          ))}
        </div>
      </div>
    </PageLayout>
  );
}
