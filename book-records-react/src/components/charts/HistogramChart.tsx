import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer
} from 'recharts';
import type { YearlySummary } from '../../types';

interface HistogramChartProps {
  data: YearlySummary[];
  currentYear: number;
  bins?: number;
}

interface HistogramBin {
  label: string;
  count: number;
  containsCurrentYear: boolean;
}

export default function HistogramChart({ data, currentYear, bins = 14 }: HistogramChartProps) {
  const values = data.map((d) => d['pages read']);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const currentValue = data.find((d) => d.year === currentYear)?.['pages read'];
  const width = (max - min) / bins || 1;

  const histogram: HistogramBin[] = Array.from({ length: bins }, (_, i) => {
    const rangeStart = min + i * width;
    const rangeEnd = i === bins - 1 ? max : rangeStart + width;
    const containsCurrentYear =
      currentValue !== undefined &&
      currentValue >= rangeStart &&
      (i === bins - 1 ? currentValue <= rangeEnd : currentValue < rangeEnd);
    return {
      label: Math.round(rangeStart).toLocaleString(),
      count: 0,
      containsCurrentYear,
    };
  });

  values.forEach((v) => {
    let idx = width === 0 ? 0 : Math.floor((v - min) / width);
    idx = Math.min(Math.max(idx, 0), bins - 1);
    histogram[idx].count += 1;
  });

  return (
    <ResponsiveContainer width="100%" height={440}>
      <BarChart data={histogram} margin={{ left: 24, right: 16, bottom: 32 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="label"
          interval={Math.ceil(bins / 7) - 1}
          tick={{ dy: 8 }}
          label={{ value: 'Pages Read', position: 'bottom', offset: 20 }}
        />
        <YAxis allowDecimals={false} label={{ value: 'Years', angle: -90, position: 'insideLeft', dx: -16 }} />
        <Tooltip
          formatter={(value: number | undefined) => [value ?? 0, 'Years']}
          labelFormatter={(label) => `~${label} pages`}
        />
        <Bar dataKey="count">
          {histogram.map((bin, i) => (
            <Cell
              key={i}
              fill={bin.containsCurrentYear ? '#75bba7' : '#6c809a'}
              opacity={bin.containsCurrentYear ? 1 : 0.7}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
