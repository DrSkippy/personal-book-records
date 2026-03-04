import type { ReactNode } from 'react';
import NavigationBar from './NavigationBar';

interface PageLayoutProps {
  children: ReactNode;
}

export default function PageLayout({ children }: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-surface">
      <NavigationBar />
      <main className="max-w-screen-xl mx-auto px-4 md:px-6 py-6">
        {children}
      </main>
    </div>
  );
}
