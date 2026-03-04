import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { formatDisplay } from '../../lib/dates';

export interface ColumnDef {
  key: string;
  label: string;
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

interface BookTableProps {
  books: unknown[];
  columns: ColumnDef[];
  onRowClick?: (id: number) => void;
  selectedId?: number | null;
}

export default function BookTable({ books, columns, onRowClick, selectedId }: BookTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const rows = books as Record<string, unknown>[];

  const sorted = sortKey
    ? [...rows].sort((a, b) => {
        const av = a[sortKey] ?? '';
        const bv = b[sortKey] ?? '';
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : rows;

  const renderCell = (col: ColumnDef, row: Record<string, unknown>) => {
    const value = row[col.key];
    if (col.render) return col.render(value, row);
    if (col.key.toLowerCase().includes('date') && value) {
      return formatDisplay(String(value));
    }
    return value !== null && value !== undefined ? String(value) : '';
  };

  if (!rows.length) {
    return (
      <div className="text-slate text-sm py-6 text-center bg-white rounded-xl border border-gray-300">
        No books found.
      </div>
    );
  }

  return (
    <div className="w-full border border-gray-300 rounded-xl overflow-hidden shadow-lg">
      <table className="w-full border-separate border-spacing-0">
        <thead>
          <tr className="bg-primary text-white">
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="px-3 py-3 text-left text-sm font-semibold cursor-pointer select-none whitespace-nowrap"
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {sortKey === col.key ? (
                    sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  ) : null}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => {
            const id = row['BookId'] as number;
            const isSelected = selectedId === id;
            return (
              <tr
                key={i}
                onClick={() => onRowClick?.(id)}
                className={`cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-primary/20'
                    : i % 2 === 0
                    ? 'bg-accent-light hover:bg-accent/30'
                    : 'bg-white hover:bg-surface'
                }`}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2.5 text-sm align-top">
                    {renderCell(col, row)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
