'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [period, setPeriod] = useState('7d');

  const stats = [
    {
      name: 'Total Subscribers',
      value: '12,345',
      change: '+8.2%',
      changeType: 'increase',
    },
    {
      name: 'Open Rate',
      value: '58.3%',
      change: '+5.4%',
      changeType: 'increase',
    },
    {
      name: 'Click Rate',
      value: '24.5%',
      change: '-2.1%',
      changeType: 'decrease',
    },
    {
      name: 'Campaigns Sent',
      value: '156',
      change: '+12.5%',
      changeType: 'increase',
    },
  ];

  const recentCampaigns = [
    {
      id: 1,
      name: 'Summer Sale Newsletter',
      status: 'Sent',
      date: '2024-02-24',
      opens: '2,345',
      clicks: '456',
    },
    {
      id: 2,
      name: 'Product Launch Announcement',
      status: 'Scheduled',
      date: '2024-02-26',
      opens: '-',
      clicks: '-',
    },
    {
      id: 3,
      name: 'Monthly Newsletter',
      status: 'Draft',
      date: '-',
      opens: '-',
      clicks: '-',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <Link
          href="/dashboard/campaigns/new"
          className="inline-flex items-center rounded-md border border-transparent bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          Create Campaign
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(stat => (
          <div key={stat.name} className="overflow-hidden rounded-lg bg-white shadow">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="truncate text-sm font-medium text-gray-500">{stat.name}</div>
                  <div className="mt-1 text-3xl font-semibold text-gray-900">{stat.value}</div>
                </div>
                <div className="ml-auto">
                  <span
                    className={`inline-flex items-baseline rounded-full px-2.5 py-0.5 text-sm font-medium ${
                      stat.changeType === 'increase'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {stat.change}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent campaigns */}
      <div className="rounded-lg bg-white shadow">
        <div className="flex items-center justify-between px-4 py-5 sm:px-6">
          <h2 className="text-lg font-medium text-gray-900">Recent Campaigns</h2>
          <div className="flex space-x-2">
            {['7d', '30d', '90d'].map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`rounded-md px-3 py-1 text-sm font-medium ${
                  period === p ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div className="border-t border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Opens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Clicks
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {recentCampaigns.map(campaign => (
                  <tr key={campaign.id}>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{campaign.name}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          campaign.status === 'Sent'
                            ? 'bg-green-100 text-green-800'
                            : campaign.status === 'Scheduled'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {campaign.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {campaign.date}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {campaign.opens}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {campaign.clicks}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="px-4 py-4 sm:px-6">
          <Link
            href="/dashboard/campaigns"
            className="text-sm font-medium text-primary hover:text-primary-dark"
          >
            View all campaigns →
          </Link>
        </div>
      </div>
    </div>
  );
}
