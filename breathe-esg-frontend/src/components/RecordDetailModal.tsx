import { useState, useEffect, useCallback } from 'react';
import { X, CheckCircle, XCircle, Lock, Edit2, Save } from 'lucide-react';
import type { RecordDto, AuditLogDto } from '../types';
import { StatusBadge, ScopeBadge, SourceBadge, SeverityBadge } from './Badges';
import { AuditTimeline } from './AuditTimeline';
import { recordsService, auditService } from '../services/services';

interface Props {
  record: RecordDto;
  onClose: () => void;
  onUpdate: (updated: RecordDto) => void;
}

export function RecordDetailModal({ record, onClose, onUpdate }: Props) {
  const [tab, setTab] = useState<'details' | 'flags' | 'audit' | 'raw'>('details');
  const [auditLogs, setAuditLogs] = useState<AuditLogDto[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState('');
  const [editForm, setEditForm] = useState({
    quantity: record.quantity?.toString() ?? '',
    unit: record.unit ?? '',
    category: record.category ?? '',
    activityDate: record.activityDate ?? '',
  });


  const loadAudit = useCallback(async () => {
    const logs = await auditService.getEntityAudit(record.id);
    setAuditLogs(logs);
  }, [record.id]);

  useEffect(() => {
    if (tab === 'audit') loadAudit();
  }, [tab, loadAudit]);

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      const updated = await recordsService.approve(record.id, notes || undefined);
      onUpdate(updated);
    } finally { setActionLoading(false); }
  };

  const handleReject = async () => {
    if (!notes.trim()) { alert('Please add a note explaining the rejection.'); return; }
    setActionLoading(true);
    try {
      const updated = await recordsService.reject(record.id, notes);
      onUpdate(updated);
    } finally { setActionLoading(false); }
  };

  const handleEdit = async () => {
    setActionLoading(true);
    try {
      const updated = await recordsService.edit(record.id, {
        quantity: editForm.quantity ? parseFloat(editForm.quantity) : undefined,
        unit: editForm.unit || undefined,
        category: editForm.category || undefined,
        activityDate: editForm.activityDate || undefined,
      });
      onUpdate(updated);
      setEditing(false);
    } finally { setActionLoading(false); }
  };

  const canEdit = !record.isLocked && record.status !== 'Approved' && record.status !== 'Rejected';
  const canAction = !record.isLocked && record.status !== 'Approved' && record.status !== 'Rejected';

  const openFlags = record.flags.filter(f => !f.resolvedAt);
  const resolvedFlags = record.flags.filter(f => f.resolvedAt);

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-panel">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-border flex-shrink-0">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={record.status} />
              <SourceBadge sourceType={record.sourceType} />
              <ScopeBadge scope={record.emissionScope} />
              {record.isLocked && (
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <Lock className="w-3 h-3" /> Locked
                </span>
              )}
            </div>
            <div className="text-sm text-text-primary font-medium">{record.description || 'Record Detail'}</div>
            <div className="mono text-[10px]">{record.id}</div>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5 -mr-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border flex-shrink-0">
          {(['details', 'flags', 'audit', 'raw'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t
                  ? 'border-accent-blue text-text-primary'
                  : 'border-transparent text-text-muted hover:text-text-secondary'
              }`}
            >
              {t === 'flags' ? `Flags (${record.flags.length})` : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* ── Details tab ── */}
          {tab === 'details' && (
            <div className="space-y-4">
              {/* Field grid */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Activity Date', value: record.activityDate },
                  { label: 'Category', value: record.category },
                  { label: 'Quantity', value: record.quantity != null ? `${record.quantity} ${record.unit}` : '—' },
                  { label: 'Original', value: record.originalQuantity != null ? `${record.originalQuantity} ${record.originalUnit}` : '—' },
                  { label: 'Location', value: record.location },
                  { label: 'Data Source', value: record.dataSourceName },
                  { label: 'File', value: record.fileName },
                  { label: 'Billing Period', value: record.activityPeriodStart ? `${record.activityPeriodStart} → ${record.activityPeriodEnd}` : '—' },
                ].map(({ label, value }) => (
                  <div key={label} className="card p-3">
                    <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{label}</div>
                    <div className="text-sm text-text-primary">{value ?? '—'}</div>
                  </div>
                ))}
              </div>

              {/* Edit form */}
              {editing && canEdit && (
                <div className="card p-4 space-y-3 border-accent-blue/30">
                  <div className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Edit Record</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-text-muted mb-1">Quantity</label>
                      <input className="input w-full" type="number" value={editForm.quantity}
                        onChange={e => setEditForm(p => ({ ...p, quantity: e.target.value }))} />
                    </div>
                    <div>
                      <label className="block text-xs text-text-muted mb-1">Unit</label>
                      <input className="input w-full" value={editForm.unit}
                        onChange={e => setEditForm(p => ({ ...p, unit: e.target.value }))} />
                    </div>
                    <div>
                      <label className="block text-xs text-text-muted mb-1">Category</label>
                      <input className="input w-full" value={editForm.category}
                        onChange={e => setEditForm(p => ({ ...p, category: e.target.value }))} />
                    </div>
                    <div>
                      <label className="block text-xs text-text-muted mb-1">Activity Date</label>
                      <input className="input w-full" type="date" value={editForm.activityDate}
                        onChange={e => setEditForm(p => ({ ...p, activityDate: e.target.value }))} />
                    </div>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <button onClick={handleEdit} disabled={actionLoading} className="btn-primary">
                      <Save className="w-3.5 h-3.5" /> Save Changes
                    </button>
                    <button onClick={() => setEditing(false)} className="btn-ghost">Cancel</button>
                  </div>
                </div>
              )}

              {/* Review / action area */}
              {canAction && !editing && (
                <div className="card p-4 space-y-3">
                  <div className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Analyst Actions</div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1">Notes</label>
                    <textarea
                      className="input w-full h-20 resize-none"
                      placeholder="Add context or reason for approval/rejection..."
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                    />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={handleApprove} disabled={actionLoading} className="btn-success">
                      <CheckCircle className="w-3.5 h-3.5" /> Approve
                    </button>
                    <button onClick={handleReject} disabled={actionLoading} className="btn-danger">
                      <XCircle className="w-3.5 h-3.5" /> Reject
                    </button>
                    {canEdit && (
                      <button onClick={() => setEditing(true)} className="btn-ghost">
                        <Edit2 className="w-3.5 h-3.5" /> Edit
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Review notes (read-only for terminal states) */}
              {record.reviewNotes && !canAction && (
                <div className="card p-3">
                  <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Review Notes</div>
                  <div className="text-sm text-text-secondary italic">"{record.reviewNotes}"</div>
                  <div className="text-[10px] text-text-muted mt-1">
                    by {record.reviewedBy} · {record.reviewedAt ? new Date(record.reviewedAt).toLocaleString() : ''}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Flags tab ── */}
          {tab === 'flags' && (
            <div className="space-y-3">
              {record.flags.length === 0 && (
                <p className="text-text-muted text-sm">No flags on this record.</p>
              )}
              {openFlags.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Open Flags</div>
                  <div className="space-y-2">
                    {openFlags.map(flag => (
                      <div key={flag.id} className="card p-3 border-l-2 border-l-accent-red">
                        <div className="flex items-center gap-2 mb-1">
                          <SeverityBadge severity={flag.severity} />
                          <span className="mono text-xs text-accent-red">{flag.ruleCode}</span>
                        </div>
                        <p className="text-sm text-text-secondary">{flag.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {resolvedFlags.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">Resolved Flags</div>
                  <div className="space-y-2">
                    {resolvedFlags.map(flag => (
                      <div key={flag.id} className="card p-3 opacity-60">
                        <div className="flex items-center gap-2 mb-1">
                          <SeverityBadge severity={flag.severity} />
                          <span className="mono text-xs">{flag.ruleCode}</span>
                        </div>
                        <p className="text-xs text-text-secondary">{flag.description}</p>
                        <div className="text-[10px] text-text-muted mt-1">
                          Resolved by {flag.resolvedBy} · {flag.resolvedAt ? new Date(flag.resolvedAt).toLocaleString() : ''}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Audit tab ── */}
          {tab === 'audit' && <AuditTimeline logs={auditLogs} />}

          {/* ── Raw tab ── */}
          {tab === 'raw' && (
            <div>
              <div className="text-xs text-text-muted mb-2">Original source payload preserved at ingestion time.</div>
              <pre className="bg-surface-2 rounded p-3 text-xs text-text-secondary overflow-x-auto leading-relaxed font-mono whitespace-pre-wrap">
                {(() => { try { return JSON.stringify(JSON.parse(record.id), null, 2); } catch { return 'Raw payload unavailable'; } })()}
              </pre>
              {/* We'd normally fetch rawPayload from a detail endpoint; shown here for demo */}
              <div className="mt-3 text-[10px] text-text-muted">
                Upload ID: <span className="mono">{record.rawUploadId}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
