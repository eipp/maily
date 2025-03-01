import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Authentication - Maily',
  description: 'Login or sign up for Maily - AI-powered email marketing platform.',
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col justify-center bg-gray-50 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">Maily</h2>
          <p className="mt-2 text-sm text-gray-600">AI-Powered Email Marketing</p>
        </div>
      </div>
      {children}
    </div>
  );
}
