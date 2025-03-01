'use client';

import { motion } from 'framer-motion';

const team = [
  {
    name: 'Sarah Johnson',
    role: 'CEO & Co-founder',
    image: '/images/team/sarah.jpg',
    bio: 'Former VP of Marketing at MailChimp with 15+ years of email marketing experience.',
  },
  {
    name: 'David Chen',
    role: 'CTO & Co-founder',
    image: '/images/team/david.jpg',
    bio: 'AI researcher and engineer with previous experience at Google and OpenAI.',
  },
  {
    name: 'Maria Garcia',
    role: 'Head of Product',
    image: '/images/team/maria.jpg',
    bio: 'Product leader focused on creating intuitive and powerful marketing tools.',
  },
  {
    name: 'James Wilson',
    role: 'Head of Customer Success',
    image: '/images/team/james.jpg',
    bio: 'Dedicated to helping customers achieve their email marketing goals.',
  },
];

const values = [
  {
    title: 'Innovation First',
    description:
      "We push the boundaries of what's possible in email marketing through AI and automation.",
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
    title: 'Customer Success',
    description:
      "Your success is our success. We're committed to helping you achieve your marketing goals.",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
        />
      </svg>
    ),
  },
  {
    title: 'Data Privacy',
    description:
      'We treat your data with the utmost respect and maintain the highest security standards.',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    ),
  },
  {
    title: 'Sustainability',
    description:
      "We're committed to reducing our environmental impact and promoting sustainable practices.",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
];

export default function About() {
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
              Our Story
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-xl text-gray-200">
              We're on a mission to revolutionize email marketing through AI-powered personalization
              and automation.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Mission section */}
      <div className="relative overflow-hidden bg-white py-16">
        <div className="relative px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-prose text-lg">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                Our Mission
              </h2>
              <p className="mt-8 text-xl leading-8 text-gray-500">
                Maily was founded in 2023 with a clear vision: to make sophisticated email marketing
                accessible to businesses of all sizes. We believe that every business deserves
                access to advanced AI-powered tools that can help them connect with their audience
                in meaningful ways.
              </p>
              <p className="mt-8 text-xl leading-8 text-gray-500">
                Our platform combines cutting-edge AI technology with intuitive design to help
                marketers create personalized, engaging email campaigns that drive results. We're
                not just another email marketing tool – we're your partner in growth.
              </p>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Values section */}
      <div className="bg-gray-50 py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Our Values</h2>
            <p className="mt-4 text-xl text-gray-500">
              The principles that guide everything we do.
            </p>
          </div>

          <div className="mt-16">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {values.map((value, valueIdx) => (
                <motion.div
                  key={value.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: valueIdx * 0.1 }}
                  className="pt-6"
                >
                  <div className="flow-root rounded-lg bg-white px-6 pb-8">
                    <div className="-mt-6">
                      <div>
                        <span className="inline-flex items-center justify-center rounded-md bg-primary p-3 shadow-lg">
                          {value.icon}
                        </span>
                      </div>
                      <h3 className="mt-8 text-lg font-medium tracking-tight text-gray-900">
                        {value.title}
                      </h3>
                      <p className="mt-5 text-base text-gray-500">{value.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Team section */}
      <div className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Our Team</h2>
            <p className="mt-4 text-xl text-gray-500">Meet the people behind Maily.</p>
          </div>

          <div className="mt-16 grid grid-cols-1 gap-12 lg:grid-cols-4 lg:gap-8">
            {team.map((member, memberIdx) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: memberIdx * 0.1 }}
                className="space-y-4"
              >
                <div className="aspect-h-3 aspect-w-3">
                  <img className="rounded-lg object-cover" src={member.image} alt={member.name} />
                </div>
                <div className="space-y-2">
                  <div className="space-y-1 text-lg font-medium leading-6">
                    <h3 className="text-gray-900">{member.name}</h3>
                    <p className="text-primary">{member.role}</p>
                  </div>
                  <div className="text-base">
                    <p className="text-gray-500">{member.bio}</p>
                  </div>
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
            <span className="block text-accent">Join us in revolutionizing email marketing.</span>
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
                Contact us
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
