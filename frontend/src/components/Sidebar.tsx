import React from 'react'
import { useAuth } from '../lib/auth'
import { UserRole } from '../lib/api'

type Props = {
  active: string
  onNavigate: (page: string) => void
}

const items = [
  { id: 'dashboard', label: 'Executive Dashboard', phase: 'Live' },
  { id: 'transactions', label: 'Transaction Analysis', phase: 'Realtime' },
  { id: 'csv_import', label: 'CSV Batch Ingestion', phase: 'Active' },
  { id: 'rules', label: 'Expert Rules Engine', phase: 'Active' },
  { id: 'models', label: 'ML & Pattern Intelligence', phase: 'Active' },
  { id: 'investigations', label: 'Investigation Cases', phase: 'Active' },
  { id: 'governance', label: 'Security & Audit Logs', phase: 'Phase 6' },
]

export default function Sidebar({ active, onNavigate }: Props) {
  const { user, role, quickSwitchUser, isLoading } = useAuth()

  return (
    <aside className="w-64 bg-slate-50 border-r border-slate-200 p-4 flex flex-col justify-between shrink-0 select-none">
      <div className="overflow-y-auto">
        <div className="flex items-center space-x-2.5 px-2 py-3 mb-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm tracking-tight">
            FG
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight leading-none">FinGuard AI</h2>
            <p className="text-[10px] text-slate-500 font-medium mt-1">Expert Financial Intelligence</p>
          </div>
        </div>

        {/* User Session & Role Card */}
        <div className="mx-1 mb-4 p-2.5 bg-white rounded-lg border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Active Identity</span>
            <span
              className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${
                role === 'ADMIN'
                  ? 'bg-purple-100 text-purple-800'
                  : role === 'ANALYST'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-slate-100 text-slate-700'
              }`}
            >
              {role}
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-900 truncate">
            {user ? user.full_name : 'Loading session...'}
          </p>
          <p className="text-[10px] text-slate-500 font-mono truncate">
            @{user ? user.username : '...'}
          </p>

          <div className="mt-2.5 pt-2 border-t border-slate-100">
            <label className="block text-[9px] font-medium text-slate-500 mb-1">
              Switch Role (Dev / Audit):
            </label>
            <div className="grid grid-cols-3 gap-1">
              {(['ADMIN', 'ANALYST', 'VIEWER'] as UserRole[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  disabled={isLoading || role === r}
                  onClick={() => quickSwitchUser(r)}
                  className={`text-[9px] font-mono py-1 rounded transition text-center ${
                    role === r
                      ? 'bg-blue-600 text-white font-bold'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                  title={`Switch active session to ${r}`}
                >
                  {r.slice(0, 3)}
                </button>
              ))}
            </div>
          </div>
        </div>

        <nav>
          <ul className="space-y-1">
            {items.map((item) => {
              const isActive = active === item.id
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => onNavigate(item.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-between transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
                    }`}
                  >
                    <span>{item.label}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                        isActive ? 'bg-blue-700 text-blue-100' : 'bg-slate-200/70 text-slate-500'
                      }`}
                    >
                      {item.phase}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>

      <div className="pt-3 border-t border-slate-200 px-2 text-[11px] text-slate-500 space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-700">Access Control</span>
          <span className="font-mono text-emerald-600 font-semibold">RBAC Active</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-700">Audit Chain</span>
          <span className="font-mono text-blue-600">SHA-256 Chained</span>
        </div>
      </div>
    </aside>
  )
}
