import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, Download, Calendar, Share2 } from 'lucide-react';

export default function ReportsPage() {
  const reports = [
    {
      id: '1',
      title: 'Security Audit Report - Q4 2025',
      type: 'security',
      date: '2025-11-29',
      status: 'complete',
      findings: 23,
      format: 'PDF',
    },
    {
      id: '2',
      title: 'Code Quality Analysis - main-api',
      type: 'quality',
      date: '2025-11-28',
      status: 'complete',
      findings: 45,
      format: 'PDF',
    },
    {
      id: '3',
      title: 'Dependency Vulnerability Scan',
      type: 'dependencies',
      date: '2025-11-27',
      status: 'complete',
      findings: 8,
      format: 'SARIF',
    },
    {
      id: '4',
      title: 'Performance Analysis Report',
      type: 'performance',
      date: '2025-11-26',
      status: 'generating',
      findings: 0,
      format: 'HTML',
    },
  ];

  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      security: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      quality: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      dependencies: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      performance: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    };
    return <Badge className={colors[type]}>{type}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            View and download audit reports
          </p>
        </div>
        <Button>
          <FileText className="mr-2 h-4 w-4" />
          Generate Report
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reports.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Shared</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-start gap-4">
                  <div className="rounded-lg bg-muted p-2">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{report.title}</span>
                      {getTypeBadge(report.type)}
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
                      <div className="flex items-center">
                        <Calendar className="mr-1 h-3 w-3" />
                        {report.date}
                      </div>
                      <span>{report.format}</span>
                      {report.findings > 0 && (
                        <span>{report.findings} findings</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {report.status === 'complete' ? (
                    <>
                      <Button variant="outline" size="sm">
                        <Share2 className="mr-2 h-4 w-4" />
                        Share
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                    </>
                  ) : (
                    <Badge variant="outline">Generating...</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
