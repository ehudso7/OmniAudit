import { Suspense } from 'react';
import { DashboardStats } from '@/components/dashboard/stats';
import { RecentActivity } from '@/components/dashboard/recent-activity';
import { SeverityChart } from '@/components/dashboard/severity-chart';
import { TopIssues } from '@/components/dashboard/top-issues';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { HealthScore } from '@/components/dashboard/health-score';
import { Skeleton } from '@/components/ui/skeleton';

// Server Component - data fetched on server
async function getDashboardData() {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${apiUrl}/api/v1/dashboard/stats`, {
      next: { revalidate: 60 }, // Cache for 60 seconds
    });

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard data');
    }

    return response.json();
  } catch (error) {
    console.error('Dashboard fetch error:', error);
    return null;
  }
}

export default async function DashboardPage() {
  const data = await getDashboardData();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your code quality and security metrics
          </p>
        </div>
        <QuickActions />
      </div>

      {/* Stats Overview */}
      <Suspense fallback={<StatsLoading />}>
        <DashboardStats data={data?.stats} />
      </Suspense>

      {/* Main Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Health Score */}
        <div className="lg:col-span-1">
          <Suspense fallback={<CardLoading />}>
            <HealthScore score={data?.health_score} />
          </Suspense>
        </div>

        {/* Severity Distribution */}
        <div className="lg:col-span-2">
          <Suspense fallback={<CardLoading />}>
            <SeverityChart data={data?.severity_breakdown} />
          </Suspense>
        </div>
      </div>

      {/* Secondary Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Top Issues */}
        <Suspense fallback={<CardLoading />}>
          <TopIssues issues={data?.top_issues} />
        </Suspense>

        {/* Recent Activity */}
        <Suspense fallback={<CardLoading />}>
          <RecentActivity activities={data?.recent_activity} />
        </Suspense>
      </div>
    </div>
  );
}

function StatsLoading() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} className="h-32 rounded-lg" />
      ))}
    </div>
  );
}

function CardLoading() {
  return <Skeleton className="h-[300px] rounded-lg" />;
}
