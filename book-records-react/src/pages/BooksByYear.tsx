import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import BookDetailPanel from '../components/books/BookDetailPanel';
import { useBooksReadByYear } from '../hooks/useBooksReadByYear';
import { useYearlySummary } from '../hooks/useYearlySummary';
import { toObjects } from '../lib/utils';
import { formatDisplay } from '../lib/dates';
import type { Book, YearlySummary } from '../types';
import { ChevronUp, ChevronDown } from 'lucide-react';

export default function BooksByYear() {
  const { year } = useParams<{ year: string }>();
  const navigate = useNavigate();
  const targetYear = year && year !== 'all' ? parseInt(year) : undefined;
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [sortKey, setSortKey] = useState<string>('ReadDate');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const { data: booksData, isLoading: booksLoading } = useBooksReadByYear(targetYear);
  const { data: summaryData } = useYearlySummary(targetYear);

  const books = booksData ? toObjects<Book & { ReadDate: string }>(booksData) : [];
  const summary = summaryData ? toObjects<YearlySummary>(summaryData) : [];
  const yearSummary = summary[0];
  const summaryByYear = Object.fromEntries(summary.map(s => [s.year, s]));

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  type BookWithRead = Book & { ReadDate: string };
  const sorted = [...books].sort((a: BookWithRead, b: BookWithRead) => {
    const av = (a as unknown as Record<string, unknown>)[sortKey] ?? '';
    const bv = (b as unknown as Record<string, unknown>)[sortKey] ?? '';
    const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const allBookIds = books.map((b) => b.BookId);

  const columns = [
    { key: 'BookId', label: 'ID' },
    { key: 'Title', label: 'Title' },
    { key: 'Author', label: 'Author' },
    { key: 'Pages', label: 'Pages' },
    { key: 'ReadDate', label: 'Read Date' },
    { key: 'Location', label: 'Location' },
    { key: 'carousel', label: 'C' },
  ];

  return (
    <PageLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">
            Books Read: {year || 'All Years'}
          </h1>
          {allBookIds.length > 0 && (
            <button
              onClick={() => navigate('/read/update', { state: { bookIds: allBookIds } })}
              className="bg-secondary text-white px-4 py-2 rounded-lg text-sm hover:bg-umber"
            >
              Update Read Notes
            </button>
          )}
        </div>

        {/* Year summary card — only for specific-year view */}
        {targetYear && yearSummary && (
          <div className="bg-white rounded-lg p-4 border border-gray-200 text-sm font-bold text-secondary border-t-4 border-t-slate">
            Year: {yearSummary.year} &nbsp;|&nbsp; Pages: {(yearSummary['pages read'] || 0).toLocaleString()} &nbsp;|&nbsp; ({yearSummary['books read'] || 0} books)
          </div>
        )}

        {booksLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-gray-200 rounded animate-pulse" />)}
          </div>
        ) : books.length === 0 ? (
          <p className="text-slate text-sm p-4 bg-white rounded-lg">No books recorded for this year.</p>
        ) : (
          <div className="w-full border border-gray-300 rounded-xl overflow-hidden shadow-lg">
            <table className="w-full border-separate border-spacing-0">
              <thead>
                <tr className="bg-primary text-white">
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      onClick={() => col.key !== 'carousel' && handleSort(col.key)}
                      className="px-3 py-3 text-left text-sm font-semibold cursor-pointer select-none whitespace-nowrap"
                    >
                      <span className="flex items-center gap-1">
                        {col.label}
                        {sortKey === col.key && (sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const renderBookRow = (book: typeof sorted[0], i: number) => (
                    <tr
                      key={`${book.BookId}-${i}`}
                      onClick={() => setSelectedId(selectedId === book.BookId ? null : book.BookId)}
                      className={`cursor-pointer transition-colors ${
                        selectedId === book.BookId
                          ? 'bg-primary/20'
                          : i % 2 === 0 ? 'bg-accent-light hover:bg-accent/30' : 'bg-white hover:bg-surface'
                      }`}
                    >
                      <td className="px-3 py-2.5 text-sm">
                        <button
                          onClick={(e) => { e.stopPropagation(); navigate(`/books/${book.BookId}`); }}
                          className="text-slate font-bold hover:bg-umber hover:text-surface px-1"
                        >
                          {book.BookId}
                        </button>
                      </td>
                      <td className="px-3 py-2.5 text-sm">{book.Title}</td>
                      <td className="px-3 py-2.5 text-sm">{book.Author}</td>
                      <td className="px-3 py-2.5 text-sm">{book.Pages || ''}</td>
                      <td className="px-3 py-2.5 text-sm">{formatDisplay(book.ReadDate)}</td>
                      <td className="px-3 py-2.5 text-sm">{book.Location}</td>
                      <td className="px-3 py-2.5 text-sm">
                        <Link
                          to={`/carousel/${book.BookId}`}
                          onClick={(e) => e.stopPropagation()}
                          className="text-secondary font-bold hover:bg-umber hover:text-surface px-1"
                        >
                          C
                        </Link>
                      </td>
                    </tr>
                  );

                  if (targetYear) {
                    return sorted.map((book, i) => renderBookRow(book, i));
                  }

                  // All-years view: group by year and inject a summary row per year
                  const groups: { year: number; books: typeof sorted }[] = [];
                  for (const book of sorted) {
                    const y = book.ReadDate ? parseInt(book.ReadDate.slice(0, 4)) : 0;
                    const last = groups[groups.length - 1];
                    if (!last || last.year !== y) groups.push({ year: y, books: [book] });
                    else last.books.push(book);
                  }

                  return groups.flatMap(({ year: y, books: yBooks }) => [
                    <tr key={`yr-${y}`} className="bg-umber text-white">
                      <td colSpan={columns.length} className="px-3 py-2 text-sm font-semibold">
                        Year: {y} &nbsp;|&nbsp; Pages: {(summaryByYear[y]?.['pages read'] ?? 0).toLocaleString()} &nbsp;|&nbsp; ({summaryByYear[y]?.['books read'] ?? 0} books)
                      </td>
                    </tr>,
                    ...yBooks.map((book, i) => renderBookRow(book, i)),
                  ]);
                })()}
              </tbody>
            </table>
          </div>
        )}

        {selectedId && (
          <BookDetailPanel bookId={selectedId} onClose={() => setSelectedId(null)} />
        )}
      </div>
    </PageLayout>
  );
}
