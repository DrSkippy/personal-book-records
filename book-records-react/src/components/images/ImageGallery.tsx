import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { uploadImage, addImageRecord } from '../../api/images';
import { DEFAULT_BOOK_IMAGE } from '../../lib/constants';
import { Upload } from 'lucide-react';

interface ImageItem {
  ImageId: number;
  Url: string | null;
  Name: string | null;
  ImageType: string;
}

interface ImageGalleryProps {
  bookId: number;
  images: ImageItem[];
}

export default function ImageGallery({ bookId, images }: ImageGalleryProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const queryClient = useQueryClient();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadError('');
    try {
      const uploadResult = await uploadImage(file);
      const filename = uploadResult.upload_image?.filename;
      const url = `${import.meta.env.VITE_RESOURCE_BASE_URL}/${filename}`;
      await addImageRecord({ BookId: bookId, Name: filename, Url: url, ImageType: 'cover-face' });
      queryClient.invalidateQueries({ queryKey: ['complete-record', bookId] });
      queryClient.invalidateQueries({ queryKey: ['images', bookId] });
    } catch {
      setUploadError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div>
      {images.length === 0 ? (
        <p className="text-slate text-sm mb-3">(No images available)</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
          {images.map((img) => (
            <div key={img.ImageId} className="space-y-1">
              <img
                src={img.Url || DEFAULT_BOOK_IMAGE}
                alt={img.Name || 'Book cover'}
                className="w-full h-auto rounded-lg"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = DEFAULT_BOOK_IMAGE;
                }}
              />
              {img.Name && <p className="text-xs text-slate truncate">{img.Name}</p>}
              <p className="text-xs text-slate">{img.ImageType}</p>
            </div>
          ))}
        </div>
      )}
      <label className="flex items-center gap-2 cursor-pointer bg-secondary text-white px-3 py-2 rounded-lg text-sm hover:bg-umber w-fit">
        <Upload size={16} />
        {isUploading ? 'Uploading...' : 'Upload Image'}
        <input type="file" accept="image/*" className="hidden" onChange={handleUpload} disabled={isUploading} />
      </label>
      {uploadError && <p className="text-red-500 text-xs mt-1">{uploadError}</p>}
    </div>
  );
}
