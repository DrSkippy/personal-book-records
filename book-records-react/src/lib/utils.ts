import type { StandardResponse } from '../types';
import { clsx, type ClassValue } from 'clsx';

export function toObjects<T>(response: StandardResponse): T[] {
  return response.data.map(row =>
    Object.fromEntries(response.header.map((key, i) => [key, row[i]])) as T
  );
}

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}
