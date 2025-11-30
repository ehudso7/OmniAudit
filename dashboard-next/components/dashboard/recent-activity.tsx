import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getRelativeTime } from '@/lib/utils';
import { GitPullRequest, FileCode, Shield, Check, X } from 'lucide-react';

interface Activity {
  id: string;
  type: 'review' | 'audit' | 'fix' | 'block';
  title: string;
  description: string;
  timestamp: string;
}

interface RecentActivityProps {
  activities?: Activity[];
}

const activityIcons = {
  review: GitPullRequest,
  audit: FileCode,
  fix: Check,
  block: X,
};

const activityColors = {
  review: 'text-blue-500',
  audit: 'text-purple-500',
  fix: 'text-green-500',
  block: 'text-red-500',
};

export function RecentActivity({ activities = [] }: RecentActivityProps) {
  const defaultActivities: Activity[] = [
    {
      id: '1',
      type: 'review',
      title: 'PR #142 reviewed',
      description: 'Added authentication middleware',
      timestamp: new Date(Date.now() - 300000).toISOString(),
    },
    {
      id: '2',
      type: 'block',
      title: 'Merge blocked',
      description: 'Critical security issue in payment.ts',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
    },
    {
      id: '3',
      type: 'audit',
      title: 'Audit completed',
      description: 'main-api repository analyzed',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: '4',
      type: 'fix',
      title: 'Auto-fix applied',
      description: '12 code style issues fixed',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: '5',
      type: 'review',
      title: 'PR #139 approved',
      description: 'Database optimization changes',
      timestamp: new Date(Date.now() - 14400000).toISOString(),
    },
  ];

  const displayActivities = activities.length > 0 ? activities : defaultActivities;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayActivities.slice(0, 5).map((activity) => {
            const Icon = activityIcons[activity.type];
            return (
              <div
                key={activity.id}
                className="flex items-start gap-3"
              >
                <div
                  className={`mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-muted ${activityColors[activity.type]}`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">{activity.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {activity.description}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {getRelativeTime(activity.timestamp)}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
