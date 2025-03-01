import { ReactNode } from 'react';

interface TemplatesLayoutProps {
  children: ReactNode;
}

export default function TemplatesLayout({ children }: TemplatesLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1">{children}</main>
    </div>
  );
}
