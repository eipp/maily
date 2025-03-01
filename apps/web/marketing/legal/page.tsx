import { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Legal Documents | Maily',
  description: 'Legal documents, terms of service, privacy policy, and other policies for Maily.',
};

const legalDocuments = [
  {
    title: 'Terms of Service',
    description: 'The terms and conditions that govern your use of Maily.',
    href: '/legal/terms',
  },
  {
    title: 'Privacy Policy',
    description: 'How we collect, use, and protect your personal information.',
    href: '/legal/privacy',
  },
  {
    title: 'Cookie Policy',
    description: 'Information about how we use cookies and similar technologies.',
    href: '/legal/cookies',
  },
  {
    title: 'GDPR Compliance',
    description: 'Our compliance with EU data protection regulations.',
    href: '/legal/gdpr',
  },
  {
    title: 'Security Policy',
    description: 'How we protect your data and maintain security.',
    href: '/legal/security',
  },
];

export default function LegalPage() {
  return (
    <div className="pt-24">
      <div className="container mx-auto px-4 py-12">
        <h1 className="mb-8 font-heading text-4xl font-bold text-gray-900">Legal Documents</h1>
        <div className="grid gap-6 md:grid-cols-2">
          {legalDocuments.map(doc => (
            <Link
              key={doc.href}
              href={doc.href}
              className="block rounded-lg border border-gray-100 bg-white p-6 shadow-sm transition hover:shadow-md"
            >
              <h2 className="mb-2 font-heading text-xl font-semibold text-gray-900">{doc.title}</h2>
              <p className="text-gray-600">{doc.description}</p>
              <div className="mt-4 font-medium text-primary">Read more →</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
