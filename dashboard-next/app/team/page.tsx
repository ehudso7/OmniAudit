import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { UserPlus, Settings, Shield, Users, Mail } from 'lucide-react';

export default function TeamPage() {
  const teamMembers = [
    {
      id: '1',
      name: 'John Smith',
      email: 'john@example.com',
      role: 'admin',
      status: 'active',
      lastActive: '2 minutes ago',
    },
    {
      id: '2',
      name: 'Alice Doe',
      email: 'alice@example.com',
      role: 'developer',
      status: 'active',
      lastActive: '1 hour ago',
    },
    {
      id: '3',
      name: 'Bob Jones',
      email: 'bob@example.com',
      role: 'developer',
      status: 'active',
      lastActive: '3 hours ago',
    },
    {
      id: '4',
      name: 'Carol White',
      email: 'carol@example.com',
      role: 'viewer',
      status: 'pending',
      lastActive: 'Never',
    },
  ];

  const getRoleBadge = (role: string) => {
    const styles: Record<string, string> = {
      admin: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      developer: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
    };
    return <Badge className={styles[role] || styles.viewer}>{role}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Team</h1>
          <p className="text-muted-foreground">
            Manage team members and permissions
          </p>
        </div>
        <Button>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite Member
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Team Size</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{teamMembers.length}</div>
            <p className="text-xs text-muted-foreground">members</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Admins</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {teamMembers.filter((m) => m.role === 'admin').length}
            </div>
            <p className="text-xs text-muted-foreground">with full access</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Today</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">3</div>
            <p className="text-xs text-muted-foreground">online now</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {teamMembers.filter((m) => m.status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">invitations</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>
            Manage access and permissions for your team
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {teamMembers.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                    {member.name
                      .split(' ')
                      .map((n) => n[0])
                      .join('')}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{member.name}</span>
                      {getRoleBadge(member.role)}
                      {member.status === 'pending' && (
                        <Badge variant="outline" className="text-yellow-600">
                          Pending
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{member.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-muted-foreground">
                    {member.lastActive}
                  </span>
                  <Button variant="ghost" size="icon">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Roles & Permissions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                role: 'Admin',
                permissions: ['Full access', 'Manage team', 'Billing', 'API keys'],
              },
              {
                role: 'Developer',
                permissions: ['Run audits', 'View reports', 'Configure rules'],
              },
              {
                role: 'Viewer',
                permissions: ['View reports', 'View dashboard'],
              },
            ].map((item) => (
              <div key={item.role} className="rounded-lg border p-4">
                <h4 className="font-medium">{item.role}</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  {item.permissions.map((perm) => (
                    <Badge key={perm} variant="secondary">
                      {perm}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
