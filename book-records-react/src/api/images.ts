import { apiClient } from './client';

export const getImages = (bookId: number) =>
  apiClient.get(`/images/${bookId}`).then(r => r.data);

export const addImageRecord = (data: { BookId: number; Name: string; Url: string; ImageType?: string }) =>
  apiClient.post('/add_image', data).then(r => r.data);

export const uploadImage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/upload_image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};
