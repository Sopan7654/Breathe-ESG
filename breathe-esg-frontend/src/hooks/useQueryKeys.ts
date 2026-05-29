/**
 * hooks/useQueryKeys.ts
 * Centralised query key factory — keeps React Query cache keys consistent
 * across all components and prevents cache misses from key typos.
 */
export const queryKeys = {
  summary:     (companyId?: string) => ['summary', companyId] as const,
  dataSources: (companyId?: string) => ['datasources', companyId] as const,
  records:     (filters: object)    => ['records', filters] as const,
  record:      (id: string)         => ['record', id] as const,
  uploads:     (page: number)       => ['uploads', page] as const,
  audits:      (page: number)       => ['audits', page] as const,
  auditEntity: (entityId: string)   => ['audit-entity', entityId] as const,
  flags:       (params: object)     => ['flags', params] as const,
};
