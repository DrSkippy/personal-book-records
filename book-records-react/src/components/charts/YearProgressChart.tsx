import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { getDayOfYear } from '../../lib/dates';
import type { Book } from '../../types';

interface YearProgressChartProps {
  yearBooks: Record<number, Book[]>;
  currentYear: number;
}

export default function YearProgressChart({ yearBooks, currentYear }: YearProgressChartProps) {
  const navigate = useNavigate();

  // Build data: [{day: 1, 2024: 300, 2023: 250, ...}, ...]
  const maxDay = 366;
  const years = Object.keys(yearBooks).map(Number).sort((a, b) => b - a);

  // For each year compute cumulative pages per day
  const cumulativeByYear: Record<number, Record<number, number>> = {};
  for (const year of years) {
    const books = yearBooks[year] || [];
    const dayPages: Record<number, number> = {};
    for (const book of books) {
      const bookRecord = book as unknown as Record<string, unknown>;
      if (bookRecord['ReadDate']) {
        const day = getDayOfYear(String(bookRecord['ReadDate']));
        const pages = Number(book.Pages) || 0;
        dayPages[day] = (dayPages[day] || 0) + pages;
      }
    }
    // Accumulate
    let cumulative = 0;
    const dayToPages: Record<number, number> = {};
    for (let d = 1; d <= maxDay; d++) {
      cumulative += dayPages[d] || 0;
      if (cumulative > 0) dayToPages[d] = cumulative;
    }
    cumulativeByYear[year] = dayToPages;
  }

  // Build flat data array
  const allDays = new Set<number>();
  for (const year of years) {
    Object.keys(cumulativeByYear[year]).forEach(d => allDays.add(Number(d)));
  }
  const data = Array.from(allDays).sort((a, b) => a - b).map(day => {
    const row: Record<string, number> = { day };
    for (const year of years) {
      if (cumulativeByYear[year][day] !== undefined) {
        row[String(year)] = cumulativeByYear[year][day];
      }
    }
    return row;
  });

  const colors = ['#75bba7', '#6c809a', '#795663', '#7ae7c7', '#645244', '#a0b4c8', '#c0a0ac', '#90d4c4'];

  return (
    <ResponsiveContainer width="100%" height={500}>
      <LineChart data={data} margin={{ left: 24 }} onClick={(e: unknown) => {
        const evt = e as { activePayload?: Array<{ dataKey?: string }> };
        if (evt?.activePayload?.[0]?.dataKey) {
          navigate(`/year/${evt.activePayload[0].dataKey}`);
        }
      }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="day" label={{ value: 'Day of Year', position: 'insideBottom', offset: -5 }} />
        <YAxis label={{ value: 'Cumulative Pages', angle: -90, position: 'insideLeft', dx: -16 }} />
        <Tooltip />
        <Legend />
        {years.map((year, i) => (
          <Line
            key={year}
            type="monotone"
            dataKey={String(year)}
            dot={false}
            stroke={year === currentYear ? '#75bba7' : colors[i] || '#6c809a'}
            strokeWidth={year === currentYear ? 3 : 1}
            strokeOpacity={year === currentYear ? 1 : 0.6}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
