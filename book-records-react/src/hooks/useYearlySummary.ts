import { useQuery } from '@tanstack/react-query';
import { getYearlySummary } from '../api/reads';

export function useYearlySummary(year?: number) {
  return useQuery({
    queryKey: ['yearly-summary', year],
    queryFn: () => getYearlySummary(year),
    staleTime: 10 * 60 * 1000,
  });
}
