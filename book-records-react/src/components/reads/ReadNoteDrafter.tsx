import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import axios from 'axios';
import { draftReadNote } from '../../api/reads';
import ReadNoteDraftEditor from './ReadNoteDraftEditor';

interface ReadNoteDrafterProps {
  bookId: number;
  readDate: string;
}

const OBSERVATION_SLOTS = 4;

/**
 * For a read with no ReadNote: collect the reader's 3-4 key observations, have
 * the server's chat LLM draft a 3-4 paragraph review, and hand it to the
 * editor for review and saving.
 */
export default function ReadNoteDrafter({ bookId, readDate }: ReadNoteDrafterProps) {
  const [step, setStep] = useState<'idle' | 'observations' | 'drafting' | 'review'>('idle');
  const [observations, setObservations] = useState<string[]>(Array(OBSERVATION_SLOTS).fill(''));
  const [draft, setDraft] = useState('');
  const [draftKey, setDraftKey] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const filled = observations.map((o) => o.trim()).filter(Boolean);

  const handleDraft = async () => {
    setStep('drafting');
    setError(null);
    try {
      const result = await draftReadNote({ BookId: bookId, ReadDate: readDate, observations: filled });
      setDraft(result.draft);
      setDraftKey((k) => k + 1);
      setStep('review');
    } catch (err) {
      const message = axios.isAxiosError(err) && err.response?.data?.error;
      setError(message || 'Failed to draft a review. Please try again.');
      setStep('observations');
    }
  };

  if (step === 'idle') {
    return (
      <button
        onClick={() => setStep('observations')}
        className="flex items-center gap-1 text-secondary text-xs font-bold hover:bg-umber hover:text-surface px-1 rounded"
      >
        <Sparkles size={12} /> Draft review
      </button>
    );
  }

  if (step === 'review') {
    return (
      <div className="space-y-2">
        <ReadNoteDraftEditor
          key={draftKey}
          bookId={bookId}
          readDate={readDate}
          initialDraft={draft}
          onDiscard={() => setStep('observations')}
        />
        <button
          onClick={handleDraft}
          className="flex items-center gap-1 text-secondary text-xs font-bold hover:bg-umber hover:text-surface px-1 rounded"
        >
          <Sparkles size={12} /> Regenerate from observations
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate">What are the 3 to 4 most important observations about this book?</p>
      {observations.map((value, i) => (
        <input
          key={i}
          type="text"
          value={value}
          onChange={(e) => setObservations((prev) => prev.map((o, j) => (j === i ? e.target.value : o)))}
          placeholder={`Observation ${i + 1}${i === OBSERVATION_SLOTS - 1 ? ' (optional)' : ''}`}
          disabled={step === 'drafting'}
          className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
      ))}
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={handleDraft}
          disabled={step === 'drafting' || filled.length < 3}
          className="flex items-center gap-1 bg-secondary text-white px-3 py-1.5 rounded-lg text-sm hover:bg-umber disabled:opacity-50"
        >
          <Sparkles size={14} /> {step === 'drafting' ? 'Drafting...' : 'Draft review'}
        </button>
        <button
          onClick={() => setStep('idle')}
          disabled={step === 'drafting'}
          className="bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-300 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
