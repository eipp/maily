import { ReactNode } from 'react';

interface SubscribersLayoutProps {
  children: ReactNode;
}

export default function SubscribersLayout({ children }: SubscribersLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1">{children}</main>
    </div>
  );
}
