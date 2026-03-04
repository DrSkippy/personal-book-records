import { apiClient } from './client';

export const getEstimates = (bookId: number) =>
  apiClient.get(`/record_set/${bookId}`).then(r => r.data);

export const getDailyPageRecords = (recordId: number) =>
  apiClient.get(`/date_page_records/${recordId}`).then(r => r.data);

export const addEstimate = (bookId: number, lastReadablePage: number, startDate?: string) => {
  const path = startDate
    ? `/add_book_estimate/${bookId}/${lastReadablePage}/${startDate}`
    : `/add_book_estimate/${bookId}/${lastReadablePage}`;
  return apiClient.put(path).then(r => r.data);
};

export const addDailyPage = (data: { RecordId: number; RecordDate: string; Page: number }) =>
  apiClient.post('/add_date_page', data).then(r => r.data);
