import { useQuery } from '@tanstack/react-query';
import { searchBooks } from '../api/books';

export type SearchParams = Record<string, string | number | undefined>;

export function useBooksSearch(params: SearchParams) {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== undefined)
  ) as Record<string, string | number>;

  return useQuery({
    queryKey: ['books-search', cleanParams],
    queryFn: () => searchBooks(cleanParams),
    enabled: Object.keys(cleanParams).length > 0,
    staleTime: 0,
  });
}
