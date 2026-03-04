import type { ReactNode } from 'react';

interface TwoColumnLayoutProps {
  left: ReactNode;
  right: ReactNode;
  className?: string;
}

export default function TwoColumnLayout({ left, right, className = '' }: TwoColumnLayoutProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 ${className}`}>
      <div>{left}</div>
      <div>{right}</div>
    </div>
  );
}
