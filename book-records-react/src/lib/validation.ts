import { z } from 'zod';

const emptyToUndefined = (val: unknown) => (val === '' || val == null ? undefined : val);

// Accepts YYYY or a real calendar date YYYY-MM-DD (Postgres rejects year 0000 and e.g. 1999-02-30).
const isValidCopyrightDate = (v: string) => {
  const m = /^(\d{4})(?:-(\d{2})-(\d{2}))?$/.exec(v);
  if (!m) return false;
  const [year, month, day] = [Number(m[1]), Number(m[2] ?? 1), Number(m[3] ?? 1)];
  if (year < 1) return false;
  const d = new Date(Date.UTC(year, month - 1, day));
  return d.getUTCFullYear() === year && d.getUTCMonth() === month - 1 && d.getUTCDate() === day;
};

export const bookSchema = z.object({
  Title: z.string().min(1, 'Title is required').max(200),
  Author: z.string().min(1, 'Author is required').max(200),
  Location: z.string().min(1, 'Location is required'),
  CopyrightDate: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || isValidCopyrightDate(v), 'Use YYYY or YYYY-MM-DD')
    .transform((v) => (v && /^\d{4}$/.test(v) ? `${v}-01-01` : v)),
  IsbnNumber: z.string().max(13).optional(),
  IsbnNumber13: z.string().max(13).optional(),
  PublisherName: z.string().max(50).optional(),
  CoverType: z.preprocess(emptyToUndefined, z.enum(['Hard', 'Soft', 'Digital']).optional()),
  Pages: z.preprocess(emptyToUndefined, z.coerce.number().int().positive().max(32767).optional()),
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
