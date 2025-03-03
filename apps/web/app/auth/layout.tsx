import { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Authentication - Maily',
  description: 'Authentication pages for Maily',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="flex justify-center">
            <Link href="/" className="flex items-center">
              <Image
                src="/images/logo.svg"
                alt="Maily Logo"
                width={48}
                height={48}
                className="h-12 w-auto"
              />
              <span className="ml-2 text-2xl font-bold text-gray-900">Maily</span>
            </Link>
          </div>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            {children}
          </div>
        </div>
      </div>
      
      <footer className="bg-white">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center space-x-6">
            <Link href="/privacy" className="text-gray-500 hover:text-gray-900">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-gray-500 hover:text-gray-900">
              Terms of Service
            </Link>
            <Link href="/contact" className="text-gray-500 hover:text-gray-900">
              Contact Us
            </Link>
          </div>
          <div className="mt-4 text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} Maily. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
