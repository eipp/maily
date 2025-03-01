'use server';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';

interface ChartData {
  date: string;
  value: number;
}

interface DashboardChartsProps {
  type: 'opens' | 'clicks';
}

async function getOpenRateData(): Promise<ChartData[]> {
  // In a real implementation, this would fetch from an API
  await new Promise(resolve => setTimeout(resolve, 1200));

  // Generate dates for the last 30 days
  const data: ChartData[] = [];
  const now = new Date();

  for (let i = 30; i >= 0; i--) {
    const date = new Date();
    date.setDate(now.getDate() - i);

    data.push({
      date: formatDate(date, { month: 'short', day: 'numeric' }),
      value: Math.floor(Math.random() * 30) + 10, // Random value between 10-40%
    });
  }

  return data;
}

async function getClickRateData(): Promise<ChartData[]> {
  // In a real implementation, this would fetch from an API
  await new Promise(resolve => setTimeout(resolve, 1200));

  // Generate dates for the last 30 days
  const data: ChartData[] = [];
  const now = new Date();

  for (let i = 30; i >= 0; i--) {
    const date = new Date();
    date.setDate(now.getDate() - i);

    data.push({
      date: formatDate(date, { month: 'short', day: 'numeric' }),
      value: Math.floor(Math.random() * 8) + 2, // Random value between 2-10%
    });
  }

  return data;
}

export default async function DashboardCharts({ type }: DashboardChartsProps) {
  const data = type === 'opens' ?
    await getOpenRateData() :
    await getClickRateData();

  const maxValue = Math.max(...data.map(d => d.value));
  const title = type === 'opens' ? 'Email Open Rate' : 'Email Click Rate';

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <div className="flex h-full items-end space-x-1">
            {data.map((item, i) => (
              <div
                key={i}
                className="group relative flex h-full w-full flex-col items-center justify-end"
              >
                <div
                  className={`w-full rounded-sm ${
                    type === 'opens' ? 'bg-blue-500' : 'bg-green-500'
                  } transition-all hover:opacity-80`}
                  style={{ height: `${(item.value / maxValue) * 100}%` }}
                >
                  <div className="absolute bottom-full left-1/2 z-10 mb-2 hidden -translate-x-1/2 transform rounded bg-black px-2 py-1 text-xs text-white group-hover:block">
                    {item.value}%
                  </div>
                </div>
                {i % 5 === 0 && (
                  <span className="mt-1 text-xs text-muted-foreground">{item.date}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
