import { useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { bookSchema, type BookFormValues } from '../../lib/validation';
import { VALID_LOCATIONS, COVER_TYPES } from '../../lib/constants';

interface BookFormProps {
  defaultValues?: Partial<BookFormValues>;
  onSubmit: (values: BookFormValues) => Promise<void>;
  isSubmitting?: boolean;
  submitLabel?: string;
  onCancel?: () => void;
}

export default function BookForm({ defaultValues, onSubmit, isSubmitting, submitLabel = 'Save', onCancel }: BookFormProps) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<BookFormValues>({
    resolver: zodResolver(bookSchema) as Resolver<BookFormValues>,
    defaultValues: {
      Recycled: 0,
      Location: 'Main Collection',
      ...defaultValues,
    },
  });

  const coverType = watch('CoverType');
  const isDigital = coverType === 'Digital';
  const availableLocations = VALID_LOCATIONS.filter((loc) =>
    isDigital ? loc === 'DOWNLOAD' : loc !== 'DOWNLOAD'
  );

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-surface rounded-md p-8 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Title *</label>
          <input {...register('Title')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
          {errors.Title && <p className="text-red-500 text-xs mt-1">{errors.Title.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Author *</label>
          <input {...register('Author')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
          {errors.Author && <p className="text-red-500 text-xs mt-1">{errors.Author.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Copyright Date</label>
          <input {...register('CopyrightDate')} placeholder="YYYY or YYYY-MM-DD" className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Pages</label>
          <input type="number" {...register('Pages')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
          {errors.Pages && <p className="text-red-500 text-xs mt-1">{errors.Pages.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Publisher</label>
          <input {...register('PublisherName')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Cover Type</label>
          <select {...register('CoverType')} className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white">
            <option value="">-- Select --</option>
            {COVER_TYPES.map((ct) => <option key={ct} value={ct}>{ct}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">Location *</label>
          <select {...register('Location')} className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white">
            {availableLocations.map((loc) => <option key={loc} value={loc}>{loc}</option>)}
          </select>
          {errors.Location && <p className="text-red-500 text-xs mt-1">{errors.Location.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">ISBN-10</label>
          <input {...register('IsbnNumber')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate mb-1">ISBN-13</label>
          <input {...register('IsbnNumber13')} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate mb-1">Book Note</label>
        <textarea {...register('BookNote')} rows={4} className="w-full px-3 py-2 border-2 border-gray-300 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
      </div>
      <div className="flex items-center gap-2">
        <input type="checkbox" id="recycled" {...register('Recycled', { setValueAs: (v) => v ? 1 : 0 })} className="w-4 h-4" />
        <label htmlFor="recycled" className="text-sm font-medium text-slate">Recycled / Removed</label>
      </div>
      <div className="flex gap-3 pt-2">
        <button type="submit" disabled={isSubmitting} className="bg-secondary text-white border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-umber disabled:opacity-50">
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="bg-surface border border-gray-300 rounded-lg px-4 py-2 text-sm cursor-pointer hover:bg-gray-200">
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
