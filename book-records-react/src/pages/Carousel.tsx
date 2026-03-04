import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';
import { getCompleteRecordsWindow, getCompleteRecordAdjacent } from '../api/books';
import { toObjects } from '../lib/utils';
import { formatDisplay } from '../lib/dates';
import { DEFAULT_BOOK_IMAGE } from '../lib/constants';
import type { Book, ReadRecord, CompleteRecord } from '../types';
import { ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';

interface CarouselBook {
  book: Book;
  reads: ReadRecord[];
  tags: string[];
  imageUrl: string | null;
}

function parseCompleteRecord(record: CompleteRecord): CarouselBook {
  const books = toObjects<Book>(record.book);
  const book = books[0];
  const reads = toObjects<ReadRecord>(record.reads);
  const tags: string[] = record.tags.data[0] ? (record.tags.data[0] as string[]) : [];
  const images: string[] = record.img.data[0] ? (record.img.data[0] as string[]) : [];
  return { book, reads, tags, imageUrl: images[0] || null };
}

function BookSlide({ item, onNavigate }: { item: CarouselBook; onNavigate: (id: number) => void }) {
  const { book, reads, tags, imageUrl } = item;
  const lastRead = reads[reads.length - 1];

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-full">
      <div className="relative">
        <img
          src={imageUrl || DEFAULT_BOOK_IMAGE}
          alt={book.Title}
          className="w-full h-auto"
          onError={(e) => { (e.target as HTMLImageElement).src = DEFAULT_BOOK_IMAGE; }}
        />
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
          <p className="text-white text-sm font-bold truncate">{book.Title}</p>
        </div>
      </div>
      <div className="p-4 flex-1 text-sm space-y-1 overflow-y-auto">
        <p className="text-slate"><span className="font-medium">Author:</span> {book.Author}</p>
        {book.CopyrightDate && <p className="text-slate"><span className="font-medium">Year:</span> {book.CopyrightDate.slice(0, 4)}</p>}
        {book.Pages && <p className="text-slate"><span className="font-medium">Pages:</span> {book.Pages}</p>}
        <p className="text-slate"><span className="font-medium">Location:</span> {book.Location}</p>
        <p className="text-slate"><span className="font-medium">ID:</span> {book.BookId}</p>
        {book.IsbnNumber && <p className="text-slate"><span className="font-medium">ISBN:</span> {book.IsbnNumber}</p>}
        {book.PublisherName && <p className="text-slate"><span className="font-medium">Publisher:</span> {book.PublisherName}</p>}
        {book.BookNote && <p className="text-slate text-xs italic mt-2">{book.BookNote.slice(0, 100)}{book.BookNote.length > 100 ? '...' : ''}</p>}
        {lastRead && (
          <p className="text-slate text-xs">
            <span className="font-medium">Read:</span> {formatDisplay(lastRead.DateRead)}
            {lastRead.ReadNote && <span className="block italic">{lastRead.ReadNote.slice(0, 80)}</span>}
          </p>
        )}
        {tags.length > 0 && (
          <p className="text-xs text-slate">
            <span className="font-medium">Tags:</span> {tags.join(', ')}
          </p>
        )}
        {!tags.length && <p className="text-xs text-slate">(no tags)</p>}
      </div>
      <div className="p-3 border-t border-gray-100">
        <button
          onClick={() => onNavigate(book.BookId)}
          className="w-full flex items-center justify-center gap-2 bg-secondary text-white py-2 rounded-lg text-sm hover:bg-umber"
        >
          <ExternalLink size={14} /> View Book
        </button>
      </div>
    </div>
  );
}

export default function Carousel() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const bookId = id ? parseInt(id) : 2;
  const safeBookId = isNaN(bookId) ? 2 : bookId;

  const [slides, setSlides] = useState<CarouselBook[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const minIdRef = useRef<number>(Infinity);
  const maxIdRef = useRef<number>(-Infinity);

  const slidesPerView = useRef(3);

  useEffect(() => {
    const updateSlidesPerView = () => {
      if (window.innerWidth < 768) slidesPerView.current = 1;
      else if (window.innerWidth < 1024) slidesPerView.current = 2;
      else slidesPerView.current = 3;
    };
    updateSlidesPerView();
    window.addEventListener('resize', updateSlidesPerView);
    return () => window.removeEventListener('resize', updateSlidesPerView);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    getCompleteRecordsWindow(safeBookId, 12)
      .then((records: CompleteRecord[]) => {
        const parsed = records.map(parseCompleteRecord).filter((item) => item.book);
        setSlides(parsed);
        const ids = parsed.map((p) => p.book.BookId);
        minIdRef.current = Math.min(...ids);
        maxIdRef.current = Math.max(...ids);
        // Find the index of the target book
        const targetIdx = parsed.findIndex((p) => p.book.BookId === safeBookId);
        setCurrentIndex(targetIdx >= 0 ? targetIdx : Math.floor(parsed.length / 2));
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [safeBookId]);

  const fetchPrev = async () => {
    if (minIdRef.current === Infinity) return;
    try {
      const record = await getCompleteRecordAdjacent(minIdRef.current, 'prev');
      const parsed = parseCompleteRecord(record);
      if (parsed.book) {
        minIdRef.current = parsed.book.BookId;
        setSlides((prev) => [parsed, ...prev]);
        setCurrentIndex((idx) => idx + 1);
      }
    } catch {}
  };

  const fetchNext = async () => {
    if (maxIdRef.current === -Infinity) return;
    try {
      const record = await getCompleteRecordAdjacent(maxIdRef.current, 'next');
      const parsed = parseCompleteRecord(record);
      if (parsed.book) {
        maxIdRef.current = parsed.book.BookId;
        setSlides((prev) => [...prev, parsed]);
      }
    } catch {}
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else {
      fetchPrev();
    }
  };

  const handleNext = () => {
    const spv = slidesPerView.current;
    if (currentIndex + spv < slides.length) {
      setCurrentIndex(currentIndex + 1);
    } else {
      fetchNext().then(() => setCurrentIndex((idx) => Math.min(idx + 1, slides.length - 1)));
    }
  };

  const visibleSlides = slides.slice(currentIndex, currentIndex + slidesPerView.current);

  if (isLoading) {
    return (
      <PageLayout>
        <div className="flex gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex-1 h-96 bg-gray-200 rounded-xl animate-pulse" />
          ))}
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-white bg-slate px-4 py-3 rounded-lg">Book Carousel</h1>

        <div className="flex items-center gap-4">
          <button
            onClick={handlePrev}
            className="shrink-0 p-3 bg-secondary text-white rounded-full hover:bg-umber transition-colors shadow-md"
          >
            <ChevronLeft size={24} />
          </button>

          <div className="flex-1 grid gap-4" style={{
            gridTemplateColumns: `repeat(${Math.min(slidesPerView.current, visibleSlides.length)}, 1fr)`
          }}>
            {visibleSlides.map((item) => (
              <BookSlide
                key={item.book.BookId}
                item={item}
                onNavigate={(id) => navigate(`/books/${id}`)}
              />
            ))}
          </div>

          <button
            onClick={handleNext}
            className="shrink-0 p-3 bg-secondary text-white rounded-full hover:bg-umber transition-colors shadow-md"
          >
            <ChevronRight size={24} />
          </button>
        </div>

        {/* Pagination dots */}
        <div className="flex gap-1 justify-center flex-wrap">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`w-2 h-2 rounded-full transition-colors ${
                i >= currentIndex && i < currentIndex + slidesPerView.current
                  ? 'bg-primary'
                  : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </PageLayout>
  );
}
