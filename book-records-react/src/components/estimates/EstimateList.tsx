import { useState } from 'react';
import { ChevronDown, ChevronRight, Plus } from 'lucide-react';
import { useDailyPageRecords } from '../../hooks/useDailyPageRecords';
import { formatDisplay } from '../../lib/dates';
import { Link } from 'react-router-dom';

interface EstimateSession {
  recordId: number;
  startDate: string;
  lastReadablePage: number;
  estimatedFinishDate: string | null;
  earliestDate: string | null;
  latestDate: string | null;
}

interface DailyRecordsProps {
  recordId: number;
}

function DailyRecords({ recordId }: DailyRecordsProps) {
  const { data, isLoading } = useDailyPageRecords(recordId);

  if (isLoading) return <p className="text-sm text-slate">Loading...</p>;

  const records: [string, number, number][] = data?.date_page_records || [];

  if (!records.length) return <p className="text-sm text-slate">No daily progress logged.</p>;

  return (
    <table className="w-full text-sm mt-2">
      <thead>
        <tr className="bg-primary text-white">
          <th className="px-3 py-2 text-left">Date</th>
          <th className="px-3 py-2 text-left">Page</th>
          <th className="px-3 py-2 text-left">Day #</th>
        </tr>
      </thead>
      <tbody>
        {records.map(([date, page, dayNum], i) => (
          <tr key={i} className={i % 2 === 0 ? 'bg-accent-light' : ''}>
            <td className="px-3 py-2">{formatDisplay(date)}</td>
            <td className="px-3 py-2">{page}</td>
            <td className="px-3 py-2">{dayNum}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface EstimateListProps {
  sessions: EstimateSession[];
  bookId: number;
}

export default function EstimateList({ sessions, bookId }: EstimateListProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (id: number) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (!sessions.length) {
    return (
      <div className="text-slate text-sm py-4">
        No estimates yet.{' '}
        <Link to={`/estimates/add/${bookId}`} className="text-secondary font-bold hover:bg-umber hover:text-surface px-1">
          Add Estimate
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sessions.map((session) => (
        <div key={session.recordId} className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="grid grid-cols-2 gap-2 text-sm mb-3">
            <div><span className="font-medium">Start:</span> {formatDisplay(session.startDate)}</div>
            <div><span className="font-medium">Record ID:</span> {session.recordId}</div>
            <div><span className="font-medium">Total Pages:</span> {session.lastReadablePage}</div>
            {session.estimatedFinishDate && (
              <div><span className="font-medium">Est. Finish:</span> {formatDisplay(session.estimatedFinishDate)}</div>
            )}
            {session.earliestDate && (
              <div><span className="font-medium">Earliest:</span> {formatDisplay(session.earliestDate)}</div>
            )}
            {session.latestDate && (
              <div><span className="font-medium">Latest:</span> {formatDisplay(session.latestDate)}</div>
            )}
          </div>
          <Link
            to={`/estimates/${session.recordId}/progress`}
            className="flex items-center gap-1 text-secondary text-sm font-bold hover:bg-umber hover:text-surface px-1 mb-3 w-fit"
          >
            <Plus size={14} /> Add pages for Record {session.recordId}
          </Link>
          <button
            onClick={() => toggle(session.recordId)}
            className="flex items-center gap-1 text-sm text-slate hover:text-secondary"
          >
            {expanded.has(session.recordId) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            Daily Records
          </button>
          {expanded.has(session.recordId) && (
            <DailyRecords recordId={session.recordId} />
          )}
        </div>
      ))}
    </div>
  );
}
