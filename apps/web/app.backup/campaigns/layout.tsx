import { ReactNode } from 'react';

interface CampaignsLayoutProps {
  children: ReactNode;
}

export default function CampaignsLayout({ children }: CampaignsLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1">{children}</main>
    </div>
  );
}
