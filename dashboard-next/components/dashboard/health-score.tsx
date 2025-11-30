import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface HealthScoreProps {
  score?: number;
}

export function HealthScore({ score = 75 }: HealthScoreProps) {
  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-500';
    if (s >= 60) return 'text-yellow-500';
    if (s >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  const getScoreLabel = (s: number) => {
    if (s >= 80) return 'Excellent';
    if (s >= 60) return 'Good';
    if (s >= 40) return 'Fair';
    return 'Needs Attention';
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Code Health Score</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center">
        <div className="relative h-32 w-32">
          {/* Background circle */}
          <svg className="h-full w-full -rotate-90 transform">
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="10"
              fill="none"
              className="text-muted"
            />
            {/* Progress circle */}
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="10"
              fill="none"
              strokeLinecap="round"
              className={getScoreColor(score)}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset,
                transition: 'stroke-dashoffset 0.5s ease',
              }}
            />
          </svg>
          {/* Score text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${getScoreColor(score)}`}>
              {score}
            </span>
            <span className="text-xs text-muted-foreground">/ 100</span>
          </div>
        </div>
        <div className="mt-4 text-center">
          <p className={`text-lg font-semibold ${getScoreColor(score)}`}>
            {getScoreLabel(score)}
          </p>
          <p className="text-sm text-muted-foreground">
            Based on security, quality, and performance metrics
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
