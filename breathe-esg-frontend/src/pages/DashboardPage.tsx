import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { recordsService } from '../services/services';
import type { DashboardSummary } from '../types';
import { queryKeys } from '../hooks/useQueryKeys';
import { StatCardSkeleton } from '../components/Skeleton';
import {
  ClipboardList, AlertTriangle, CheckCircle, XCircle,
  Upload, Database, ArrowRight, RefreshCw,
} from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
}

function StatCard({ label, value, icon, color, onClick }: StatCardProps) {
  return (
    <div
      className={`stat-card ${onClick ? 'cursor-pointer hover:border-border transition-colors' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted uppercase tracking-wider">{label}</span>
        <span className={color}>{icon}</span>
      </div>
      <div className={`text-2xl font-semibold ${color}`}>{value.toLocaleString()}</div>
    </div>
  );
}

export default function DashboardPage() {
  const navigate    = useNavigate();
  const queryClient = useQueryClient();

  const { data: summary, isLoading, isFetching } = useQuery<DashboardSummary>({
    queryKey: queryKeys.summary(),
    queryFn:  () => recordsService.getSummary(),
    // Override default staleTime — dashboard is more time-sensitive
    staleTime: 30_000,
  });

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.summary() });
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="text-base font-semibold text-text-primary">ESG Operations Dashboard</h1>
          <p className="text-xs text-text-muted mt-0.5">
            {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
          </p>
        </div>
        <button onClick={handleRefresh} className="btn-ghost" disabled={isFetching}>
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Stat grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                label="Total Records" value={summary?.totalRecords ?? 0}
                icon={<Database className="w-4 h-4" />} color="text-text-primary"
              />
              <StatCard
                label="Pending" value={summary?.pendingCount ?? 0}
                icon={<ClipboardList className="w-4 h-4" />} color="text-yellow-400"
                onClick={() => navigate('/review?status=Pending')}
              />
              <StatCard
                label="Flagged" value={summary?.flaggedCount ?? 0}
                icon={<AlertTriangle className="w-4 h-4" />} color="text-accent-red"
                onClick={() => navigate('/review?status=Flagged')}
              />
              <StatCard
                label="Approved" value={summary?.approvedCount ?? 0}
                icon={<CheckCircle className="w-4 h-4" />} color="text-accent-green"
                onClick={() => navigate('/review?status=Approved')}
              />
            </>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                label="Rejected" value={summary?.rejectedCount ?? 0}
                icon={<XCircle className="w-4 h-4" />} color="text-text-muted"
                onClick={() => navigate('/review?status=Rejected')}
              />
              <StatCard
                label="Total Uploads" value={summary?.totalUploads ?? 0}
                icon={<Upload className="w-4 h-4" />} color="text-accent-blue"
                onClick={() => navigate('/upload')}
              />
              <StatCard
                label="Open Flags" value={summary?.openFlagsCount ?? 0}
                icon={<AlertTriangle className="w-4 h-4" />} color="text-yellow-400"
                onClick={() => navigate('/flags')}
              />
            </>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-text-primary">Quick Actions</h2>
          </div>
          <div className="divide-y divide-border-subtle">
            {[
              { label: 'Review Flagged Records', desc: `${summary?.flaggedCount ?? 0} records require attention`, to: '/review?status=Flagged', urgent: (summary?.flaggedCount ?? 0) > 0 },
              { label: 'Upload New Data File', desc: 'Ingest SAP, utility, or travel data', to: '/upload', urgent: false },
              { label: 'View Audit Log', desc: 'Full immutable trail of all actions', to: '/audit', urgent: false },
              { label: 'Triage Flags', desc: `${summary?.openFlagsCount ?? 0} open data quality flags`, to: '/flags', urgent: false },
            ].map(item => (
              <div
                key={item.to}
                className="flex items-center justify-between px-4 py-3 hover:bg-surface-2 cursor-pointer transition-colors"
                onClick={() => navigate(item.to)}
              >
                <div>
                  <div className={`text-sm font-medium ${item.urgent ? 'text-accent-red' : 'text-text-primary'}`}>
                    {item.label}
                    {item.urgent && <span className="ml-2 w-1.5 h-1.5 rounded-full bg-accent-red inline-block" />}
                  </div>
                  <div className="text-xs text-text-muted">{item.desc}</div>
                </div>
                <ArrowRight className="w-4 h-4 text-text-muted" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
