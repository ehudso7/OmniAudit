import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, ExternalLink, Settings } from 'lucide-react';

export default function IntegrationsPage() {
  const integrations = [
    {
      id: 'github',
      name: 'GitHub',
      description: 'Connect repositories and enable PR reviews',
      icon: '/icons/github.svg',
      connected: true,
      status: 'active',
    },
    {
      id: 'gitlab',
      name: 'GitLab',
      description: 'Integrate with GitLab CI/CD pipelines',
      icon: '/icons/gitlab.svg',
      connected: false,
      status: 'available',
    },
    {
      id: 'slack',
      name: 'Slack',
      description: 'Get notifications and alerts in Slack',
      icon: '/icons/slack.svg',
      connected: true,
      status: 'active',
    },
    {
      id: 'jira',
      name: 'Jira',
      description: 'Create issues automatically from findings',
      icon: '/icons/jira.svg',
      connected: false,
      status: 'available',
    },
    {
      id: 'vscode',
      name: 'VS Code',
      description: 'Real-time analysis in your editor',
      icon: '/icons/vscode.svg',
      connected: true,
      status: 'active',
    },
    {
      id: 'jenkins',
      name: 'Jenkins',
      description: 'Integrate with Jenkins pipelines',
      icon: '/icons/jenkins.svg',
      connected: false,
      status: 'available',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
          <p className="text-muted-foreground">
            Connect OmniAudit with your favorite tools
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Connected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {integrations.filter((i) => i.connected).length}
            </div>
            <p className="text-xs text-muted-foreground">active integrations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Available</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {integrations.filter((i) => !i.connected).length}
            </div>
            <p className="text-xs text-muted-foreground">ready to connect</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">API Calls Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">across all integrations</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {integrations.map((integration) => (
          <Card key={integration.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted text-2xl">
                    {integration.name.charAt(0)}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{integration.name}</CardTitle>
                    {integration.connected && (
                      <Badge className="mt-1 bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                        <Check className="mr-1 h-3 w-3" />
                        Connected
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="mb-4">
                {integration.description}
              </CardDescription>
              <div className="flex items-center gap-2">
                {integration.connected ? (
                  <>
                    <Button variant="outline" size="sm">
                      <Settings className="mr-2 h-4 w-4" />
                      Configure
                    </Button>
                    <Button variant="ghost" size="sm">
                      Disconnect
                    </Button>
                  </>
                ) : (
                  <Button size="sm">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Connect
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Webhooks</CardTitle>
          <CardDescription>
            Set up webhooks to receive real-time notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <p className="font-medium">Audit Completed</p>
                <p className="text-sm text-muted-foreground font-mono">
                  https://api.example.com/webhook/audit
                </p>
              </div>
              <Badge variant="outline">Active</Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div>
                <p className="font-medium">Critical Finding</p>
                <p className="text-sm text-muted-foreground font-mono">
                  https://api.example.com/webhook/security
                </p>
              </div>
              <Badge variant="outline">Active</Badge>
            </div>
            <Button variant="outline">
              Add Webhook
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
