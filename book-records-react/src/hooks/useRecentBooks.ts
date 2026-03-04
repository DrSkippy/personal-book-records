import { useQuery } from '@tanstack/react-query';
import { getRecentBooks } from '../api/books';

export function useRecentBooks(limit = 10) {
  return useQuery({
    queryKey: ['recent', limit],
    queryFn: () => getRecentBooks(limit),
  });
}
