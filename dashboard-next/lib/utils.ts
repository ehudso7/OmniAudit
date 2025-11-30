import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export function getRelativeTime(date: Date | string): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString();
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-600 bg-red-100 dark:bg-red-900/20',
    high: 'text-orange-600 bg-orange-100 dark:bg-orange-900/20',
    medium: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20',
    low: 'text-blue-600 bg-blue-100 dark:bg-blue-900/20',
    info: 'text-gray-600 bg-gray-100 dark:bg-gray-900/20',
  };
  return colors[severity] || colors.info;
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    security: 'shield',
    performance: 'zap',
    quality: 'check-circle',
    accessibility: 'eye',
    'best-practices': 'star',
    maintainability: 'tool',
  };
  return icons[category] || 'file';
}
