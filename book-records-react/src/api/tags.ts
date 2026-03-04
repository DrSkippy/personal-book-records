import { apiClient } from './client';
import type { StandardResponse } from '../types';

export const getTagsForBook = (bookId: number) =>
  apiClient.get(`/tags/${bookId}`).then(r => r.data);

export const getTagCounts = (prefix?: string) =>
  apiClient.get<StandardResponse>(prefix ? `/tag_counts/${prefix}` : '/tag_counts').then(r => r.data);

export const searchByTag = (tag: string) =>
  apiClient.get<StandardResponse>(`/tags_search/${encodeURIComponent(tag)}`).then(r => r.data);

export const addTag = (bookId: number, tag: string) =>
  apiClient.put(`/add_tag/${bookId}/${encodeURIComponent(tag)}`).then(r => r.data);

export const renameTag = (current: string, updated: string) =>
  apiClient.put(`/update_tag_value/${encodeURIComponent(current)}/${encodeURIComponent(updated)}`).then(r => r.data);
