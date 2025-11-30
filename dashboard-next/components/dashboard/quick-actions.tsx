'use client';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, Play, FileText, RefreshCw } from 'lucide-react';
import Link from 'next/link';

export function QuickActions() {
  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" asChild>
        <Link href="/reports">
          <FileText className="mr-2 h-4 w-4" />
          View Reports
        </Link>
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Audit
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem asChild>
            <Link href="/audit?mode=quick">
              <Play className="mr-2 h-4 w-4" />
              Quick Scan
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/audit?mode=full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Full Audit
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/audit?mode=security">
              Security Only
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/audit?mode=performance">
              Performance Only
            </Link>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
