import { useState, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { uploadService, recordsService } from '../services/services';
import type { DataSourceDto, UploadListItem, UploadResponse } from '../types';
import { queryKeys } from '../hooks/useQueryKeys';
import { TableBodySkeleton } from '../components/Skeleton';
import { Upload, CheckCircle, AlertCircle, FileText, ArrowUpCircle } from 'lucide-react';

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

const srcTypeLabel: Record<string, string> = {
  SapFuel: 'SAP Fuel CSV',
  UtilityElectricity: 'Utility CSV',
  CorporateTravel: 'Concur JSON',
};

export default function UploadPage() {
  const queryClient  = useQueryClient();
  const fileRef      = useRef<HTMLInputElement>(null);
  const [selectedSource, setSelectedSource] = useState('');
  const [file,  setFile]     = useState<File | null>(null);
  const [state, setState]    = useState<UploadState>('idle');
  const [result, setResult]  = useState<UploadResponse | null>(null);
  const [errorMsg, setError] = useState('');
  const [dragging, setDrag]  = useState(false);

  // React Query for data sources — cached 5 min (matches backend cache TTL)
  const { data: dataSources = [] } = useQuery<DataSourceDto[]>({
    queryKey: queryKeys.dataSources(),
    queryFn:  () => recordsService.getDataSources(),
    staleTime: 5 * 60 * 1000,
  });

  // React Query for upload history — refetches after successful upload
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: queryKeys.uploads(1),
    queryFn:  () => uploadService.getUploads(1, 20),
  });
  const history: UploadListItem[] = (historyData as any)?.items ?? [];

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file || !selectedSource) return;
    setState('uploading');
    setError('');
    try {
      const res = await uploadService.uploadFile(file, selectedSource);
      setResult(res);
      setState('success');
      // Invalidate upload history + dashboard summary
      queryClient.invalidateQueries({ queryKey: queryKeys.uploads(1) });
      queryClient.invalidateQueries({ queryKey: queryKeys.summary() });
    } catch (err: any) {
      setError(err.response?.data?.error ?? err.message ?? 'Upload failed');
      setState('error');
    }
  };

  const reset = () => { setState('idle'); setFile(null); setResult(null); setError(''); };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="text-base font-semibold text-text-primary">Data Ingestion</h1>
          <p className="text-xs text-text-muted mt-0.5">Upload SAP, utility, or corporate travel files for normalization and review.</p>
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Upload form */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-4 space-y-4">
            <h2 className="text-sm font-semibold text-text-primary">Upload File</h2>

            <div>
              <label className="block text-xs text-text-muted mb-1.5">Data Source *</label>
              <select className="select w-full" value={selectedSource}
                onChange={e => setSelectedSource(e.target.value)}>
                <option value="">— Select source —</option>
                {dataSources.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name} ({srcTypeLabel[ds.sourceType] ?? ds.sourceType})
                  </option>
                ))}
              </select>
            </div>

            <div
              onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                dragging ? 'border-accent-blue bg-blue-900/10'
                : file   ? 'border-accent-green bg-green-900/10'
                : 'border-border hover:border-border hover:bg-surface-2'
              }`}
            >
              <input ref={fileRef} type="file" accept=".csv,.json" className="hidden"
                onChange={e => setFile(e.target.files?.[0] ?? null)} />
              {file ? (
                <div className="space-y-1">
                  <FileText className="w-6 h-6 text-accent-green mx-auto" />
                  <div className="text-sm text-text-primary font-medium">{file.name}</div>
                  <div className="text-xs text-text-muted">{(file.size / 1024).toFixed(1)} KB</div>
                  <button onClick={e => { e.stopPropagation(); setFile(null); }}
                    className="text-xs text-accent-red hover:underline mt-1">Remove</button>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <ArrowUpCircle className="w-7 h-7 text-text-muted mx-auto" />
                  <div className="text-sm text-text-secondary">Drop file here or <span className="text-accent-blue">browse</span></div>
                  <div className="text-xs text-text-muted">CSV or JSON · max 50 MB</div>
                </div>
              )}
            </div>

            {(state === 'idle' || state === 'error') && (
              <button onClick={handleUpload} disabled={!file || !selectedSource}
                className="btn-primary w-full justify-center">
                <Upload className="w-4 h-4" /> Ingest File
              </button>
            )}
            {state === 'uploading' && (
              <button disabled className="btn-primary w-full justify-center opacity-70">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing...
              </button>
            )}

            {state === 'error' && (
              <div className="flex items-start gap-2 bg-red-900/20 border border-accent-red/30 rounded p-3">
                <AlertCircle className="w-4 h-4 text-accent-red flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm text-accent-red font-medium">Upload failed</div>
                  <div className="text-xs text-text-secondary mt-0.5">{errorMsg}</div>
                </div>
              </div>
            )}

            {state === 'success' && result && (
              <div className="space-y-3">
                <div className="flex items-start gap-2 bg-green-900/20 border border-accent-green/30 rounded p-3">
                  <CheckCircle className="w-4 h-4 text-accent-green flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm text-accent-green font-medium">Ingestion complete</div>
                    <div className="text-xs text-text-secondary mt-0.5">
                      {result.rowCount} records processed · {result.flaggedCount} flagged
                    </div>
                  </div>
                </div>
                <button onClick={reset} className="btn-ghost w-full justify-center">Upload Another File</button>
              </div>
            )}
          </div>

          {/* Format guide */}
          <div className="card p-4 space-y-3">
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Expected Formats</h3>
            {[
              { type: 'SAP Fuel CSV', cols: 'Buchungskreis, Plant, Fuel_Type, Menge, Einheit, Datum' },
              { type: 'Utility CSV', cols: 'Meter ID, Billing Start, Billing End, kWh, Tariff' },
              { type: 'Concur JSON', cols: 'employeeId, tripType, from, to, distanceKm, tripDate' },
            ].map(f => (
              <div key={f.type}>
                <div className="text-xs font-medium text-text-secondary">{f.type}</div>
                <div className="text-[11px] text-text-muted mono mt-0.5">{f.cols}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Upload history */}
        <div className="lg:col-span-3">
          <div className="card">
            <div className="px-4 py-3 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">Upload History</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>File</th><th>Source</th><th>Rows</th>
                    <th>Status</th><th>By</th><th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {historyLoading && <TableBodySkeleton rows={4} cols={6} />}
                  {!historyLoading && history.length === 0 && (
                    <tr><td colSpan={6} className="text-center text-text-muted py-6">No uploads yet</td></tr>
                  )}
                  {history.map(u => (
                    <tr key={u.id}>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-text-muted flex-shrink-0" />
                          <span className="text-xs max-w-[180px] truncate" title={u.fileName}>{u.fileName}</span>
                        </div>
                        {u.errorSummary && (
                          <div className="text-[10px] text-accent-red mt-0.5 truncate max-w-[180px]" title={u.errorSummary}>
                            {u.errorSummary}
                          </div>
                        )}
                      </td>
                      <td><span className="mono text-xs">{u.sourceType}</span></td>
                      <td className="text-xs">{u.rowCount}</td>
                      <td>
                        <span className={`badge text-[10px] ${
                          u.status === 'Completed' ? 'badge-approved' :
                          u.status === 'Failed' ? 'badge-flagged' : 'badge-pending'
                        }`}>{u.status}</span>
                      </td>
                      <td className="text-xs text-text-muted">{u.uploadedBy}</td>
                      <td className="text-xs text-text-muted">{new Date(u.createdAt).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
