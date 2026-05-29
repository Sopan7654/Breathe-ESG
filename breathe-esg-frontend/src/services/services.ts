import api from './api';
import type {
  RecordDto, RecordListResponse, RecordFilters, DashboardSummary, DataSourceDto,
  AuditLogDto, AuditListResponse
} from '../types';

export const recordsService = {
  async getRecords(filters: RecordFilters): Promise<RecordListResponse> {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.sourceType) params.set('sourceType', filters.sourceType);
    if (filters.scope) params.set('scope', filters.scope);
    if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
    if (filters.dateTo) params.set('dateTo', filters.dateTo);
    if (filters.uploadId) params.set('uploadId', filters.uploadId);
    params.set('page', String(filters.page));
    params.set('pageSize', String(filters.pageSize));
    const res = await api.get<RecordListResponse>(`/api/records?${params}`);
    return res.data;
  },

  async getRecord(id: string): Promise<RecordDto> {
    const res = await api.get<RecordDto>(`/api/records/${id}`);
    return res.data;
  },

  async approve(id: string, notes?: string): Promise<RecordDto> {
    const res = await api.post<RecordDto>(`/api/records/${id}/approve`, { notes });
    return res.data;
  },

  async reject(id: string, notes?: string): Promise<RecordDto> {
    const res = await api.post<RecordDto>(`/api/records/${id}/reject`, { notes });
    return res.data;
  },

  async edit(id: string, data: {
    quantity?: number; unit?: string; category?: string;
    activityDate?: string; reviewNotes?: string;
  }): Promise<RecordDto> {
    const res = await api.patch<RecordDto>(`/api/records/${id}`, data);
    return res.data;
  },

  async getSummary(): Promise<DashboardSummary> {
    const res = await api.get<DashboardSummary>('/api/records/summary');
    return res.data;
  },

  async getDataSources(): Promise<DataSourceDto[]> {
    const res = await api.get<DataSourceDto[]>('/api/records/datasources');
    return res.data;
  },
};

export const auditService = {
  async getAuditLog(page = 1, pageSize = 50): Promise<AuditListResponse> {
    const res = await api.get<AuditListResponse>(`/api/audits?page=${page}&pageSize=${pageSize}`);
    return res.data;
  },

  async getEntityAudit(entityId: string): Promise<AuditLogDto[]> {
    const res = await api.get<AuditLogDto[]>(`/api/audits/entity/${entityId}`);
    return res.data;
  },
};

export const uploadService = {
  async uploadFile(file: File, dataSourceId: string) {
    const form = new FormData();
    form.append('file', file);
    form.append('dataSourceId', dataSourceId);
    const res = await api.post('/api/uploads', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async getUploads(page = 1, pageSize = 20) {
    const res = await api.get(`/api/uploads?page=${page}&pageSize=${pageSize}`);
    return res.data;
  },
};

export const flagsService = {
  async getFlags(openOnly = true, severity?: string, page = 1, pageSize = 50) {
    const params = new URLSearchParams({ openOnly: String(openOnly), page: String(page), pageSize: String(pageSize) });
    if (severity) params.set('severity', severity);
    const res = await api.get(`/api/flags?${params}`);
    return res.data;
  },
};
