import { apiClient } from './client';
import type { StandardResponse } from '../types';

export const getBooksRead = (year?: number) =>
  apiClient.get<StandardResponse>(year ? `/books_read/${year}` : '/books_read').then(r => r.data);

export const getYearlySummary = (year?: number) =>
  apiClient.get<StandardResponse>(year ? `/summary_books_read_by_year/${year}` : '/summary_books_read_by_year').then(r => r.data);

export const getReadStatus = (bookId: number) =>
  apiClient.get<StandardResponse>(`/status_read/${bookId}`).then(r => r.data);

export const addReadDates = (records: Array<{ BookId: number; ReadDate: string; ReadNote?: string }>) =>
  apiClient.post('/add_read_dates', records).then(r => r.data);

export const updateEditReadNote = (data: { BookId: number; ReadDate: string; ReadNote: string }) =>
  apiClient.post('/update_edit_read_note', data).then(r => r.data);
