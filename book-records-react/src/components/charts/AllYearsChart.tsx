import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, ReferenceLine
} from 'recharts';
import type { YearlySummary } from '../../types';

interface AllYearsChartProps {
  data: YearlySummary[];
  currentYear: number;
}

export default function AllYearsChart({ data, currentYear }: AllYearsChartProps) {
  const navigate = useNavigate();

  const sorted = [...data].sort((a, b) => a.year - b.year);

  return (
    <ResponsiveContainer width="100%" height={500}>
      <BarChart
        data={sorted}
        margin={{ left: 24 }}
        onClick={(e: unknown) => {
          const evt = e as { activePayload?: Array<{ payload?: YearlySummary }> };
          if (evt?.activePayload?.[0]?.payload) {
            const year = evt.activePayload[0].payload.year;
            navigate(`/year/${year}`);
          }
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="year" />
        <YAxis label={{ value: 'Pages Read', angle: -90, position: 'insideLeft', dx: -16 }} />
        <Tooltip
          formatter={(value: number | undefined) => [(value ?? 0).toLocaleString(), 'Pages Read']}
          labelFormatter={(label) => `Year: ${label}`}
        />
        <ReferenceLine x={currentYear} stroke="#795663" strokeDasharray="5 5" />
        <Bar dataKey="pages read" cursor="pointer">
          {sorted.map((entry) => (
            <Cell
              key={entry.year}
              fill={entry.year === currentYear ? '#75bba7' : '#6c809a'}
              opacity={entry.year === currentYear ? 1 : 0.7}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
