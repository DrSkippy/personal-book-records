import { apiClient } from './client';
import type { Book, CompleteRecord, StandardResponse } from '../types';

export const searchBooks = (params: Record<string, string | number>) =>
  apiClient.get<StandardResponse>('/books_search', { params }).then(r => r.data);

export const getCompleteRecord = (bookId: number) =>
  apiClient.get<CompleteRecord>(`/complete_record/${bookId}`).then(r => r.data);

export const getCompleteRecordAdjacent = (bookId: number, direction: 'next' | 'prev') =>
  apiClient.get<CompleteRecord>(`/complete_record/${bookId}/${direction}`).then(r => r.data);

export const getCompleteRecordsWindow = (bookId: number, windowSize: number) =>
  apiClient.get<CompleteRecord[]>(`/complete_records_window/${bookId}/${windowSize}`).then(r => r.data);

export const getCompleteRecordsByIds = (bookIds: number[]) =>
  apiClient.post<CompleteRecord[]>('/complete_record_window', { book_ids: bookIds }).then(r => r.data);

export const getRecentBooks = (limit = 10) =>
  apiClient.get<StandardResponse>(limit === 10 ? '/recent' : `/recent/${limit}`).then(r => r.data);

export const addBooks = (books: Partial<Book>[]) =>
  apiClient.post('/add_books', books).then(r => r.data);

export const updateBook = (book: Partial<Book> & { BookId: number }) =>
  apiClient.post('/update_book_record', book).then(r => r.data);

export const updateBookNoteStatus = (data: { BookId: number; BookNote?: string; Recycled?: 0 | 1 }) =>
  apiClient.post('/update_book_note_status', data).then(r => r.data);

export const deleteBook = (bookId: number) =>
  apiClient.delete(`/delete_book/${bookId}`).then(r => r.data);

export const lookupByIsbn = (isbnList: string[]) =>
  apiClient.post('/books_by_isbn', { isbn_list: isbnList }).then(r => r.data);

export const getConfiguration = () =>
  apiClient.get('/configuration').then(r => r.data);
