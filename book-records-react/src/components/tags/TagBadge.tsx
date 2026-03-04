import { useNavigate } from 'react-router-dom';

interface TagBadgeProps {
  tag: string;
  clickable?: boolean;
}

export default function TagBadge({ tag, clickable = true }: TagBadgeProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (clickable) {
      navigate(`/books?tags=${encodeURIComponent(tag)}`);
    }
  };

  return (
    <span
      onClick={handleClick}
      className={`inline-block bg-accent-light text-secondary text-xs font-medium px-2 py-0.5 rounded-full ${
        clickable ? 'cursor-pointer hover:bg-accent' : ''
      }`}
    >
      {tag}
    </span>
  );
}
