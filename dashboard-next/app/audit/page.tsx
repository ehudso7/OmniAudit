'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Play, Folder, GitBranch, Shield, Zap, FileCode, Settings } from 'lucide-react';

export default function AuditPage() {
  const [projectPath, setProjectPath] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [selectedAnalyzers, setSelectedAnalyzers] = useState<string[]>([
    'security',
    'quality',
    'performance',
  ]);

  const analyzers = [
    { id: 'security', name: 'Security', icon: Shield, description: 'Detect vulnerabilities and security issues' },
    { id: 'quality', name: 'Code Quality', icon: FileCode, description: 'Check code style and best practices' },
    { id: 'performance', name: 'Performance', icon: Zap, description: 'Find performance bottlenecks' },
    { id: 'dependencies', name: 'Dependencies', icon: GitBranch, description: 'Scan for vulnerable dependencies' },
  ];

  const toggleAnalyzer = (id: string) => {
    setSelectedAnalyzers((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id],
    );
  };

  const startAudit = async () => {
    setIsRunning(true);
    // Simulate audit
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setIsRunning(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Run Audit</h1>
          <p className="text-muted-foreground">
            Analyze your codebase for security, quality, and performance issues
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Project Configuration</CardTitle>
              <CardDescription>
                Specify the project path or repository to analyze
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Folder className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="/path/to/project or https://github.com/org/repo"
                    className="pl-10"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                  />
                </div>
                <Button variant="outline">Browse</Button>
              </div>

              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GitBranch className="h-4 w-4" />
                <span>Branch: main</span>
                <Button variant="link" size="sm" className="h-auto p-0">
                  Change
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Select Analyzers</CardTitle>
              <CardDescription>
                Choose which analyzers to run during the audit
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {analyzers.map((analyzer) => (
                  <div
                    key={analyzer.id}
                    onClick={() => toggleAnalyzer(analyzer.id)}
                    className={`cursor-pointer rounded-lg border p-4 transition-colors ${
                      selectedAnalyzers.includes(analyzer.id)
                        ? 'border-primary bg-primary/5'
                        : 'hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`rounded-lg p-2 ${
                          selectedAnalyzers.includes(analyzer.id)
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <analyzer.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-medium">{analyzer.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {analyzer.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Audit Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Analyzers</span>
                <Badge variant="secondary">{selectedAnalyzers.length} selected</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Est. Time</span>
                <span className="text-sm font-medium">~2 minutes</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Rules</span>
                <span className="text-sm font-medium">233 active</span>
              </div>

              <div className="pt-4">
                <Button
                  className="w-full"
                  size="lg"
                  onClick={startAudit}
                  disabled={isRunning || !projectPath}
                >
                  {isRunning ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Running Audit...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Audit
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Settings className="mr-2 h-4 w-4" />
                Configure Rules
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <FileCode className="mr-2 h-4 w-4" />
                View Last Report
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
