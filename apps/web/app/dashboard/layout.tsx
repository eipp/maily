import { Suspense } from 'react';
import Link from 'next/link';
import DashboardNav from '../../components/dashboard/DashboardNav';
import UserProfileDropdown from '../../components/dashboard/UserProfileDropdown';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

export const metadata = {
  title: 'Maily Dashboard',
  description: 'Manage your email campaigns with AI-powered tools',
};

// This is a Server Component - no "use client" directive
async function SidebarStats() {
  // In a real implementation, this would fetch data from an API
  const stats = {
    totalSubscribers: 2547,
    activeSubscribers: 2103,
    openRate: '28.4%',
    clickRate: '4.8%'
  };

  return (
    <div className="mt-6 space-y-4 px-4">
      <h3 className="text-sm font-medium text-gray-500">Quick Stats</h3>
      <div className="rounded-lg bg-white p-4 shadow">
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-xs text-gray-500">Subscribers</dt>
            <dd className="text-lg font-medium">{stats.totalSubscribers}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Active</dt>
            <dd className="text-lg font-medium">{stats.activeSubscribers}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Open Rate</dt>
            <dd className="text-lg font-medium">{stats.openRate}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Click Rate</dt>
            <dd className="text-lg font-medium">{stats.clickRate}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-200 bg-white">
        <div className="flex h-16 items-center px-6">
          <Link href="/dashboard" className="text-xl font-bold text-blue-600">
            Maily
          </Link>
        </div>

        <DashboardNav />

        <Suspense fallback={<div className="p-4 text-center">Loading stats...</div>}>
          <SidebarStats />
        </Suspense>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
          <h1 className="text-lg font-medium">Dashboard</h1>

          <div className="flex items-center space-x-4">
            <button className="rounded-full bg-blue-100 p-2 text-blue-600">
              <span className="sr-only">Notifications</span>
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>

            <UserProfileDropdown />
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-auto p-6">
          <Suspense fallback={<LoadingSpinner />}>
            {children}
          </Suspense>
        </main>
      </div>
    </div>
  );
}
