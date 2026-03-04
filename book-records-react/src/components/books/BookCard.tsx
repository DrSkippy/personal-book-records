import { useNavigate } from 'react-router-dom';
import TagBadge from '../tags/TagBadge';
import { formatDisplay } from '../../lib/dates';
import { DEFAULT_BOOK_IMAGE } from '../../lib/constants';

interface BookCardProps {
  bookId: number;
  title: string;
  author: string;
  tags?: string[];
  lastReadDate?: string | null;
  imageUrl?: string | null;
}

export default function BookCard({ bookId, title, author, tags = [], lastReadDate, imageUrl }: BookCardProps) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/books/${bookId}`)}
      className="bg-white rounded-lg shadow-md p-4 cursor-pointer hover:shadow-lg transition-shadow"
    >
      <img
        src={imageUrl || DEFAULT_BOOK_IMAGE}
        alt={title}
        className="w-full h-auto rounded-md mb-3"
        onError={(e) => { (e.target as HTMLImageElement).src = DEFAULT_BOOK_IMAGE; }}
      />
      <h3 className="text-sm font-semibold text-secondary truncate">{title}</h3>
      <p className="text-xs text-slate mb-2 truncate">{author}</p>
      <div className="flex flex-wrap gap-1 mb-2">
        {tags.slice(0, 3).map((tag) => (
          <TagBadge key={tag} tag={tag} clickable={false} />
        ))}
      </div>
      {lastReadDate && (
        <p className="text-xs text-slate">Read: {formatDisplay(lastReadDate)}</p>
      )}
    </div>
  );
}
