import { useQuery } from '@tanstack/react-query';
import { getBooksRead } from '../api/reads';

export function useBooksReadByYear(year?: number) {
  return useQuery({
    queryKey: ['books-read', year],
    queryFn: () => getBooksRead(year),
  });
}
