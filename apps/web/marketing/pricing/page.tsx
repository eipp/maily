'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

const plans = [
  {
    name: 'Starter',
    price: {
      monthly: 29,
      yearly: 24,
    },
    description: 'Perfect for small businesses just getting started with email marketing.',
    features: [
      'Up to 5,000 subscribers',
      'Unlimited email sends',
      'Basic AI personalization',
      'Email templates',
      'Basic analytics',
      'Email support',
    ],
    cta: 'Start with Starter',
    popular: false,
  },
  {
    name: 'Professional',
    price: {
      monthly: 79,
      yearly: 69,
    },
    description: 'Advanced features for growing businesses seeking better engagement.',
    features: [
      'Up to 25,000 subscribers',
      'Unlimited email sends',
      'Advanced AI personalization',
      'Custom templates',
      'Advanced analytics',
      'Priority email support',
      'A/B testing',
      'Automation workflows',
      'Team collaboration',
    ],
    cta: 'Go Professional',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: {
      monthly: 199,
      yearly: 179,
    },
    description: 'Custom solutions for large organizations with complex needs.',
    features: [
      'Unlimited subscribers',
      'Unlimited email sends',
      'Enterprise AI features',
      'Custom integrations',
      'Advanced security',
      'Dedicated support',
      'SLA guarantee',
      'Custom reporting',
      'Advanced automation',
      'API access',
    ],
    cta: 'Contact Sales',
    popular: false,
  },
];

export default function Pricing() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <div className="bg-white">
      {/* Header */}
      <div className="relative bg-primary">
        <div className="mx-auto max-w-7xl px-4 pb-16 pt-24 text-center sm:px-6 lg:px-8">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl"
          >
            Simple, Transparent Pricing
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-xl text-gray-200"
          >
            Choose the perfect plan for your business. Save up to 15% with yearly billing.
          </motion.p>

          {/* Billing toggle */}
          <div className="mt-12 flex justify-center">
            <div className="relative flex self-center rounded-lg bg-primary-dark p-0.5 sm:mt-0">
              <button
                type="button"
                onClick={() => setIsYearly(false)}
                className={`${
                  !isYearly ? 'bg-white text-gray-900' : 'text-gray-200'
                } relative whitespace-nowrap rounded-md border-transparent px-6 py-2 text-sm font-medium transition-colors focus:z-10 focus:outline-none sm:w-auto`}
              >
                Monthly billing
              </button>
              <button
                type="button"
                onClick={() => setIsYearly(true)}
                className={`${
                  isYearly ? 'bg-white text-gray-900' : 'text-gray-200'
                } relative ml-0.5 whitespace-nowrap rounded-md border-transparent px-6 py-2 text-sm font-medium transition-colors focus:z-10 focus:outline-none sm:w-auto`}
              >
                Yearly billing
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing section */}
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {plans.map((plan, planIdx) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: planIdx * 0.2 }}
              className={`relative flex flex-col rounded-2xl border ${
                plan.popular ? 'border-primary shadow-xl' : 'border-gray-200'
              } p-8 ${plan.popular ? 'bg-primary/5' : 'bg-white'}`}
            >
              {plan.popular && (
                <div className="absolute right-0 top-0 -translate-y-1/2 translate-x-1/2">
                  <span className="inline-flex rounded-full bg-accent px-4 py-1 text-sm font-semibold text-white">
                    Most popular
                  </span>
                </div>
              )}

              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900">{plan.name}</h3>
                <p className="mt-4 flex items-baseline text-gray-900">
                  <span className="text-5xl font-extrabold tracking-tight">
                    ${isYearly ? plan.price.yearly : plan.price.monthly}
                  </span>
                  <span className="ml-1 text-xl font-semibold">/month</span>
                </p>
                <p className="mt-6 text-gray-500">{plan.description}</p>

                <ul className="mt-6 space-y-4">
                  {plan.features.map(feature => (
                    <li key={feature} className="flex">
                      <svg
                        className="h-6 w-6 flex-shrink-0 text-accent"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span className="ml-3 text-gray-500">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <a
                href={
                  plan.name === 'Enterprise'
                    ? '/marketing/contact'
                    : 'https://app.justmaily.com/auth/signup'
                }
                className={`mt-8 block w-full rounded-md px-6 py-3 text-center text-sm font-medium ${
                  plan.popular
                    ? 'bg-primary text-white hover:bg-primary-dark'
                    : 'bg-primary/10 hover:bg-primary/20 text-primary'
                }`}
              >
                {plan.cta}
              </a>
            </motion.div>
          ))}
        </div>
      </div>

      {/* FAQ section */}
      <div className="bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <h2 className="mb-12 text-center text-3xl font-extrabold text-gray-900">
            Frequently Asked Questions
          </h2>
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Can I change my plan later?</h3>
              <p className="mt-2 text-gray-500">
                Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected
                in your next billing cycle.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                What happens if I exceed my subscriber limit?
              </h3>
              <p className="mt-2 text-gray-500">
                We'll notify you when you're approaching your limit. You can upgrade to a higher
                plan or remove inactive subscribers.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Do you offer a free trial?</h3>
              <p className="mt-2 text-gray-500">
                Yes, all plans come with a 14-day free trial. No credit card required to start.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                What payment methods do you accept?
              </h3>
              <p className="mt-2 text-gray-500">
                We accept all major credit cards, PayPal, and wire transfers for enterprise
                customers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
