// ── Shared types matching backend DTOs ────────────────────────────────────

export interface FlagDto {
  id: string;
  ruleCode: string;
  severity: 'Warning' | 'Error';
  description: string;
  resolvedAt: string | null;
  resolvedBy: string | null;
  createdAt: string;
}

export interface RecordDto {
  id: string;
  companyId: string;
  rawUploadId: string;
  sourceType: 'SapFuel' | 'UtilityElectricity' | 'CorporateTravel';
  emissionScope: 'Scope1' | 'Scope2' | 'Scope3';
  activityDate: string | null;
  activityPeriodStart: string | null;
  activityPeriodEnd: string | null;
  quantity: number | null;
  unit: string | null;
  originalQuantity: number | null;
  originalUnit: string | null;
  category: string | null;
  location: string | null;
  description: string | null;
  status: 'Pending' | 'Flagged' | 'Approved' | 'Rejected';
  reviewedBy: string | null;
  reviewedAt: string | null;
  reviewNotes: string | null;
  isLocked: boolean;
  flags: FlagDto[];
  dataSourceName: string;
  fileName: string;
  createdAt: string;
  updatedAt: string;
}

export interface RecordListResponse {
  items: RecordDto[];
  totalCount: number;
  page: number;
  pageSize: number;
}

export interface UploadListItem {
  id: string;
  fileName: string;
  dataSourceName: string;
  sourceType: string;
  rowCount: number;
  status: string;
  uploadedBy: string;
  errorSummary: string | null;
  createdAt: string;
}

export interface UploadListResponse {
  items: UploadListItem[];
  totalCount: number;
  page: number;
  pageSize: number;
}

export interface UploadResponse {
  uploadId: string;
  fileName: string;
  rowCount: number;
  flaggedCount: number;
  status: string;
  errorSummary: string | null;
  createdAt: string;
}

export interface AuditLogDto {
  id: string;
  entityType: string;
  entityId: string;
  action: string;
  performedBy: string;
  previousValue: string | null;
  newValue: string | null;
  changedFields: string[];
  ipAddress: string | null;
  createdAt: string;
}

export interface AuditListResponse {
  items: AuditLogDto[];
  totalCount: number;
  page: number;
  pageSize: number;
}

export interface DashboardSummary {
  totalRecords: number;
  pendingCount: number;
  flaggedCount: number;
  approvedCount: number;
  rejectedCount: number;
  totalUploads: number;
  openFlagsCount: number;
}

export interface DataSourceDto {
  id: string;
  name: string;
  sourceType: string;
}

export interface FlagListItem {
  id: string;
  normalizedRecordId: string;
  ruleCode: string;
  severity: string;
  description: string;
  recordDescription: string;
  recordStatus: string;
  resolvedAt: string | null;
  createdAt: string;
}

export interface RecordFilters {
  status?: string;
  sourceType?: string;
  scope?: string;
  dateFrom?: string;
  dateTo?: string;
  uploadId?: string;
  page: number;
  pageSize: number;
}
