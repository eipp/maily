import { executeQuery } from '@/lib/apollo-server';
import { GET_CAMPAIGN_STATS } from '@/graphql/queries';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface CampaignStatsProps {
  id: string;
}

interface DailyStats {
  date: string;
  opens: number;
  clicks: number;
}

interface DeviceStats {
  device: string;
  count: number;
}

interface LocationStats {
  country: string;
  count: number;
}

interface CampaignStatsData {
  campaignStats: {
    dailyStats: DailyStats[];
    deviceStats: DeviceStats[];
    locationStats: LocationStats[];
    linkStats: {
      url: string;
      clicks: number;
    }[];
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28AFF'];

export async function CampaignStats({ id }: CampaignStatsProps) {
  try {
    const data = await executeQuery<CampaignStatsData>(GET_CAMPAIGN_STATS, { id });
    const stats = data.campaignStats;

    if (!stats) {
      return <div className="text-center py-8">No statistics available for this campaign yet.</div>;
    }

    // Transform data for pie chart
    const deviceData = stats.deviceStats.map((item, index) => ({
      ...item,
      color: COLORS[index % COLORS.length],
    }));

    const totalDeviceCount = deviceData.reduce((sum, item) => sum + item.count, 0);

    return (
      <div className="space-y-8">
        {/* Opens and Clicks Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Over Time</CardTitle>
            <CardDescription>Daily opens and clicks after sending the campaign</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stats.dailyStats}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="opens" fill="#0088FE" name="Opens" />
                  <Bar dataKey="clicks" fill="#00C49F" name="Clicks" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Devices and Locations */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Device Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Device Breakdown</CardTitle>
              <CardDescription>Opens by device type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row items-center justify-center gap-8">
                <div className="h-[200px] w-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={deviceData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="count"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {deviceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {deviceData.map((device, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: device.color }}
                      />
                      <span className="text-sm">{device.device}</span>
                      <span className="text-sm text-muted-foreground ml-auto">
                        {((device.count / totalDeviceCount) * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Top Locations */}
          <Card>
            <CardHeader>
              <CardTitle>Top Locations</CardTitle>
              <CardDescription>Opens by country</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.locationStats.slice(0, 5).map((location, index) => (
                  <div key={index} className="flex items-center">
                    <span className="text-sm font-medium">{location.country}</span>
                    <div className="mx-4 flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${(location.count / stats.locationStats[0].count) * 100}%`
                        }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {location.count} opens
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Link Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Link Performance</CardTitle>
            <CardDescription>Click rates for links in your campaign</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.linkStats.map((link, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate max-w-[70%]">{link.url}</span>
                    <span className="text-sm text-muted-foreground">{link.clicks} clicks</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary"
                      style={{
                        width: `${(link.clicks / Math.max(...stats.linkStats.map(l => l.clicks))) * 100}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch campaign stats:', error);
    return (
      <div className="text-center py-8 text-destructive">
        Error loading campaign statistics. Please try again later.
      </div>
    );
  }
}
