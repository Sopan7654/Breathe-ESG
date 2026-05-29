import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Upload, ClipboardList, History,
  AlertTriangle, Leaf
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/review', label: 'Review', icon: ClipboardList },
  { to: '/audit', label: 'Audit Log', icon: History },
  { to: '/flags', label: 'Flags', icon: AlertTriangle },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
          <div className="w-7 h-7 rounded-md bg-accent-green/20 border border-accent-green/30 flex items-center justify-center">
            <Leaf className="w-4 h-4 text-accent-green" />
          </div>
          <div>
            <div className="text-sm font-semibold text-text-primary">Breathe ESG</div>
            <div className="text-[10px] text-text-muted">Operations Platform</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

{/*         
        <div className="px-4 py-3 border-t border-border">
          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Company</div>
          <div className="text-xs text-text-secondary font-medium">Acme Industries Ltd.</div>
          <div className="text-[10px] text-text-muted mt-0.5 mono">
            {import.meta.env.VITE_ANALYST_NAME || 'Analyst'}
          </div>
        </div> */}
      </aside>

      {/* ── Main content ── */}
      <main className="main-content flex-1">
        {children}
      </main>
    </div>
  );
}
