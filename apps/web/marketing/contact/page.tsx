'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

type ContactFormData = {
  name: string;
  email: string;
  company: string;
  subject: string;
  message: string;
};

const contactMethods = [
  {
    name: 'Sales',
    description: 'Questions about our plans and pricing',
    email: 'sales@justmaily.com',
    phone: '+1 (555) 123-4567',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    name: 'Support',
    description: 'Get help with your account or campaigns',
    email: 'support@justmaily.com',
    phone: '+1 (555) 234-5678',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    ),
  },
  {
    name: 'Press',
    description: 'Media inquiries and press kit requests',
    email: 'press@justmaily.com',
    phone: '+1 (555) 345-6789',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H14"
        />
      </svg>
    ),
  },
];

export default function Contact() {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'success' | 'error' | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to submit contact form');
      }
      
      setSubmitStatus('success');
      setFormData({
        name: '',
        email: '',
        company: '',
        subject: '',
        message: '',
      });
    } catch (error) {
      console.error('Form submission error:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white">
      {/* Hero section */}
      <div className="relative bg-primary">
        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Get in Touch
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-xl text-gray-200">
              Have questions? We're here to help. Choose the best way to reach us below.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Contact methods section */}
      <div className="bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-3">
            {contactMethods.map((method, methodIdx) => (
              <motion.div
                key={method.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: methodIdx * 0.1 }}
                className="flex flex-col rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
              >
                <div className="flex items-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                    {method.icon}
                  </div>
                  <h3 className="ml-4 text-xl font-semibold text-gray-900">{method.name}</h3>
                </div>
                <p className="mt-4 text-gray-500">{method.description}</p>
                <dl className="mt-8 space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Email</dt>
                    <dd className="mt-1">
                      <a
                        href={`mailto:${method.email}`}
                        className="text-primary hover:text-primary-dark"
                      >
                        {method.email}
                      </a>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Phone</dt>
                    <dd className="mt-1">
                      <a
                        href={`tel:${method.phone}`}
                        className="text-primary hover:text-primary-dark"
                      >
                        {method.phone}
                      </a>
                    </dd>
                  </div>
                </dl>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Contact form section */}
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="relative bg-white shadow-xl">
          <div className="grid grid-cols-1 lg:grid-cols-3">
            {/* Contact information */}
            <div className="relative overflow-hidden bg-primary px-6 py-10 sm:px-10 xl:p-12">
              <div className="pointer-events-none absolute inset-0 sm:hidden" aria-hidden="true">
                <svg
                  className="absolute inset-0 h-full w-full"
                  width={343}
                  height={388}
                  viewBox="0 0 343 388"
                  fill="none"
                  preserveAspectRatio="xMidYMid slice"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M-99 461.107L608.107-246l707.103 707.107-707.103 707.103L-99 461.107z"
                    fill="url(#linear1)"
                    fillOpacity=".1"
                  />
                  <defs>
                    <linearGradient
                      id="linear1"
                      x1="254.553"
                      y1="107.554"
                      x2="961.66"
                      y2="814.66"
                      gradientUnits="userSpaceOnUse"
                    >
                      <stop stopColor="#fff" />
                      <stop offset={1} stopColor="#fff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div
                className="pointer-events-none absolute bottom-0 right-0 top-0 hidden w-1/2 sm:block lg:hidden"
                aria-hidden="true"
              >
                <svg
                  className="absolute inset-0 h-full w-full"
                  width={359}
                  height={339}
                  viewBox="0 0 359 339"
                  fill="none"
                  preserveAspectRatio="xMidYMid slice"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M-161 382.107L546.107-325l707.103 707.107-707.103 707.103L-161 382.107z"
                    fill="url(#linear2)"
                    fillOpacity=".1"
                  />
                  <defs>
                    <linearGradient
                      id="linear2"
                      x1="192.553"
                      y1="28.553"
                      x2="899.66"
                      y2="735.66"
                      gradientUnits="userSpaceOnUse"
                    >
                      <stop stopColor="#fff" />
                      <stop offset={1} stopColor="#fff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div
                className="pointer-events-none absolute bottom-0 right-0 top-0 hidden w-1/2 lg:block"
                aria-hidden="true"
              >
                <svg
                  className="absolute inset-0 h-full w-full"
                  width={160}
                  height={678}
                  viewBox="0 0 160 678"
                  fill="none"
                  preserveAspectRatio="xMidYMid slice"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M-161 679.107L546.107-28l707.103 707.107-707.103 707.103L-161 679.107z"
                    fill="url(#linear3)"
                    fillOpacity=".1"
                  />
                  <defs>
                    <linearGradient
                      id="linear3"
                      x1="192.553"
                      y1="325.553"
                      x2="899.66"
                      y2="1032.66"
                      gradientUnits="userSpaceOnUse"
                    >
                      <stop stopColor="#fff" />
                      <stop offset={1} stopColor="#fff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white">Contact Information</h3>
              <p className="mt-6 max-w-3xl text-base text-primary-100">
                Fill out the form and our team will get back to you within 24 hours.
              </p>
              <dl className="mt-8 space-y-6">
                <dt>
                  <span className="sr-only">Address</span>
                </dt>
                <dd className="flex text-base text-primary-100">
                  <svg
                    className="text-primary-200 h-6 w-6 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span className="ml-3">123 Market Street, San Francisco, CA 94105</span>
                </dd>
                <dt>
                  <span className="sr-only">Phone number</span>
                </dt>
                <dd className="flex text-base text-primary-100">
                  <svg
                    className="text-primary-200 h-6 w-6 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                    />
                  </svg>
                  <span className="ml-3">+1 (555) 123-4567</span>
                </dd>
                <dt>
                  <span className="sr-only">Email</span>
                </dt>
                <dd className="flex text-base text-primary-100">
                  <svg
                    className="text-primary-200 h-6 w-6 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  <span className="ml-3">contact@justmaily.com</span>
                </dd>
              </dl>
            </div>

            {/* Contact form */}
            <div className="px-6 py-10 sm:px-10 lg:col-span-2 xl:p-12">
              <h3 className="text-lg font-medium text-gray-900">Send us a message</h3>
              <form
                onSubmit={handleSubmit}
                className="mt-6 grid grid-cols-1 gap-y-6 sm:grid-cols-2 sm:gap-x-8"
              >
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-900">
                    Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="name"
                      id="name"
                      autoComplete="name"
                      required
                      value={formData.name}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-primary focus:ring-primary"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-900">
                    Email
                  </label>
                  <div className="mt-1">
                    <input
                      type="email"
                      name="email"
                      id="email"
                      autoComplete="email"
                      required
                      value={formData.email}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-primary focus:ring-primary"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="company" className="block text-sm font-medium text-gray-900">
                    Company
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="company"
                      id="company"
                      value={formData.company}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-primary focus:ring-primary"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-gray-900">
                    Subject
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="subject"
                      id="subject"
                      required
                      value={formData.subject}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-primary focus:ring-primary"
                    />
                  </div>
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="message" className="block text-sm font-medium text-gray-900">
                    Message
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="message"
                      name="message"
                      rows={4}
                      required
                      value={formData.message}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-primary focus:ring-primary"
                    />
                  </div>
                </div>
                <div className="sm:col-span-2">
                  {submitStatus === 'success' && (
                    <div className="rounded-md bg-green-50 p-4">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg
                            className="h-5 w-5 text-green-400"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-green-800">
                            Message sent successfully! We'll get back to you soon.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  {submitStatus === 'error' && (
                    <div className="rounded-md bg-red-50 p-4">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg
                            className="h-5 w-5 text-red-400"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-red-800">
                            Something went wrong. Please try again.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className={`mt-6 inline-flex w-full items-center justify-center rounded-md border border-transparent bg-primary px-6 py-3 text-base font-medium text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                      isSubmitting ? 'cursor-not-allowed opacity-75' : ''
                    }`}
                  >
                    {isSubmitting ? 'Sending...' : 'Send message'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
