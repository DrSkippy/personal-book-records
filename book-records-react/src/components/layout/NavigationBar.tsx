import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { getConfiguration } from '../../api/books';

export default function NavigationBar() {
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    getConfiguration()
      .then((data) => setVersion(data.version || ''))
      .catch(() => {});
  }, []);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-surface no-underline px-4 py-3 text-sm font-medium transition-colors ${
      isActive ? 'bg-primary' : 'hover:bg-slate'
    }`;

  return (
    <nav className="sticky top-0 z-50 bg-secondary text-white shadow-md">
      <div className="max-w-screen-xl mx-auto flex items-center flex-wrap">
        <NavLink to="/" className={navLinkClass} end>Browse Collection</NavLink>
        <NavLink to="/carousel/2" className={navLinkClass}>Book Carousel</NavLink>
        <NavLink to="/books" className={navLinkClass}>Search & Reports</NavLink>
        <NavLink to="/progress" className={navLinkClass}>Yearly Progress</NavLink>
        <NavLink to="/year/all" className={navLinkClass}>Books Read — All</NavLink>
        <NavLink to="/inventory" className={navLinkClass}>Inventory</NavLink>
        <NavLink to="/ai-chat" className={navLinkClass}>AI Chat</NavLink>
        <span className="ml-auto flex gap-3 text-sm opacity-75 px-4">
          <span>UI v{__APP_VERSION__}</span>
          {version && <span>API v{version}</span>}
        </span>
      </div>
    </nav>
  );
}
