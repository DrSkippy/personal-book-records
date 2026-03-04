import PageLayout from '../components/layout/PageLayout';
import YearProgressChart from '../components/charts/YearProgressChart';
import AllYearsChart from '../components/charts/AllYearsChart';
import { useYearlySummary } from '../hooks/useYearlySummary';
import { toObjects } from '../lib/utils';
import type { Book, YearlySummary } from '../types';
import { useQueries } from '@tanstack/react-query';
import { getBooksRead } from '../api/reads';

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 15 }, (_, i) => CURRENT_YEAR - i);

export default function Progress() {
  const { data: summaryData, isLoading: summaryLoading } = useYearlySummary();
  const yearlySummary = summaryData ? toObjects<YearlySummary>(summaryData) : [];

  // Fetch books for last 15 years in parallel
  const yearQueries = useQueries({
    queries: YEARS.map((year) => ({
      queryKey: ['books-read', year],
      queryFn: () => getBooksRead(year),
      staleTime: 5 * 60 * 1000,
    })),
  });

  const yearBooks: Record<number, Book[]> = {};
  YEARS.forEach((year, i) => {
    const data = yearQueries[i].data;
    if (data) {
      yearBooks[year] = toObjects<Book>(data);
    }
  });

  const allLoading = yearQueries.some((q) => q.isLoading);

  return (
    <PageLayout>
      <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg mb-6">
        Reading Progress
      </h1>
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg">
            Compare Yearly Progress
          </h2>
          <div className="bg-white rounded-b-lg shadow p-4">
            {allLoading ? (
              <div className="h-96 bg-gray-200 rounded animate-pulse" />
            ) : (
              <>
                <YearProgressChart yearBooks={yearBooks} currentYear={CURRENT_YEAR} />
                <p className="text-xs text-slate mt-2 text-center">
                  Cumulative pages by day of year — last 15 years. Click a line to view that year.
                </p>
              </>
            )}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white bg-umber px-4 py-2 rounded-t-lg">
            All Years Statistics
          </h2>
          <div className="bg-white rounded-b-lg shadow p-4">
            {summaryLoading ? (
              <div className="h-96 bg-gray-200 rounded animate-pulse" />
            ) : (
              <>
                <AllYearsChart data={yearlySummary} currentYear={CURRENT_YEAR} />
                <p className="text-xs text-slate mt-2 text-center">
                  Total pages per year. Current year highlighted. Click a bar to view that year.
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
