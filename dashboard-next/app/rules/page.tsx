'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Plus, Settings, CheckCircle, XCircle } from 'lucide-react';

export default function RulesPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const ruleCategories = [
    { id: 'security', name: 'Security', count: 65, color: 'text-red-500' },
    { id: 'quality', name: 'Code Quality', count: 46, color: 'text-blue-500' },
    { id: 'performance', name: 'Performance', count: 34, color: 'text-yellow-500' },
    { id: 'best-practices', name: 'Best Practices', count: 88, color: 'text-green-500' },
  ];

  const rules = [
    {
      id: 'SEC-001',
      name: 'sql-injection',
      title: 'SQL Injection Detection',
      category: 'security',
      severity: 'critical',
      enabled: true,
      description: 'Detects potential SQL injection vulnerabilities',
    },
    {
      id: 'SEC-002',
      name: 'xss-prevention',
      title: 'XSS Prevention',
      category: 'security',
      severity: 'high',
      enabled: true,
      description: 'Identifies cross-site scripting vulnerabilities',
    },
    {
      id: 'PERF-001',
      name: 'n-plus-one',
      title: 'N+1 Query Detection',
      category: 'performance',
      severity: 'medium',
      enabled: true,
      description: 'Finds N+1 query patterns in ORM usage',
    },
    {
      id: 'QUAL-001',
      name: 'cyclomatic-complexity',
      title: 'Cyclomatic Complexity',
      category: 'quality',
      severity: 'low',
      enabled: false,
      description: 'Warns when function complexity exceeds threshold',
    },
  ];

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      low: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    };
    return <Badge className={styles[severity] || styles.low}>{severity}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rules</h1>
          <p className="text-muted-foreground">
            Configure and manage audit rules
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Custom Rule
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {ruleCategories.map((category) => (
          <Card key={category.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">{category.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${category.color}`}>
                {category.count}
              </div>
              <p className="text-xs text-muted-foreground">active rules</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Rules</CardTitle>
              <CardDescription>
                {rules.length} rules configured
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search rules..."
                  className="w-64 pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button variant="outline" size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {rules
              .filter(
                (rule) =>
                  rule.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  rule.name.toLowerCase().includes(searchQuery.toLowerCase()),
              )
              .map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`rounded-full p-1 ${
                        rule.enabled
                          ? 'bg-green-100 text-green-600 dark:bg-green-900/20'
                          : 'bg-gray-100 text-gray-400 dark:bg-gray-900/20'
                      }`}
                    >
                      {rule.enabled ? (
                        <CheckCircle className="h-5 w-5" />
                      ) : (
                        <XCircle className="h-5 w-5" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{rule.title}</span>
                        {getSeverityBadge(rule.severity)}
                        <Badge variant="outline">{rule.category}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {rule.description}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground font-mono">
                        {rule.id}: {rule.name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      Configure
                    </Button>
                    <Button
                      variant={rule.enabled ? 'destructive' : 'default'}
                      size="sm"
                    >
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
