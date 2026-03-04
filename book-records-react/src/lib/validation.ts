import { z } from 'zod';

export const bookSchema = z.object({
  Title: z.string().min(1, 'Title is required').max(200),
  Author: z.string().min(1, 'Author is required').max(200),
  Location: z.string().min(1, 'Location is required'),
  CopyrightDate: z.string().optional(),
  IsbnNumber: z.string().max(13).optional(),
  IsbnNumber13: z.string().max(13).optional(),
  PublisherName: z.string().max(50).optional(),
  CoverType: z.enum(['Hard', 'Soft', 'Digital']).optional(),
  Pages: z.coerce.number().int().positive().max(32767).optional(),
  BookNote: z.string().optional(),
  Recycled: z.literal(0).or(z.literal(1)).default(0),
});

export type BookFormValues = z.infer<typeof bookSchema>;

export const readDateSchema = z.object({
  BookId: z.number().int().positive(),
  ReadDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be YYYY-MM-DD'),
  ReadNote: z.string().optional(),
});

export const estimateSchema = z.object({
  lastReadablePage: z.coerce.number().int().positive('Must be a positive page number'),
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});
