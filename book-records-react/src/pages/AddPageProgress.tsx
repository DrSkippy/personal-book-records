import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PageLayout from '../components/layout/PageLayout';
import { useDailyPageRecords } from '../hooks/useDailyPageRecords';
import { addDailyPage } from '../api/estimates';
import { todayApi, formatDisplay } from '../lib/dates';

export default function AddPageProgress() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const recordId = id ? parseInt(id) : null;

  const { data, isLoading, refetch } = useDailyPageRecords(recordId);

  const [recordDate, setRecordDate] = useState(todayApi());
  const [page, setPage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!recordId) return <PageLayout><p className="text-red-500">Invalid record ID.</p></PageLayout>;

  const records: [string, number, number][] = data?.date_page_records || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(page);
    if (!pageNum || pageNum <= 0) {
      setError('Please enter a valid page number.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      await addDailyPage({ RecordId: recordId, RecordDate: recordDate, Page: pageNum });
      queryClient.invalidateQueries({ queryKey: ['daily-pages', recordId] });
      setPage('');
      setRecordDate(todayApi());
      refetch();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setError(msg || 'Failed to add progress. Date may already exist.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">
        Add Reading Progress (Record #{recordId})
      </h1>

      {/* Existing records */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg">Existing Progress</h2>
        <div className="bg-white rounded-b-lg shadow">
          {isLoading ? (
            <p className="p-4 text-slate text-sm">Loading...</p>
          ) : records.length === 0 ? (
            <p className="p-4 text-slate text-sm">No progress logged yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-primary text-white">
                  <tr>
                    <th className="px-3 py-2 text-left text-sm">Date</th>
                    <th className="px-3 py-2 text-left text-sm">Page</th>
                    <th className="px-3 py-2 text-left text-sm">Day #</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map(([date, pageProg, dayNum], i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-accent-light' : ''}>
                      <td className="px-3 py-2 text-sm">{formatDisplay(date)}</td>
                      <td className="px-3 py-2 text-sm">{pageProg}</td>
                      <td className="px-3 py-2 text-sm">{dayNum}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* New entry form */}
      <form onSubmit={handleSubmit} className="bg-surface rounded-md p-8 space-y-4 max-w-md">
        <h2 className="text-xl font-semibold text-umber">New Entry</h2>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Date *</label>
          <input
            type="date"
            value={recordDate}
            onChange={(e) => setRecordDate(e.target.value)}
            required
            className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Current Page *</label>
          <input
            type="number"
            value={page}
            onChange={(e) => setPage(e.target.value)}
            min={1}
            required
            placeholder="Cumulative page reached"
            className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
          />
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber disabled:opacity-50"
          >
            {isSubmitting ? 'Adding...' : 'Add Progress'}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="bg-surface border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>
      </form>
    </PageLayout>
  );
}
