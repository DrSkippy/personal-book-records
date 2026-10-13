import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Check, Save, X } from 'lucide-react';
import { updateEditReadNote } from '../../api/reads';

interface ReadNoteDraftEditorProps {
  bookId: number;
  readDate: string;
  initialDraft: string;
  title?: string;
  onDiscard?: () => void;
  onSaved?: () => void;
}

/**
 * Editable AI-drafted read note. Nothing is written until the user clicks Save,
 * which replaces the read's ReadNote via POST /update_edit_read_note.
 */
export default function ReadNoteDraftEditor({ bookId, readDate, initialDraft, title, onDiscard, onSaved }: ReadNoteDraftEditorProps) {
  const queryClient = useQueryClient();
  const [text, setText] = useState(initialDraft);
  const [status, setStatus] = useState<'editing' | 'saving' | 'saved' | 'discarded'>('editing');
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setStatus('saving');
    setError(null);
    try {
      await updateEditReadNote({ BookId: bookId, ReadDate: readDate, ReadNote: text.trim() });
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
      setStatus('saved');
      onSaved?.();
    } catch {
      setError('Failed to save the read note. Please try again.');
      setStatus('editing');
    }
  };

  const handleDiscard = () => {
    setStatus('discarded');
    onDiscard?.();
  };

  if (status === 'saved') {
    return (
      <p className="flex items-center gap-1 text-sm text-green-700">
        <Check size={14} /> Read note saved{title ? ` for "${title}"` : ''} ({readDate}).
      </p>
    );
  }
  if (status === 'discarded') {
    return <p className="text-sm text-slate italic">Draft discarded.</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate">
        Draft read note{title ? ` for "${title}"` : ''}, read {readDate}. Edit it as needed, then save.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-surface text-sm text-slate focus:outline-none focus:ring-2 focus:ring-primary"
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={status === 'saving' || !text.trim()}
          className="flex items-center gap-1 bg-secondary text-white px-3 py-1.5 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
        >
          <Save size={14} /> {status === 'saving' ? 'Saving...' : 'Save read note'}
        </button>
        <button
          onClick={handleDiscard}
          disabled={status === 'saving'}
          className="flex items-center gap-1 bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-300 disabled:opacity-50"
        >
          <X size={14} /> Discard
        </button>
      </div>
    </div>
  );
}
