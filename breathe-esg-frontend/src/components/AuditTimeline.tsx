import type { AuditLogDto } from '../types';
import { Clock, Edit2, CheckCircle, XCircle, Upload, AlertTriangle } from 'lucide-react';

interface Props {
  logs: AuditLogDto[];
}

const actionConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  CREATED:  { icon: <Upload className="w-3 h-3" />,      color: 'text-accent-blue',   label: 'Created' },
  UPDATED:  { icon: <Edit2 className="w-3 h-3" />,       color: 'text-yellow-400',    label: 'Edited' },
  APPROVED: { icon: <CheckCircle className="w-3 h-3" />, color: 'text-accent-green',  label: 'Approved' },
  REJECTED: { icon: <XCircle className="w-3 h-3" />,     color: 'text-accent-red',    label: 'Rejected' },
  FLAGGED:  { icon: <AlertTriangle className="w-3 h-3"/>, color: 'text-yellow-400',   label: 'Flagged' },
};

export function AuditTimeline({ logs }: Props) {
  if (logs.length === 0) {
    return <p className="text-text-muted text-sm py-4">No audit history yet.</p>;
  }

  return (
    <div className="space-y-0">
      {logs.map((log, i) => {
        const ac = actionConfig[log.action] ?? {
          icon: <Clock className="w-3 h-3" />, color: 'text-text-muted', label: log.action
        };

        let parsedBefore: Record<string, unknown> | null = null;
        let parsedAfter: Record<string, unknown> | null = null;
        try {
          if (log.previousValue) parsedBefore = JSON.parse(log.previousValue);
          if (log.newValue) parsedAfter = JSON.parse(log.newValue);
        } catch { /* ignore */ }

        return (
          <div key={log.id} className="relative pl-6">
            {/* Timeline line */}
            {i < logs.length - 1 && (
              <div className="absolute left-[9px] top-5 bottom-0 w-px bg-border" />
            )}

            {/* Dot */}
            <div className={`absolute left-0 top-1.5 w-[18px] h-[18px] rounded-full border border-border bg-surface-2 flex items-center justify-center ${ac.color}`}>
              {ac.icon}
            </div>

            <div className="pb-4">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={`text-xs font-semibold ${ac.color}`}>{ac.label}</span>
                <span className="text-text-muted text-xs">by {log.performedBy}</span>
              </div>
              <div className="text-[11px] text-text-muted mono mb-1">
                {new Date(log.createdAt).toLocaleString()}
              </div>

              {/* Changed fields */}
              {log.changedFields.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-1.5">
                  {log.changedFields.map(f => (
                    <span key={f} className="px-1.5 py-0.5 bg-surface-3 rounded text-[10px] text-text-secondary font-mono">
                      {f}
                    </span>
                  ))}
                </div>
              )}

              {/* Before/after diff for updates */}
              {log.action === 'UPDATED' && parsedBefore && parsedAfter && (
                <div className="space-y-1 mt-1.5">
                  {log.changedFields.map(field => {
                    const before = parsedBefore![field as keyof typeof parsedBefore];
                    const after = parsedAfter![field as keyof typeof parsedAfter];
                    if (before === after) return null;
                    return (
                      <div key={field} className="text-xs">
                        <span className="text-text-muted">{field}: </span>
                        <span className="line-through text-accent-red/80 mr-1">{String(before ?? '—')}</span>
                        <span className="text-accent-green/80">{String(after ?? '—')}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Notes for approve/reject */}
              {['APPROVED', 'REJECTED'].includes(log.action) && parsedAfter && (parsedAfter as any).reviewNotes && (
                <div className="mt-1 text-xs text-text-secondary italic">
                  "{(parsedAfter as any).reviewNotes}"
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
