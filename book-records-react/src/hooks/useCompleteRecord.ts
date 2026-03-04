import { useQuery } from '@tanstack/react-query';
import { getCompleteRecord } from '../api/books';

export function useCompleteRecord(bookId: number | null) {
  return useQuery({
    queryKey: ['complete-record', bookId],
    queryFn: () => getCompleteRecord(bookId!),
    enabled: bookId !== null,
  });
}
