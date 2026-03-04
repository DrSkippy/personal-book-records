import { useQuery } from '@tanstack/react-query';
import { getEstimates } from '../api/estimates';

export function useReadingEstimates(bookId: number | null) {
  return useQuery({
    queryKey: ['estimates', bookId],
    queryFn: () => getEstimates(bookId!),
    enabled: bookId !== null,
  });
}
