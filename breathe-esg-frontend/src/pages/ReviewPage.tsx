import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { recordsService } from '../services/services';
import type { RecordDto, RecordFilters } from '../types';
import { StatusBadge, ScopeBadge, SourceBadge } from '../components/Badges';
import { RecordDetailModal } from '../components/RecordDetailModal';
import { TableBodySkeleton } from '../components/Skeleton';
import { queryKeys } from '../hooks/useQueryKeys';
import { useDebounce } from '../hooks/useDebounce';
import { AlertTriangle, ChevronLeft, ChevronRight, RefreshCw, Filter } from 'lucide-react';

const PAGE_SIZE = 50;

export default function ReviewPage() {
  const [searchParams]  = useSearchParams();
  const queryClient     = useQueryClient();
  const [selected, setSelected] = useState<RecordDto | null>(null);

  // Separate UI filters (updates instantly) from debounced filters (fires API call)
  const [filters, setFilters] = useState<RecordFilters>({
    status:     searchParams.get('status') ?? '',
    sourceType: '',
    scope:      '',
    dateFrom:   '',
    dateTo:     '',
    page:       1,
    pageSize:   PAGE_SIZE,
  });

  // 300ms debounce — prevents API spam on every filter change
  const debouncedFilters = useDebounce(filters, 300);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: queryKeys.records(debouncedFilters),
    queryFn:  () => recordsService.getRecords(debouncedFilters),
    // Keep previous data visible while new page loads — no flash of empty content
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.ceil(data.totalCount / PAGE_SIZE) : 0;

  const handleUpdate = (updated: RecordDto) => {
    // Optimistic local update — no full refetch needed for single record changes
    queryClient.setQueryData(queryKeys.records(debouncedFilters), (old: typeof data) =>
      old ? { ...old, items: old.items.map(r => r.id === updated.id ? updated : r) } : old
    );
    // Invalidate summary so dashboard counts refresh next visit
    queryClient.invalidateQueries({ queryKey: queryKeys.summary() });
    setSelected(updated);
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['records'] });
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="page-header flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-text-primary">Record Review</h1>
          <p className="text-xs text-text-muted mt-0.5">
            {data?.totalCount.toLocaleString() ?? '—'} records · click row to open detail panel
          </p>
        </div>
        <button onClick={handleRefresh} className="btn-ghost" disabled={isFetching}>
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter bar */}
      <div className="px-6 py-2 border-b border-border bg-surface-1 flex items-center gap-3 flex-wrap flex-shrink-0">
        <Filter className="w-3.5 h-3.5 text-text-muted flex-shrink-0" />

        <select className="select text-xs py-1" value={filters.status}
          onChange={e => setFilters(p => ({ ...p, status: e.target.value, page: 1 }))}>
          <option value="">All Statuses</option>
          <option>Pending</option><option>Flagged</option>
          <option>Approved</option><option>Rejected</option>
        </select>

        <select className="select text-xs py-1" value={filters.sourceType}
          onChange={e => setFilters(p => ({ ...p, sourceType: e.target.value, page: 1 }))}>
          <option value="">All Sources</option>
          <option value="SapFuel">SAP Fuel</option>
          <option value="UtilityElectricity">Utility</option>
          <option value="CorporateTravel">Travel</option>
        </select>

        <select className="select text-xs py-1" value={filters.scope}
          onChange={e => setFilters(p => ({ ...p, scope: e.target.value, page: 1 }))}>
          <option value="">All Scopes</option>
          <option value="Scope1">Scope 1</option>
          <option value="Scope2">Scope 2</option>
          <option value="Scope3">Scope 3</option>
        </select>

        <input className="input text-xs py-1 w-32" type="date" value={filters.dateFrom}
          onChange={e => setFilters(p => ({ ...p, dateFrom: e.target.value, page: 1 }))} />
        <input className="input text-xs py-1 w-32" type="date" value={filters.dateTo}
          onChange={e => setFilters(p => ({ ...p, dateTo: e.target.value, page: 1 }))} />

        {(filters.status || filters.sourceType || filters.scope || filters.dateFrom || filters.dateTo) && (
          <button className="text-xs text-accent-red hover:underline"
            onClick={() => setFilters(p => ({ ...p, status: '', sourceType: '', scope: '', dateFrom: '', dateTo: '', page: 1 }))}>
            Clear
          </button>
        )}

        {/* Subtle "loading new results" indicator — data stays visible */}
        {isFetching && !isLoading && (
          <div className="ml-auto flex items-center gap-1.5 text-xs text-text-muted">
            <div className="w-3 h-3 border border-border border-t-accent-blue rounded-full animate-spin" />
            Updating…
          </div>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-8" />
              <th>Description</th>
              <th>Source</th>
              <th>Scope</th>
              <th>Date</th>
              <th>Quantity</th>
              <th>Category</th>
              <th>Location</th>
              <th>Status</th>
              <th>Flags</th>
              <th>Reviewed By</th>
            </tr>
          </thead>
          <tbody>
            {/* First load: show skeleton rows */}
            {isLoading && <TableBodySkeleton rows={10} cols={11} />}

            {/* Empty state */}
            {!isLoading && data?.items.length === 0 && (
              <tr><td colSpan={11} className="text-center text-text-muted py-8">No records match filters.</td></tr>
            )}

            {/* Data rows — kept visible while new page loads (placeholderData) */}
            {data?.items.map(record => {
              const hasOpenFlag = record.flags.some(f => !f.resolvedAt);
              const hasError    = record.flags.some(f => f.severity === 'Error' && !f.resolvedAt);
              return (
                <tr key={record.id} onClick={() => setSelected(record)}
                  className={hasError ? 'bg-red-900/5' : ''}>
                  <td>
                    {hasOpenFlag && (
                      <AlertTriangle className={`w-3.5 h-3.5 ${hasError ? 'text-accent-red' : 'text-yellow-400'}`} />
                    )}
                  </td>
                  <td>
                    <div className="text-xs max-w-[220px] truncate" title={record.description ?? ''}>
                      {record.description || '—'}
                    </div>
                    <div className="mono text-[10px] text-text-muted">{record.id.slice(0, 8)}…</div>
                  </td>
                  <td><SourceBadge sourceType={record.sourceType} /></td>
                  <td><ScopeBadge scope={record.emissionScope} /></td>
                  <td className="text-xs text-text-secondary">{record.activityDate ?? '—'}</td>
                  <td className="text-xs">
                    {record.quantity != null ? `${Number(record.quantity).toLocaleString()} ${record.unit}` : '—'}
                  </td>
                  <td className="text-xs text-text-secondary">{record.category ?? '—'}</td>
                  <td className="text-xs text-text-muted max-w-[120px] truncate">{record.location ?? '—'}</td>
                  <td><StatusBadge status={record.status} /></td>
                  <td className="text-xs">
                    {record.flags.length > 0 ? (
                      <span className={`mono ${hasError ? 'text-accent-red' : 'text-yellow-400'}`}>
                        {record.flags.filter(f => !f.resolvedAt).length} open
                      </span>
                    ) : '—'}
                  </td>
                  <td className="text-xs text-text-muted">{record.reviewedBy ?? '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-6 py-3 border-t border-border bg-surface-1 flex-shrink-0">
        <span className="text-xs text-text-muted">
          Page {filters.page} of {totalPages} · {data?.totalCount ?? 0} records
        </span>
        <div className="flex gap-2">
          <button className="btn-ghost py-1 px-2" disabled={filters.page <= 1}
            onClick={() => setFilters(p => ({ ...p, page: p.page - 1 }))}>
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button className="btn-ghost py-1 px-2" disabled={filters.page >= totalPages}
            onClick={() => setFilters(p => ({ ...p, page: p.page + 1 }))}>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {selected && (
        <RecordDetailModal
          record={selected}
          onClose={() => setSelected(null)}
          onUpdate={handleUpdate}
        />
      )}
    </div>
  );
}
