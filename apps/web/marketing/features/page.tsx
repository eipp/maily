import { motion } from 'framer-motion';

const features = [
  {
    name: 'AI-Powered Personalization',
    description:
      'Leverage advanced machine learning algorithms to create highly personalized email campaigns that resonate with each subscriber.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
    details: [
      'Dynamic content adaptation based on user behavior',
      'Personalized subject lines and preview text',
      'Smart send-time optimization',
      'Automated content recommendations',
    ],
  },
  {
    name: 'Smart Automation',
    description:
      'Create sophisticated email workflows that automatically engage your audience at the perfect moment.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>
    ),
    details: [
      'Behavior-triggered email sequences',
      'Advanced segmentation rules',
      'A/B testing automation',
      'Intelligent workflow builder',
    ],
  },
  {
    name: 'Advanced Analytics',
    description:
      'Gain deep insights into your campaign performance with comprehensive analytics and reporting tools.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    details: [
      'Real-time performance tracking',
      'Conversion attribution',
      'Engagement metrics analysis',
      'ROI reporting',
    ],
  },
  {
    name: 'List Management',
    description:
      'Efficiently manage and segment your subscriber lists for targeted campaigns and better engagement.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
    details: [
      'Smart list segmentation',
      'Automated list cleaning',
      'Custom fields and tags',
      'Import/export capabilities',
    ],
  },
];

export default function Features() {
  return (
    <div className="bg-white">
      {/* Hero section */}
      <div className="relative bg-primary py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl">
              Powerful Features for Modern Email Marketing
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-xl text-gray-200">
              Everything you need to create, automate, and optimize your email campaigns with
              AI-powered intelligence.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Feature section */}
      <div className="py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="space-y-16">
            {features.map((feature, featureIdx) => (
              <motion.div
                key={feature.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: featureIdx * 0.2 }}
                className={`flex flex-col lg:flex-row ${
                  featureIdx % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
                } items-center gap-12`}
              >
                <div className="flex-1">
                  <div className="flex items-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                      {feature.icon}
                    </div>
                    <h2 className="ml-4 text-3xl font-bold text-gray-900">{feature.name}</h2>
                  </div>
                  <p className="mt-4 text-lg text-gray-500">{feature.description}</p>
                  <ul className="mt-8 space-y-4">
                    {feature.details.map(detail => (
                      <li key={detail} className="flex items-center">
                        <svg
                          className="h-5 w-5 text-accent"
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
                        <span className="ml-3 text-gray-700">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex-1 rounded-lg bg-gray-100 p-8">
                  {/* Placeholder for feature illustration/screenshot */}
                  <div className="aspect-h-9 aspect-w-16 rounded-lg bg-gray-200"></div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA section */}
      <div className="bg-primary">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:flex lg:items-center lg:justify-between lg:px-8 lg:py-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">Ready to get started?</span>
            <span className="block text-accent">Start your free trial today.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-md shadow">
              <a
                href="https://app.justmaily.com/auth/signup"
                className="inline-flex items-center justify-center rounded-md border border-transparent bg-accent px-5 py-3 text-base font-medium text-white hover:bg-accent-dark"
              >
                Get started
              </a>
            </div>
            <div className="ml-3 inline-flex rounded-md shadow">
              <a
                href="/marketing/contact"
                className="inline-flex items-center justify-center rounded-md border border-transparent bg-white px-5 py-3 text-base font-medium text-primary hover:bg-gray-50"
              >
                Learn more
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
