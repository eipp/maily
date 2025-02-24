import { Metadata } from 'next';
import Link from 'next/link';
import { ResetPasswordForm } from '../components/ResetPasswordForm';

export const metadata: Metadata = {
  title: 'Reset Password | Maily',
  description: 'Reset your Maily account password.',
};

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-heading font-bold text-gray-900">
            Reset your password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>

        <ResetPasswordForm />

        <div className="text-center">
          <Link
            href="/auth/login"
            className="font-medium text-sm text-gray-600 hover:text-gray-900 transition"
          >
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
} 