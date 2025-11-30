'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface SeverityChartProps {
  data?: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

const SEVERITY_COLORS = {
  critical: '#DC2626',
  high: '#EA580C',
  medium: '#CA8A04',
  low: '#2563EB',
  info: '#6B7280',
};

export function SeverityChart({ data }: SeverityChartProps) {
  const chartData = [
    { name: 'Critical', value: data?.critical ?? 0, color: SEVERITY_COLORS.critical },
    { name: 'High', value: data?.high ?? 0, color: SEVERITY_COLORS.high },
    { name: 'Medium', value: data?.medium ?? 0, color: SEVERITY_COLORS.medium },
    { name: 'Low', value: data?.low ?? 0, color: SEVERITY_COLORS.low },
    { name: 'Info', value: data?.info ?? 0, color: SEVERITY_COLORS.info },
  ];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Issues by Severity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={80} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
