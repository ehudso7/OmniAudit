import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn, getSeverityColor, getRelativeTime } from '@/lib/utils';

interface Issue {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  file: string;
  category: string;
  created_at: string;
}

interface TopIssuesProps {
  issues?: Issue[];
}

export function TopIssues({ issues = [] }: TopIssuesProps) {
  const defaultIssues: Issue[] = [
    {
      id: '1',
      title: 'SQL Injection vulnerability',
      severity: 'critical',
      file: 'src/api/users.ts',
      category: 'security',
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: '2',
      title: 'Exposed API key in config',
      severity: 'high',
      file: '.env.example',
      category: 'security',
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: '3',
      title: 'Inefficient database query',
      severity: 'medium',
      file: 'src/services/orders.ts',
      category: 'performance',
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: '4',
      title: 'Missing error handling',
      severity: 'low',
      file: 'src/utils/parser.ts',
      category: 'quality',
      created_at: new Date(Date.now() - 172800000).toISOString(),
    },
  ];

  const displayIssues = issues.length > 0 ? issues : defaultIssues;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Top Issues</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayIssues.slice(0, 5).map((issue) => (
            <div
              key={issue.id}
              className="flex items-start justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-xs font-medium',
                      getSeverityColor(issue.severity),
                    )}
                  >
                    {issue.severity}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {issue.category}
                  </span>
                </div>
                <p className="font-medium text-sm">{issue.title}</p>
                <p className="text-xs text-muted-foreground font-mono">
                  {issue.file}
                </p>
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {getRelativeTime(issue.created_at)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
