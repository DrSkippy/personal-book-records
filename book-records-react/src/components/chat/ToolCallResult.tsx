import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface ToolCallResultProps {
  toolName: string;
  args?: Record<string, unknown>;
  result?: unknown;
}

export default function ToolCallResult({ toolName, args, result }: ToolCallResultProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="my-2 border border-gray-200 rounded-lg overflow-hidden text-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-surface hover:bg-gray-100 text-left"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="font-mono font-bold text-secondary">{toolName}</span>
        {args && (
          <span className="text-slate">
            ({Object.entries(args).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ')})
          </span>
        )}
      </button>
      {expanded && result !== undefined && (
        <pre className="px-3 py-2 bg-white overflow-x-auto text-slate">
          {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
