import React, { useState } from 'react'
import { useAuth } from '../lib/auth'
import { UserRole, changePasswordApi } from '../lib/api'
import LoadingSpinner from './LoadingSpinner'

interface IdentityModalProps {
  isOpen: boolean
  onClose: () => void
  onNavigateToAccessControl?: () => void
}

const SEEDED_IDENTITIES: { role: UserRole; username: string; label: string; desc: string }[] = [
  {
    role: 'ADMIN',
    username: 'admin',
    label: 'Security Administrator',
    desc: 'Full administrative access: user & role provisioning, SHA-256 cryptographic audit verification, model training.',
  },
  {
    role: 'ANALYST',
    username: 'analyst',
    label: 'Financial Risk Analyst',
    desc: 'Operational review: transaction risk assessments, batch CSV ingestion, case investigations, timeline notes, and dispositions.',
  },
  {
    role: 'VIEWER',
    username: 'viewer',
    label: 'Auditor / Viewer',
    desc: 'Strictly read-only access: review dashboards, rules, transactions, and cases. All write and assessment actions blocked.',
  },
]

export default function IdentityModal({
  isOpen,
  onClose,
  onNavigateToAccessControl,
}: IdentityModalProps) {
  const { user, role, quickSwitchUser, logout, isLoading } = useAuth()

  const [activeTab, setActiveTab] = useState<'profile' | 'permissions' | 'simulator'>('profile')

  // Change Password form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)

  // Role Simulator Confirmation Dialog state
  const [confirmingTargetRole, setConfirmingTargetRole] = useState<UserRole | null>(null)
  const [simulatorError, setSimulatorError] = useState<string | null>(null)

  if (!isOpen) return null

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(null)

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.')
      return
    }

    setPasswordLoading(true)
    try {
      await changePasswordApi(currentPassword, newPassword)
      setPasswordSuccess('Password successfully updated and recorded in the audit log.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      setPasswordError(err.message || 'Failed to update password.')
    } finally {
      setPasswordLoading(false)
    }
  }

  const handleExecuteRoleSwitch = async () => {
    if (!confirmingTargetRole) return
    setSimulatorError(null)
    try {
      await quickSwitchUser(confirmingTargetRole)
      setConfirmingTargetRole(null)
      onClose()
    } catch (err: any) {
      setSimulatorError(err.message || 'Failed to authenticate as simulated role.')
    }
  }

  const getInitials = (name?: string, fallback: string = 'FG') => {
    if (!name) return fallback.slice(0, 2).toUpperCase()
    const parts = name.trim().split(/\s+/)
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/80">
          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-xs ${
                role === 'ADMIN'
                  ? 'bg-purple-600'
                  : role === 'ANALYST'
                  ? 'bg-blue-600'
                  : 'bg-slate-600'
              }`}
            >
              {getInitials(user?.full_name || user?.username)}
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 leading-snug">
                Account & Identity Management
              </h3>
              <p className="text-xs text-slate-500">
                Active Session: <span className="font-mono font-semibold text-slate-700">@{user?.username || 'user'}</span> · Role: <span className="font-semibold text-slate-700">{role}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200/60 transition"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 px-6 space-x-6 text-xs font-semibold bg-white">
          <button
            type="button"
            onClick={() => setActiveTab('profile')}
            className={`py-3 transition-colors ${
              activeTab === 'profile'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Signed-In Profile
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('permissions')}
            className={`py-3 transition-colors ${
              activeTab === 'permissions'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Access Policy Matrix
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('simulator')}
            className={`py-3 transition-colors flex items-center space-x-1.5 ${
              activeTab === 'simulator'
                ? 'border-b-2 border-purple-600 text-purple-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Role Simulator</span>
            <span className="text-[9px] px-1.5 py-0.2 rounded font-mono bg-purple-100 text-purple-700 font-bold">
              Dev Only
            </span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* ================= TAB 1: PROFILE ================= */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {/* Profile Card */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Identity Attributes
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      role === 'ADMIN'
                        ? 'bg-purple-100 text-purple-800 border-purple-300'
                        : role === 'ANALYST'
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-slate-100 text-slate-700 border-slate-300'
                    }`}
                  >
                    {role === 'ADMIN' ? 'Security Administrator' : role === 'ANALYST' ? 'Risk Analyst' : 'Auditor (Viewer)'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div>
                    <span className="text-[11px] text-slate-500 block">Full Name:</span>
                    <span className="text-sm font-bold text-slate-900 block">{user?.full_name || '—'}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block">Username:</span>
                    <span className="text-sm font-mono font-bold text-slate-900 block">@{user?.username}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block">Email Address:</span>
                    <span className="text-xs text-slate-700 font-mono block">{user?.email || '—'}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block">Account Status:</span>
                    <span className="text-xs text-emerald-700 font-semibold inline-flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Active & Authenticated
                    </span>
                  </div>
                </div>

                {role === 'ADMIN' && onNavigateToAccessControl && (
                  <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                    <div>
                      <p className="text-[11px] font-semibold text-slate-800">
                        Authorized Administrator Privileges
                      </p>
                      <p className="text-[10px] text-slate-500">
                        Manage user roles, provision accounts, and inspect cryptographic audit chains.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        onClose()
                        onNavigateToAccessControl()
                      }}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-xs transition"
                    >
                      Access Control & Users →
                    </button>
                  </div>
                )}
              </div>

              {/* Change Password Form */}
              <form onSubmit={handlePasswordSubmit} className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Update Account Password
                </h4>
                <p className="text-[11px] text-slate-500">
                  Password changes are encrypted with 12-round bcrypt and recorded into the audit log.
                </p>

                {passwordError && (
                  <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-[11px]">
                    {passwordError}
                  </div>
                )}
                {passwordSuccess && (
                  <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-[11px]">
                    {passwordSuccess}
                  </div>
                )}

                <div className="space-y-2.5">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">Current Password</label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                      placeholder="••••••••"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">New Password (min 8 chars)</label>
                      <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                        placeholder="••••••••"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-0.5">Confirm New Password</label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={passwordLoading}
                    className="px-3.5 py-1.5 bg-slate-900 hover:bg-black text-white font-semibold text-xs rounded-lg shadow-xs transition flex items-center space-x-1.5"
                  >
                    {passwordLoading && <LoadingSpinner />}
                    <span>Update Password</span>
                  </button>
                </div>
              </form>

              {/* Sign Out Action */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-200">
                <span className="text-[11px] text-slate-500">
                  Terminate current session and clear local token.
                </span>
                <button
                  type="button"
                  onClick={async () => {
                    await logout()
                    onClose()
                  }}
                  className="px-3 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}

          {/* ================= TAB 2: PERMISSIONS MATRIX ================= */}
          {activeTab === 'permissions' && (
            <div className="space-y-4">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs">
                <span className="font-bold">Backend-Enforced Authorization:</span> Every API endpoint verifies incoming JWT claims on the FastAPI backend. Attempts by unauthorized roles return HTTP 403 Forbidden.
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold text-[11px]">
                      <th className="py-2.5 px-3">System Capability</th>
                      <th className="py-2.5 px-3 text-center">Viewer</th>
                      <th className="py-2.5 px-3 text-center">Risk Analyst</th>
                      <th className="py-2.5 px-3 text-center">Administrator</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Executive Dashboard & Analytics</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Read</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Read</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Full</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Execute Transaction AI Assessments</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Batch CSV Ingestion & Creation</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Investigation Case Creation & Disposition</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Supervised Model Training Pipeline</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">Cryptographic Audit Log Verification</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-slate-800">User Role Management & Status</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-rose-500 font-bold">✗ 403</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 font-bold">✓ Allowed</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================= TAB 3: ROLE SIMULATOR ================= */}
          {activeTab === 'simulator' && (
            <div className="space-y-4">
              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-xs">
                  <span>⚠️ Isolated Development Identity Simulator</span>
                </div>
                <p className="text-[11px] leading-relaxed">
                  This tool is strictly provided for local academic demonstration and evaluation. Selecting a role terminates your active session and authenticates against the pre-seeded account on the FastAPI backend, issuing a genuine role-scoped JWT token.
                </p>
                <p className="text-[10px] text-amber-800 font-mono">
                  Never grants client-side privileges without backend authentication. Explicit confirmation is required.
                </p>
              </div>

              {simulatorError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs">
                  {simulatorError}
                </div>
              )}

              <div className="grid grid-cols-1 gap-3">
                {SEEDED_IDENTITIES.map((ident) => {
                  const isCurrent = role === ident.role && user?.username === ident.username
                  return (
                    <div
                      key={ident.role}
                      className={`p-3.5 rounded-xl border transition flex items-center justify-between ${
                        isCurrent
                          ? 'bg-blue-50/60 border-blue-300'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-xs">{ident.label}</span>
                          <span className="text-[10px] font-mono text-slate-500">(@{ident.username})</span>
                          {isCurrent && (
                            <span className="text-[9px] font-bold bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded font-mono">
                              ACTIVE SESSION
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-600 max-w-md">{ident.desc}</p>
                      </div>

                      <button
                        type="button"
                        disabled={isCurrent || isLoading}
                        onClick={() => setConfirmingTargetRole(ident.role)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition shrink-0 ml-3 ${
                          isCurrent
                            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                            : 'bg-slate-900 hover:bg-black text-white shadow-xs'
                        }`}
                      >
                        {isCurrent ? 'Current' : 'Simulate Role →'}
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50/60 flex justify-between items-center text-xs text-slate-500">
          <span>Security Architecture: 12-round Bcrypt + HS256 JWT</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 border border-slate-300 rounded-lg hover:bg-white text-slate-700 font-semibold transition"
          >
            Close
          </button>
        </div>
      </div>

      {/* Confirmation Modal for Role Simulation */}
      {confirmingTargetRole && (
        <div className="fixed inset-0 z-60 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-2 text-amber-700">
              <span className="text-xl">⚠️</span>
              <h3 className="text-base font-bold text-slate-900">
                Confirm Simulated Identity Switch
              </h3>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5 text-slate-700">
              <p>
                You are about to switch from your current session (<strong>@{user?.username}</strong>, {role}) and authenticate as:
              </p>
              <div className="p-2 bg-white rounded border border-slate-200 font-mono font-bold text-slate-900 flex items-center justify-between">
                <span>{confirmingTargetRole}</span>
                <span className="text-[11px] text-slate-500">
                  Account: @{confirmingTargetRole.toLowerCase()}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                The FastAPI backend will issue a new JWT session strictly scoped to <strong>{confirmingTargetRole}</strong> authorization claims.
              </p>
            </div>

            <div className="flex justify-end space-x-2.5 pt-2">
              <button
                type="button"
                disabled={isLoading}
                onClick={() => setConfirmingTargetRole(null)}
                className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isLoading}
                onClick={handleExecuteRoleSwitch}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center space-x-1.5"
              >
                {isLoading && <LoadingSpinner />}
                <span>Confirm & Authenticate</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
