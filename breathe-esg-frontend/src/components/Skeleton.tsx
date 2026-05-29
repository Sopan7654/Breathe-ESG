/**
 * components/Skeleton.tsx
 * Reusable loading skeleton components.
 * Shows animated placeholders instead of blank screens while data loads.
 */

/** Single shimmer block */
export function SkeletonBlock({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-surface-3 rounded ${className}`} />
  );
}

/** Stat card skeleton — matches StatCard dimensions */
export function StatCardSkeleton() {
  return (
    <div className="stat-card space-y-3">
      <div className="flex items-center justify-between">
        <SkeletonBlock className="h-2.5 w-20" />
        <SkeletonBlock className="h-4 w-4 rounded-full" />
      </div>
      <SkeletonBlock className="h-7 w-12" />
    </div>
  );
}

/** Table row skeletons */
export function TableRowSkeleton({ cols = 11 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="py-2 px-3">
          <SkeletonBlock className="h-3 w-full" />
        </td>
      ))}
    </tr>
  );
}

/** Multiple table rows */
export function TableBodySkeleton({ rows = 8, cols = 11 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <TableRowSkeleton key={i} cols={cols} />
      ))}
    </>
  );
}
