export const VALID_LOCATIONS = [
  'Main Collection',
  'Bedroom',
  'Storage',
  'Oversized',
  'Pets',
  'Woodwork',
  'Reference',
  'Birding',
] as const;

export const COVER_TYPES = ['Hard', 'Soft', 'Digital'] as const;

export const DEFAULT_BOOK_IMAGE = `${import.meta.env.VITE_RESOURCE_BASE_URL}/default.webp`;
