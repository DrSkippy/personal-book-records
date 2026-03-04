import { useQuery } from '@tanstack/react-query';
import { getImages } from '../api/images';

export function useImages(bookId: number | null) {
  return useQuery({
    queryKey: ['images', bookId],
    queryFn: () => getImages(bookId!),
    enabled: bookId !== null,
  });
}
