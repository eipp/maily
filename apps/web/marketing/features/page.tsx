import { MarketingNav } from '@/marketing/components/MarketingNav';
import { MarketingFooter } from '@/marketing/components/MarketingFooter';
import Link from 'next/link';
import { Button } from '@/components/Button';
import Image from 'next/image';

export default function FeaturesPage() {
  const features = [
    {
      id: 'email-marketing',
      title: 'AI-Powered Personalization',
      description:
        'Create highly personalized email campaigns that resonate with your audience. Our AI analyzes recipient behavior and preferences to help you craft messages that drive conversions.',
      image: '/images/feature-personalization.svg',
      imageDescription: 'Personalized email recommendations powered by AI',
      details: [
        'Audience segmentation based on behavior and preferences',
        'Smart content recommendations for each segment',
        'Personalized subject lines that boost open rates',
        'Dynamic content blocks that adapt to user interests',
        'A/B testing with AI-driven analysis',
      ],
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
    },
    {
      id: 'automation',
      title: 'Smart Automation',
      description:
        'Set up intelligent workflows that automatically send the right message at the right time. Our platform handles the repetitive tasks so you can focus on strategy.',
      image: '/images/feature-automation.svg',
      imageDescription: 'Email automation workflow builder',
      details: [
        'Drag-and-drop workflow builder',
        'Trigger-based email sequences',
        'Behavioral automation based on user actions',
        'Time and date-based scheduling',
        'Multi-channel campaign coordination',
      ],
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
    },
    {
      id: 'analytics',
      title: 'Advanced Analytics',
      description:
        'Get deep insights into your campaign performance with our comprehensive analytics dashboard. Understand what works and optimize your strategy in real-time.',
      image: '/images/feature-analytics.svg',
      imageDescription: 'Comprehensive email analytics dashboard',
      details: [
        'Real-time performance tracking',
        'Conversion attribution across campaigns',
        'Subscriber engagement scoring',
        'Revenue and ROI calculation',
        'Predictive performance forecasting',
      ],
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
    },
    {
      id: 'templates',
      title: 'Beautiful Email Templates',
      description:
        'Access a library of professionally designed email templates that are fully customizable and responsive. Create stunning emails without any design skills.',
      image: '/images/feature-templates.svg',
      imageDescription: 'Library of email templates',
      details: [
        'Mobile-responsive design for all devices',
        'Drag-and-drop visual editor',
        'Industry-specific template collections',
        'Custom branding and style settings',
        'HTML code editing for advanced users',
      ],
      icon: (
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
    },
  ];

  return (
    <div className="bg-white">
      <MarketingNav />

      {/* Hero */}
      <div className="relative bg-gradient-to-r from-blue-600 to-indigo-700 pt-16">
        <div className="mx-auto max-w-7xl px-4 pt-16 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl">
              <span className="block">Powerful Features</span>
              <span className="block text-blue-200">for Modern Email Marketing</span>
            </h1>
            <p className="mx-auto mt-3 max-w-md text-base text-gray-300 sm:text-lg md:mt-5 md:max-w-3xl md:text-xl">
              Everything you need to create, automate, and optimize your email campaigns in one platform.
            </p>
          </div>
        </div>
        <div className="h-24 bg-gradient-to-b from-transparent to-white"></div>
      </div>

      {/* Feature List */}
      <div className="py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="space-y-24">
            {features.map((feature, index) => (
              <div 
                key={feature.id} 
                id={feature.id}
                className={`flex flex-col gap-y-10 lg:flex-row lg:items-center lg:gap-x-16 ${
                  index % 2 === 1 ? 'lg:flex-row-reverse' : ''
                }`}
              >
                {/* Image/Icon Placeholder */}
                <div className="relative flex-1 overflow-hidden rounded-xl bg-gradient-to-br from-blue-100 to-indigo-50 p-8">
                  <div className="flex h-64 items-center justify-center">
                    <Image 
                      src={feature.image} 
                      alt={feature.imageDescription} 
                      width={400} 
                      height={300} 
                      className="rounded-lg"
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                    {feature.title}
                  </h2>
                  <p className="mt-4 text-lg text-gray-500">
                    {feature.description}
                  </p>
                  
                  <div className="mt-8">
                    <h3 className="text-lg font-medium text-gray-900">What you'll get:</h3>
                    <ul className="mt-4 space-y-3">
                      {feature.details.map((detail, i) => (
                        <li key={i} className="flex items-start">
                          <div className="flex-shrink-0">
                            <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <p className="ml-3 text-base text-gray-700">{detail}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:flex lg:items-center lg:justify-between lg:px-8 lg:py-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">Ready to get started?</span>
            <span className="block text-blue-200">Try all features with a free trial.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-md shadow">
              <Button variant="primary" size="lg" asChild>
                <Link href="/auth/signup">Get Started</Link>
              </Button>
            </div>
            <div className="ml-3 inline-flex rounded-md shadow">
              <Button variant="outline" size="lg" asChild>
                <Link href="/pricing">View Pricing</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <MarketingFooter />
    </div>
  );
}
