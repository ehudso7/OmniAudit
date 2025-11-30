import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Shield, AlertTriangle, Lock, Key, Bug, RefreshCw } from 'lucide-react';

export default function SecurityPage() {
  const vulnerabilities = [
    {
      id: 'CVE-2024-1234',
      title: 'SQL Injection in User Query',
      severity: 'critical',
      file: 'src/api/users.ts',
      line: 42,
      status: 'open',
    },
    {
      id: 'CVE-2024-5678',
      title: 'XSS in Comment Rendering',
      severity: 'high',
      file: 'src/components/Comments.tsx',
      line: 89,
      status: 'open',
    },
    {
      id: 'SEC-001',
      title: 'Weak Password Policy',
      severity: 'medium',
      file: 'src/auth/validation.ts',
      line: 15,
      status: 'fixed',
    },
  ];

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-600 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-black',
      low: 'bg-blue-500 text-white',
    };
    return <Badge className={styles[severity]}>{severity.toUpperCase()}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Security</h1>
          <p className="text-muted-foreground">
            Monitor and manage security vulnerabilities
          </p>
        </div>
        <Button>
          <RefreshCw className="mr-2 h-4 w-4" />
          Run Security Scan
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">3</div>
            <p className="text-xs text-muted-foreground">Require immediate action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High</CardTitle>
            <Shield className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">7</div>
            <p className="text-xs text-muted-foreground">Should be addressed soon</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Medium</CardTitle>
            <Bug className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">12</div>
            <p className="text-xs text-muted-foreground">Plan to fix</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <Lock className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">45</div>
            <p className="text-xs text-muted-foreground">Fixed this month</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Vulnerabilities</CardTitle>
            <CardDescription>
              Issues requiring immediate attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {vulnerabilities
                .filter((v) => v.status === 'open')
                .map((vuln) => (
                  <div
                    key={vuln.id}
                    className="rounded-lg border p-4 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          {getSeverityBadge(vuln.severity)}
                          <span className="text-sm text-muted-foreground">
                            {vuln.id}
                          </span>
                        </div>
                        <p className="font-medium">{vuln.title}</p>
                        <p className="text-sm text-muted-foreground font-mono">
                          {vuln.file}:{vuln.line}
                        </p>
                      </div>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Security Score</CardTitle>
            <CardDescription>
              Overall security posture
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center pt-6">
            <div className="relative h-40 w-40">
              <svg className="h-full w-full -rotate-90 transform">
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  className="text-muted"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="none"
                  strokeLinecap="round"
                  className="text-green-500"
                  style={{
                    strokeDasharray: 2 * Math.PI * 70,
                    strokeDashoffset: 2 * Math.PI * 70 * 0.22,
                  }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-bold">78</span>
                <span className="text-sm text-muted-foreground">/ 100</span>
              </div>
            </div>
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Your security score is Good. Fix critical issues to improve.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>OWASP Top 10 Coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {[
              'Injection',
              'Broken Auth',
              'Sensitive Data',
              'XXE',
              'Access Control',
              'Misconfiguration',
              'XSS',
              'Deserialization',
              'Components',
              'Logging',
            ].map((item, i) => (
              <div
                key={item}
                className="rounded-lg border p-3 text-center transition-colors hover:bg-muted/50"
              >
                <div className="text-xs text-muted-foreground">A{i + 1}</div>
                <div className="font-medium text-sm mt-1">{item}</div>
                <div className="mt-2">
                  <Badge variant={i < 3 ? 'default' : 'secondary'}>
                    {i < 3 ? 'Protected' : 'Check'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
