import { useQuery } from '@tanstack/react-query';
import { getTagCounts } from '../api/tags';

export function useTagCounts(prefix?: string) {
  return useQuery({
    queryKey: ['tag-counts', prefix],
    queryFn: () => getTagCounts(prefix),
  });
}
