'use client';

import { useState } from 'react';
import { Metadata } from 'next';
import Link from 'next/link';
import { SignupForm } from '../components/SignupForm';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Sign Up | Maily',
  description: 'Create your Maily account and start optimizing your email marketing campaigns.',
};

export default function Signup() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSocialSignup = async (provider: string) => {
    try {
      setIsLoading(true);
      await signIn(provider, { callbackUrl: '/app/onboarding' });
    } catch (err) {
      setError('Failed to sign up with social provider. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center font-heading text-3xl font-bold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link
              href="/auth/login"
              className="font-medium text-primary transition hover:text-primary-dark"
            >
              Sign in
            </Link>
          </p>
        </div>

        <SignupForm />

        <p className="mt-3 text-center text-xs text-gray-500">
          By signing up, you agree to our{' '}
          <Link href="/legal/terms" className="underline transition hover:text-gray-700">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/legal/privacy" className="underline transition hover:text-gray-700">
            Privacy Policy
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
