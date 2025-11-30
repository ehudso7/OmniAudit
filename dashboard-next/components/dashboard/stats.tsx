import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileCode, Bug, Shield, Zap } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

interface StatsProps {
  data?: {
    total_reviews: number;
    issues_found: number;
    security_blocked: number;
    performance_issues: number;
  };
}

export function DashboardStats({ data }: StatsProps) {
  const stats = [
    {
      title: 'Total Reviews',
      value: data?.total_reviews ?? 0,
      icon: FileCode,
      description: 'Code reviews completed',
      trend: '+12%',
      trendUp: true,
    },
    {
      title: 'Issues Found',
      value: data?.issues_found ?? 0,
      icon: Bug,
      description: 'Total issues detected',
      trend: '-8%',
      trendUp: false,
    },
    {
      title: 'Security Blocked',
      value: data?.security_blocked ?? 0,
      icon: Shield,
      description: 'Security vulnerabilities caught',
      trend: '+23%',
      trendUp: true,
    },
    {
      title: 'Performance Issues',
      value: data?.performance_issues ?? 0,
      icon: Zap,
      description: 'Performance problems identified',
      trend: '-15%',
      trendUp: false,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stat.value)}</div>
            <p className="text-xs text-muted-foreground">
              {stat.description}
            </p>
            <div className="mt-2 flex items-center text-xs">
              <span
                className={
                  stat.trendUp ? 'text-green-600' : 'text-red-600'
                }
              >
                {stat.trend}
              </span>
              <span className="ml-1 text-muted-foreground">from last month</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
