import React, { useState } from 'react'
import { useAuth } from '../lib/auth'
import IdentityModal from './IdentityModal'

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
  { id: 'access_control', label: 'Access Control & IAM', phase: 'Admin' },
  { id: 'governance', label: 'Security & Audit Logs', phase: 'Phase 6' },
]

export default function Sidebar({ active, onNavigate }: Props) {
  const { user, role, logout } = useAuth()
  const [showIdentityModal, setShowIdentityModal] = useState(false)

  const getInitials = (name?: string, fallback: string = 'FG') => {
    if (!name) return fallback.slice(0, 2).toUpperCase()
    const parts = name.trim().split(/\s+/)
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  const roleLabel =
    role === 'ADMIN'
      ? 'Administrator'
      : role === 'ANALYST'
      ? 'Risk Analyst'
      : 'Auditor (Viewer)'

  return (
    <>
      <aside className="w-64 bg-slate-50 border-r border-slate-200 p-4 flex flex-col justify-between shrink-0 select-none">
        <div className="overflow-y-auto">
          {/* Brand Header */}
          <div className="flex items-center space-x-2.5 px-2 py-3 mb-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm tracking-tight">
              FG
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 tracking-tight leading-none">FinGuard AI</h2>
              <p className="text-[10px] text-slate-500 font-medium mt-1">Expert Financial Intelligence</p>
            </div>
          </div>

          {/* Signed-In User Profile Card */}
          <div className="mx-1 mb-4 p-3 bg-white rounded-xl border border-slate-200/90 shadow-xs space-y-2.5">
            <div className="flex items-center space-x-2.5">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-xs shadow-xs shrink-0 ${
                  role === 'ADMIN'
                    ? 'bg-purple-600 ring-2 ring-purple-100'
                    : role === 'ANALYST'
                    ? 'bg-blue-600 ring-2 ring-blue-100'
                    : 'bg-slate-600 ring-2 ring-slate-100'
                }`}
              >
                {getInitials(user?.full_name || user?.username)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-slate-900 truncate leading-tight">
                  {user ? (user.full_name || user.username) : 'Signed In'}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <p className="text-[10px] text-slate-500 font-mono truncate">
                    @{user ? user.username : '...'}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1 border-t border-slate-100">
              <span
                className={`text-[9.5px] px-2 py-0.5 rounded-md font-bold font-mono border ${
                  role === 'ADMIN'
                    ? 'bg-purple-50 text-purple-700 border-purple-200'
                    : role === 'ANALYST'
                    ? 'bg-blue-50 text-blue-700 border-blue-200'
                    : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                {roleLabel}
              </span>
              <button
                type="button"
                onClick={() => logout()}
                className="text-[10px] text-slate-400 hover:text-rose-600 font-medium transition"
                title="Sign Out"
              >
                Sign Out
              </button>
            </div>

            <button
              type="button"
              onClick={() => setShowIdentityModal(true)}
              className="w-full mt-1 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200/80 text-slate-700 font-semibold text-[11px] rounded-lg transition flex items-center justify-center gap-1.5"
            >
              <span>⚙️</span>
              <span>Manage Identity & Security</span>
            </button>
          </div>

          {/* Navigation Items */}
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
                          isActive
                            ? 'bg-blue-700 text-blue-100'
                            : item.phase === 'Admin'
                            ? 'bg-purple-100 text-purple-700 font-bold'
                            : 'bg-slate-200/70 text-slate-500'
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
            <span className="font-mono text-emerald-600 font-semibold">RBAC Enforced</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-700">Audit Chain</span>
            <span className="font-mono text-blue-600">SHA-256 Chained</span>
          </div>
        </div>
      </aside>

      {/* Identity & Account Modal */}
      <IdentityModal
        isOpen={showIdentityModal}
        onClose={() => setShowIdentityModal(false)}
        onNavigateToAccessControl={() => {
          setShowIdentityModal(false)
          onNavigate('access_control')
        }}
      />
    </>
  )
}
