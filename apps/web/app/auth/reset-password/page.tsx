import { Metadata } from 'next';
import Link from 'next/link';
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '../../api/auth/[...nextauth]/route';
import ResetPasswordForm from './reset-password-form';

export const metadata: Metadata = {
  title: 'Reset Password - Maily',
  description: 'Reset your Maily account password',
};

export default async function ResetPasswordPage() {
  const session = await getServerSession(authOptions);

  // Redirect to dashboard if already signed in
  if (session) {
    redirect('/dashboard');
  }

  return (
    <div>
      <h2 className="mt-2 text-center text-3xl font-bold tracking-tight text-gray-900">
        Reset your password
      </h2>
      <p className="mt-2 text-center text-sm text-gray-600">
        Enter your email address and we&apos;ll send you a link to reset your password.
      </p>

      <div className="mt-8">
        <ResetPasswordForm />

        <div className="mt-6 text-center">
          <Link
            href="/auth/signin"
            className="font-medium text-indigo-600 hover:text-indigo-500"
          >
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
