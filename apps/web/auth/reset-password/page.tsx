import { Metadata } from 'next';
import Link from 'next/link';
import { ResetPasswordForm } from '../components/ResetPasswordForm';

export const metadata: Metadata = {
  title: 'Reset Password | Maily',
  description: 'Reset your Maily account password.',
};

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center font-heading text-3xl font-bold text-gray-900">
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
            className="text-sm font-medium text-gray-600 transition hover:text-gray-900"
          >
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
