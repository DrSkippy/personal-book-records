interface ProgressBarProps {
  current: number;
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  return (
    <div className="w-full bg-surface rounded-full h-2 border border-gray-200">
      <div
        className="bg-primary h-2 rounded-full transition-all"
        style={{ width: `${pct}%` }}
      />
      <p className="text-xs text-slate mt-1">{current} / {total} pages ({pct}%)</p>
    </div>
  );
}
