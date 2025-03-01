'use client';

import { useState } from 'react';
import { Metadata } from 'next';
import Link from 'next/link';
import { SignupForm } from '../components/SignupForm';

export const metadata: Metadata = {
  title: 'Sign Up | Maily',
  description: 'Create your Maily account and start optimizing your email marketing campaigns.',
};

export default function Signup() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      // TODO: Implement signup logic
      console.log('Signup attempt with:', { email: formData.email, name: formData.name });
    } catch (err) {
      setError('Failed to create account. Please try again.');
    } finally {
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
