import { useQuery } from '@tanstack/react-query';
import { getDailyPageRecords } from '../api/estimates';

export function useDailyPageRecords(recordId: number | null) {
  return useQuery({
    queryKey: ['daily-pages', recordId],
    queryFn: () => getDailyPageRecords(recordId!),
    enabled: recordId !== null,
  });
}
