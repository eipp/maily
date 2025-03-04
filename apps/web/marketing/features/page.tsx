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
              <span className="relative block">
                <span className="relative z-10 inline-block transform transition-all duration-700 hover:scale-105">Powerful Features</span>
                <svg className="absolute -bottom-2 left-1/2 z-0 h-3 w-24 -translate-x-1/2 text-blue-400 md:-bottom-3 md:w-40" viewBox="0 0 100 12" preserveAspectRatio="none">
                  <path d="M0,0 C20,8 50,12 80,8 L100,0 L100,12 L0,12 Z" fill="currentColor" />
                </svg>
              </span>
              <span className="mt-2 block bg-gradient-to-r from-blue-200 to-indigo-200 bg-clip-text text-transparent transition-all duration-700 hover:from-white hover:to-blue-200">for Modern Email Marketing</span>
            </h1>
            <p className="mx-auto mt-3 max-w-md text-base text-gray-300 sm:text-lg md:mt-5 md:max-w-3xl md:text-xl">
              Everything you need to create, automate, and optimize your email campaigns in one platform.
            </p>
            
            {/* Animated stats for social proof */}
            <div className="mx-auto mt-8 grid max-w-4xl grid-cols-2 gap-8 md:grid-cols-4">
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-white">10k+</div>
                <div className="text-sm text-blue-200">Active Users</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-white">98%</div>
                <div className="text-sm text-blue-200">Deliverability</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-white">45%</div>
                <div className="text-sm text-blue-200">Avg. Open Rate</div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-white">24/7</div>
                <div className="text-sm text-blue-200">Support</div>
              </div>
            </div>
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
                {/* Enhanced image presentation with optimizations */}
                <div className="relative flex-1 overflow-hidden rounded-xl bg-gradient-to-br from-blue-100 to-indigo-50 p-8 shadow-xl shadow-blue-100/30 dark:shadow-indigo-900/10 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-200/40">
                  <div className="flex h-64 items-center justify-center">
                    <div className="relative transform transition-transform duration-500 hover:scale-105">
                      <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-primary-600 to-indigo-600 opacity-30 blur-lg"></div>
                      <Image 
                        src={feature.image} 
                        alt={feature.imageDescription} 
                        width={400} 
                        height={300}
                        loading={index === 0 ? "eager" : "lazy"} 
                        sizes="(max-width: 768px) 100vw, 50vw"
                        className="rounded-lg shadow-md relative z-10"
                        priority={index === 0}
                      />
                    </div>
                  </div>
                  {/* Feature icon floating element */}
                  <div className="absolute -right-2 -top-2 rounded-full bg-white p-2 shadow-lg dark:bg-gray-800">
                    <div className="rounded-full bg-gradient-to-br from-primary-500 to-indigo-600 p-2 text-white">
                      {feature.icon}
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="space-y-4">
                    <h2 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 sm:text-4xl">
                      {feature.title}
                    </h2>
                    <div className="h-1 w-20 rounded-full bg-gradient-to-r from-primary-500 to-indigo-500"></div>
                  </div>
                  <p className="mt-4 text-lg text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                  
                  <div className="mt-10">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">What you'll get:</h3>
                    <ul className="mt-6 space-y-5">
                      {feature.details.map((detail, i) => (
                        <li key={i} className="flex items-start transition-all duration-300 hover:translate-x-1">
                          <div className="flex-shrink-0">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-100 text-primary-600 dark:bg-primary-900/50 dark:text-primary-400">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          </div>
                          <p className="ml-3 text-base font-medium text-gray-700 dark:text-gray-300">{detail}</p>
                        </li>
                      ))}
                    </ul>
                    
                    {/* Feature CTA */}
                    <div className="mt-8">
                      <Button variant="outline" size="sm" className="group" asChild>
                        <Link href="/auth/signup">
                          <span className="flex items-center">
                            Try it now
                            <svg className="ml-2 h-4 w-4 transform transition-transform duration-300 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                          </span>
                        </Link>
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Enhanced CTA Section with visual elements */}
      <div className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 z-0">
          <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-blue-600 opacity-20 blur-3xl"></div>
          <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-indigo-600 opacity-20 blur-3xl"></div>
        </div>
        
        {/* Main content */}
        <div className="relative z-10 bg-gradient-to-r from-blue-600 to-indigo-700">
          <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:flex lg:items-center lg:justify-between lg:px-8 lg:py-20">
            <div className="lg:max-w-2xl">
              <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl lg:text-5xl">
                <span className="block">Ready to get started?</span>
                <span className="mt-2 block bg-gradient-to-r from-blue-200 to-indigo-200 bg-clip-text text-transparent">
                  Try all features with a free trial.
                </span>
              </h2>
              <p className="mt-4 max-w-lg text-lg text-blue-100">
                Join thousands of marketers who've already upgraded their email strategy. No credit card required.
              </p>
              
              {/* Social proof */}
              <div className="mt-8 flex items-center">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="inline-block h-8 w-8 rounded-full bg-blue-300/90 ring-2 ring-white"></div>
                  ))}
                </div>
                <p className="ml-4 text-sm font-medium text-blue-100">Join 10,000+ satisfied customers</p>
              </div>
            </div>
            
            <div className="mt-10 flex flex-col space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0 lg:mt-0 lg:flex-shrink-0">
              <Button 
                variant="primary" 
                size="lg" 
                asChild
                className="group relative overflow-hidden bg-white text-blue-600 shadow-xl transition-transform duration-300 hover:-translate-y-1 hover:shadow-2xl"
              >
                <Link href="/auth/signup">
                  <span className="relative z-10 flex items-center font-semibold">
                    Get Started Free
                    <svg className="ml-2 h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </span>
                </Link>
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                asChild
                className="border-white/80 text-white transition-all duration-300 hover:bg-white hover:text-blue-600"
              >
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
