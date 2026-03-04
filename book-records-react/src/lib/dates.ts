import { format, parseISO } from 'date-fns';

export function formatDisplay(date: string | null | undefined): string {
  if (!date) return '';
  try {
    return format(parseISO(date), 'MMM d, yyyy');
  } catch {
    return date;
  }
}

export function formatApi(date: Date): string {
  return format(date, 'yyyy-MM-dd');
}

export function todayApi(): string {
  return formatApi(new Date());
}

export function getDayOfYear(dateStr: string): number {
  const date = parseISO(dateStr);
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}
