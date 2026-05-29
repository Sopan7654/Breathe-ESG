import type { RecordDto } from '../types';

interface Props {
  status: RecordDto['status'] | string;
  size?: 'sm' | 'md';
}

const config: Record<string, { label: string; cls: string }> = {
  Pending:  { label: 'Pending',  cls: 'badge-pending' },
  Flagged:  { label: 'Flagged',  cls: 'badge-flagged' },
  Approved: { label: 'Approved', cls: 'badge-approved' },
  Rejected: { label: 'Rejected', cls: 'badge-rejected' },
};

export function StatusBadge({ status }: Props) {
  const c = config[status] ?? { label: status, cls: 'badge-rejected' };
  return <span className={c.cls}>{c.label}</span>;
}

const scopeConfig: Record<string, { label: string; cls: string }> = {
  Scope1: { label: 'Scope 1', cls: 'badge-scope1' },
  Scope2: { label: 'Scope 2', cls: 'badge-scope2' },
  Scope3: { label: 'Scope 3', cls: 'badge-scope3' },
};

export function ScopeBadge({ scope }: { scope: string }) {
  const c = scopeConfig[scope] ?? { label: scope, cls: 'badge-rejected' };
  return <span className={c.cls}>{c.label}</span>;
}

const sourceConfig: Record<string, { label: string; cls: string }> = {
  SapFuel:             { label: 'SAP Fuel',    cls: 'badge-sap' },
  UtilityElectricity:  { label: 'Utility',     cls: 'badge-utility' },
  CorporateTravel:     { label: 'Travel',      cls: 'badge-travel' },
};

export function SourceBadge({ sourceType }: { sourceType: string }) {
  const c = sourceConfig[sourceType] ?? { label: sourceType, cls: 'badge-rejected' };
  return <span className={c.cls}>{c.label}</span>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === 'Error' ? 'badge-error' : 'badge-warning';
  return <span className={cls}>{severity}</span>;
}
