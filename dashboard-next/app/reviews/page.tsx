import { Suspense } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { GitPullRequest, Check, X, Clock, MessageSquare } from 'lucide-react';

async function getPRReviews() {
  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  try {
    const response = await fetch(`${apiUrl}/api/v1/reviews`, {
      next: { revalidate: 30 },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function ReviewsPage() {
  const reviews = await getPRReviews();

  const defaultReviews = [
    {
      id: 'pr-142',
      title: 'Add user authentication middleware',
      repo: 'main-api',
      author: 'jsmith',
      status: 'approved',
      issues: 0,
      comments: 3,
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 'pr-141',
      title: 'Fix payment processing bug',
      repo: 'main-api',
      author: 'adoe',
      status: 'changes_requested',
      issues: 2,
      comments: 5,
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: 'pr-140',
      title: 'Update database schema',
      repo: 'db-migrations',
      author: 'bjones',
      status: 'pending',
      issues: 0,
      comments: 1,
      created_at: new Date(Date.now() - 14400000).toISOString(),
    },
  ];

  const displayReviews = reviews?.data || defaultReviews;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            <Check className="mr-1 h-3 w-3" /> Approved
          </Badge>
        );
      case 'changes_requested':
        return (
          <Badge className="bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
            <X className="mr-1 h-3 w-3" /> Changes Requested
          </Badge>
        );
      default:
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
            <Clock className="mr-1 h-3 w-3" /> Pending
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PR Reviews</h1>
          <p className="text-muted-foreground">
            Manage and track pull request reviews
          </p>
        </div>
        <Button>
          <GitPullRequest className="mr-2 h-4 w-4" />
          Sync PRs
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Reviews</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{displayReviews.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {displayReviews.filter((r: any) => r.status === 'approved').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {displayReviews.filter((r: any) => r.status === 'pending').length}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Pull Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {displayReviews.map((review: any) => (
              <div
                key={review.id}
                className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-start gap-4">
                  <GitPullRequest className="mt-1 h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{review.title}</span>
                      {getStatusBadge(review.status)}
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
                      <span>{review.repo}</span>
                      <span>#{review.id.replace('pr-', '')}</span>
                      <span>by {review.author}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {review.issues > 0 && (
                    <span className="text-sm text-red-600">
                      {review.issues} issues
                    </span>
                  )}
                  <div className="flex items-center text-sm text-muted-foreground">
                    <MessageSquare className="mr-1 h-4 w-4" />
                    {review.comments}
                  </div>
                  <Button variant="outline" size="sm">
                    View
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
