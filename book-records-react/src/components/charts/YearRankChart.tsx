import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer
} from 'recharts';
import type { YearlySummary } from '../../types';

interface YearRankChartProps {
  data: YearlySummary[];
  currentYear: number;
}

interface RankedYear extends YearlySummary {
  rank: number;
}

export default function YearRankChart({ data, currentYear }: YearRankChartProps) {
  const navigate = useNavigate();

  const ranked: RankedYear[] = [...data]
    .sort((a, b) => b['pages read'] - a['pages read'])
    .map((entry, i) => ({ ...entry, rank: i + 1 }));

  return (
    <ResponsiveContainer width="100%" height={440}>
      <BarChart
        data={ranked}
        margin={{ left: 24, right: 16, bottom: 32 }}
        onClick={(e: unknown) => {
          const evt = e as { activePayload?: Array<{ payload?: RankedYear }> };
          if (evt?.activePayload?.[0]?.payload) {
            const year = evt.activePayload[0].payload.year;
            navigate(`/year/${year}`);
          }
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="rank" tick={{ dy: 8 }} label={{ value: 'Rank', position: 'bottom', offset: 20 }} />
        <YAxis label={{ value: 'Pages Read', angle: -90, position: 'insideLeft', dx: -16 }} />
        <Tooltip
          formatter={(value: number | undefined) => [(value ?? 0).toLocaleString(), 'Pages Read']}
          labelFormatter={(label: unknown, payload) => {
            const year = payload?.[0]?.payload?.year;
            return year ? `Rank ${label} — Year ${year}` : `Rank ${label}`;
          }}
        />
        <Bar dataKey="pages read" cursor="pointer">
          {ranked.map((entry) => (
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
