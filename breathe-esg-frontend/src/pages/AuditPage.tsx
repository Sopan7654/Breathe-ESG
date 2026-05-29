import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { auditService } from '../services/services';
import { queryKeys } from '../hooks/useQueryKeys';
import { TableBodySkeleton } from '../components/Skeleton';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

const ACTION_COLORS: Record<string, string> = {
  CREATED:  'text-accent-blue',
  UPDATED:  'text-yellow-400',
  APPROVED: 'text-accent-green',
  REJECTED: 'text-accent-red',
  FLAGGED:  'text-yellow-400',
};

const PAGE_SIZE = 50;

export default function AuditPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: queryKeys.audits(page),
    queryFn:  () => auditService.getAuditLog(page, PAGE_SIZE),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.ceil(data.totalCount / PAGE_SIZE) : 0;

  return (
    <div className="flex flex-col h-screen">
      <div className="page-header flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-text-primary">Audit Log</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Append-only trail of all analyst actions · {data?.totalCount.toLocaleString() ?? '—'} entries
          </p>
        </div>
        <button onClick={() => queryClient.invalidateQueries({ queryKey: ['audits'] })}
          className="btn-ghost" disabled={isFetching}>
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Entity Type</th>
              <th>Entity ID</th>
              <th>Performed By</th>
              <th>Changed Fields</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <TableBodySkeleton rows={8} cols={7} />}
            {!isLoading && data?.items.length === 0 && (
              <tr><td colSpan={7} className="text-center text-text-muted py-8">No audit entries yet.</td></tr>
            )}
            {data?.items.map((log) => (
              <tr key={log.id}>
                <td className="text-xs mono text-text-muted whitespace-nowrap">
                  {new Date(log.createdAt).toLocaleString()}
                </td>
                <td>
                  <span className={`text-xs font-semibold mono ${ACTION_COLORS[log.action] ?? 'text-text-secondary'}`}>
                    {log.action}
                  </span>
                </td>
                <td className="text-xs text-text-secondary">{log.entityType}</td>
                <td className="text-xs mono text-text-muted">{log.entityId.slice(0, 12)}…</td>
                <td className="text-xs text-text-primary">{log.performedBy}</td>
                <td className="text-xs">
                  {log.changedFields.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {log.changedFields.map(f => (
                        <span key={f} className="px-1.5 py-0.5 bg-surface-3 rounded text-[10px] mono text-text-muted">{f}</span>
                      ))}
                    </div>
                  ) : '—'}
                </td>
                <td className="text-xs mono text-text-muted">{log.ipAddress ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between px-6 py-3 border-t border-border bg-surface-1 flex-shrink-0">
        <span className="text-xs text-text-muted">Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button className="btn-ghost py-1 px-2" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button className="btn-ghost py-1 px-2" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
