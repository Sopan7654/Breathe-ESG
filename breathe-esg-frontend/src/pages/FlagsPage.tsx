import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { flagsService } from '../services/services';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { TableBodySkeleton } from '../components/Skeleton';
import { queryKeys } from '../hooks/useQueryKeys';
import { RefreshCw } from 'lucide-react';

export default function FlagsPage() {
  const queryClient   = useQueryClient();
  const [openOnly, setOpenOnly] = useState(true);
  const [severity, setSeverity] = useState('');

  const params = { openOnly, severity };
  const { data, isLoading, isFetching } = useQuery({
    queryKey: queryKeys.flags(params),
    queryFn:  () => flagsService.getFlags(openOnly, severity || undefined),
  });

  const flags = data?.items ?? [];
  const total = data?.totalCount ?? 0;

  return (
    <div className="flex flex-col h-screen">
      <div className="page-header flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-text-primary">Data Quality Flags</h1>
          <p className="text-xs text-text-muted mt-0.5">{total} flags · validation rules fired at ingestion time</p>
        </div>
        <button onClick={() => queryClient.invalidateQueries({ queryKey: ['flags'] })}
          className="btn-ghost" disabled={isFetching}>
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filters */}
      <div className="px-6 py-2 border-b border-border bg-surface-1 flex items-center gap-3 flex-shrink-0">
        <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
          <input type="checkbox" checked={openOnly} onChange={e => setOpenOnly(e.target.checked)}
            className="accent-accent-blue" />
          Open flags only
        </label>
        <select className="select text-xs py-1" value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="Error">Error</option>
          <option value="Warning">Warning</option>
        </select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rule Code</th>
              <th>Severity</th>
              <th>Description</th>
              <th>Record</th>
              <th>Record Status</th>
              <th>Detected</th>
              <th>Resolved</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <TableBodySkeleton rows={6} cols={7} />}
            {!isLoading && flags.length === 0 && (
              <tr><td colSpan={7} className="text-center text-text-muted py-8">No flags found.</td></tr>
            )}
            {flags.map(f => (
              <tr key={f.id}>
                <td><span className="mono text-xs text-text-secondary">{f.ruleCode}</span></td>
                <td><SeverityBadge severity={f.severity} /></td>
                <td className="text-xs text-text-secondary max-w-[300px]">{f.description}</td>
                <td className="text-xs mono text-text-muted">{f.normalizedRecordId.slice(0, 10)}…</td>
                <td><StatusBadge status={f.recordStatus} /></td>
                <td className="text-xs text-text-muted">{new Date(f.createdAt).toLocaleDateString()}</td>
                <td className="text-xs text-text-muted">
                  {f.resolvedAt ? new Date(f.resolvedAt).toLocaleDateString() : <span className="text-yellow-400">Open</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
