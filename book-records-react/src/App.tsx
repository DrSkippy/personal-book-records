import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import BookSearch from './pages/BookSearch';
import AddBook from './pages/AddBook';
import BookDetail from './pages/BookDetail';
import EditBook from './pages/EditBook';
import AddReadDate from './pages/AddReadDate';
import BatchUpdateReadNotes from './pages/BatchUpdateReadNotes';
import BooksByYear from './pages/BooksByYear';
import Inventory from './pages/Inventory';
import Carousel from './pages/Carousel';
import Progress from './pages/Progress';
import ReadingEstimates from './pages/ReadingEstimates';
import AddEstimate from './pages/AddEstimate';
import AddPageProgress from './pages/AddPageProgress';
import AiChat from './pages/AiChat';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/books" element={<BookSearch />} />
        {/* /books/add MUST come before /books/:id to avoid ambiguity */}
        <Route path="/books/add" element={<AddBook />} />
        <Route path="/books/:id" element={<BookDetail />} />
        <Route path="/books/:id/edit" element={<EditBook />} />
        <Route path="/read/add/:id" element={<AddReadDate />} />
        <Route path="/read/update" element={<BatchUpdateReadNotes />} />
        <Route path="/year/:year" element={<BooksByYear />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/carousel/:id" element={<Carousel />} />
        <Route path="/progress" element={<Progress />} />
        {/* /estimates/add/:id MUST come before /estimates/:id */}
        <Route path="/estimates/add/:id" element={<AddEstimate />} />
        <Route path="/estimates/:id/progress" element={<AddPageProgress />} />
        <Route path="/estimates/:id" element={<ReadingEstimates />} />
        <Route path="/ai-chat" element={<AiChat />} />
      </Routes>
    </BrowserRouter>
  );
}
