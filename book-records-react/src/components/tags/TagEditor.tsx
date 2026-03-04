import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { addTag } from '../../api/tags';
import { Plus } from 'lucide-react';

interface TagEditorProps {
  bookId: number;
  existingTags: string[];
}

export default function TagEditor({ bookId }: TagEditorProps) {
  const [newTag, setNewTag] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const handleAdd = async () => {
    const tag = newTag.trim();
    if (!tag) return;
    setIsAdding(true);
    setError('');
    try {
      await addTag(bookId, tag);
      setNewTag('');
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
    } catch {
      setError('Failed to add tag');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="mt-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="Add tag..."
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-surface"
        />
        <button
          onClick={handleAdd}
          disabled={isAdding || !newTag.trim()}
          className="flex items-center gap-1 bg-secondary text-white px-3 py-1 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
        >
          <Plus size={14} />
          Add
        </button>
      </div>
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
}
