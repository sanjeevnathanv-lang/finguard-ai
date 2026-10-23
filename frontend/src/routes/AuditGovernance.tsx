import React, { useEffect, useState } from 'react'
import { useAuth } from '../lib/auth'
import {
  UserProfile,
  AuditLogEntry,
  AuditVerificationResult,
  SystemReadiness,
  getUsersApi,
  createUserApi,
  updateUserStatusApi,
  updateUserRoleApi,
  getAuditLogsApi,
  verifyAuditChainApi,
  getSystemReadinessApi,
  UserRole,
} from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'

interface AuditGovernanceProps {
  initialTab?: 'audit' | 'users' | 'diagnostics'
}

export default function AuditGovernance({ initialTab = 'audit' }: AuditGovernanceProps) {
  const { role, user: currentUser } = useAuth()
  const isAdmin = role === 'ADMIN'

  const [activeTab, setActiveTab] = useState<'audit' | 'users' | 'diagnostics'>(initialTab)

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab)
    }
  }, [initialTab])

  // Audit Log State
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([])
  const [totalLogs, setTotalLogs] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(25)
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('')
  const [actorFilter, setActorFilter] = useState<string>('')
  const [loadingLogs, setLoadingLogs] = useState<boolean>(true)

  // Verification State
  const [verification, setVerification] = useState<AuditVerificationResult | null>(null)
  const [verifying, setVerifying] = useState<boolean>(false)

  // Users State
  const [users, setUsers] = useState<UserProfile[]>([])
  const [loadingUsers, setLoadingUsers] = useState<boolean>(false)
  const [showAddUserModal, setShowAddUserModal] = useState<boolean>(false)

  // Role Update State
  const [roleChangeTarget, setRoleChangeTarget] = useState<{ user: UserProfile; newRole: UserRole } | null>(null)
  const [roleUpdating, setRoleUpdating] = useState<boolean>(false)
  const [roleError, setRoleError] = useState<string | null>(null)

  // User form
  const [newUsername, setNewUsername] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newFullName, setNewFullName] = useState('')
  const [newRole, setNewRole] = useState<UserRole>('ANALYST')

  // Diagnostics State
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null)
  const [loadingDiag, setLoadingDiag] = useState<boolean>(false)

  // Load Audit Logs
  const loadAuditLogs = async () => {
    if (!isAdmin) return
    setLoadingLogs(true)
    try {
      const res = await getAuditLogsApi({
        event_type: eventTypeFilter || undefined,
        actor_username: actorFilter || undefined,
        page,
        page_size: pageSize,
      })
      setAuditLogs(res.items)
      setTotalLogs(res.total)
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoadingLogs(false)
    }
  }

  // Load Users
  const loadUsers = async () => {
    if (!isAdmin) return
    setLoadingUsers(true)
    try {
      const data = await getUsersApi()
      setUsers(data)
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoadingUsers(false)
    }
  }

  // Load Diagnostics
  const loadDiagnostics = async () => {
    setLoadingDiag(true)
    try {
      const diag = await getSystemReadinessApi()
      setReadiness(diag)
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoadingDiag(false)
    }
  }

  // Run Hash Chain Verification
  const handleVerifyChain = async () => {
    setVerifying(true)
    try {
      const res = await verifyAuditChainApi()
      setVerification(res)
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`)
    } finally {
      setVerifying(false)
    }
  }

  // Toggle user activation
  const handleToggleUser = async (u: UserProfile) => {
    if (u.id === currentUser?.id) {
      alert('You cannot deactivate your own active administrator account.')
      return
    }
    const action = u.is_active ? 'deactivate' : 'activate'
    if (!confirm(`Are you sure you want to ${action} user '${u.username}'?`)) return
    try {
      await updateUserStatusApi(u.id, !u.is_active)
      await loadUsers()
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Create user
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createUserApi({
        username: newUsername.trim(),
        email: newEmail.trim(),
        password: newPassword,
        full_name: newFullName.trim() || undefined,
        role: newRole,
      })
      setShowAddUserModal(false)
      setNewUsername('')
      setNewEmail('')
      setNewPassword('')
      setNewFullName('')
      await loadUsers()
      alert('User provisioned successfully.')
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle role modification
  const handleConfirmRoleChange = async () => {
    if (!roleChangeTarget) return
    setRoleUpdating(true)
    setRoleError(null)
    try {
      await updateUserRoleApi(roleChangeTarget.user.id, roleChangeTarget.newRole)
      setRoleChangeTarget(null)
      await loadUsers()
    } catch (err: any) {
      setRoleError(err.message || 'Failed to update user role.')
    } finally {
      setRoleUpdating(false)
    }
  }

  useEffect(() => {
    if (isAdmin) {
      loadAuditLogs()
      if (activeTab === 'users') loadUsers()
    }
    if (activeTab === 'diagnostics') loadDiagnostics()
  }, [activeTab, page, eventTypeFilter, isAdmin])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Security, Audit & Access Governance
            </h1>
            <span
              className={`px-2.5 py-0.5 rounded text-[11px] font-bold border ${
                isAdmin
                  ? 'bg-purple-100 text-purple-800 border-purple-300'
                  : 'bg-blue-100 text-blue-800 border-blue-300'
              }`}
            >
              Role: {role}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Attributable security events, cryptographic SHA-256 hash-chain verification, and role-based access governance
          </p>
        </div>

        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleVerifyChain}
              disabled={verifying}
              className="px-3.5 py-2 bg-slate-900 hover:bg-black text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <span>{verifying ? 'Verifying Hashes...' : '🔐 Run Hash Chain Verification'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Access Warning if not Admin */}
      {!isAdmin && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1">
          <h4 className="font-bold text-amber-900">Restricted Administrator Area</h4>
          <p className="text-amber-800">
            Audit log entries, user provisioning, and role modifications require the <strong>ADMIN</strong> role. You are currently logged in with the <strong>{role}</strong> role. Backend RBAC policies strictly enforce these boundaries.
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`pb-3 transition-colors ${
            activeTab === 'audit'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Audit Log & Cryptographic Chain
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('users')}
          className={`pb-3 transition-colors ${
            activeTab === 'users'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Access Control & IAM {isAdmin ? `(${users.length || '...'})` : ''}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('diagnostics')}
          className={`pb-3 transition-colors ${
            activeTab === 'diagnostics'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          Operational Readiness & Diagnostics
        </button>
      </div>

      {/* ================= TAB 1: AUDIT LOG & HASH CHAIN ================= */}
      {activeTab === 'audit' && (
        <div className="space-y-5">
          {/* Hash Chain Verification Result Banner */}
          {verification && (
            <div
              className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                verification.is_valid
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-rose-50 border-rose-200 text-rose-900'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm">
                  {verification.is_valid ? '✓ Cryptographic Hash Chain: VERIFIED' : '⚠ Tamper Warning: INTEGRITY CORRUPTED'}
                </span>
                <span className="font-mono text-[11px] opacity-75">
                  Records Verified: {verification.total_records_checked}
                </span>
              </div>
              <p className="leading-relaxed">{verification.message}</p>
              {verification.latest_hash && (
                <div className="font-mono text-[10px] opacity-80 truncate">
                  Latest Block Digest: {verification.latest_hash}
                </div>
              )}
            </div>
          )}

          {/* Cryptographic Architecture Notice */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
            <h4 className="font-bold text-slate-800">Tamper-Evident SHA-256 Hash Chaining Architecture</h4>
            <p className="text-slate-600 leading-relaxed">
              Every sensitive action appends a canonical structured event linked to the cryptographic digest of the prior entry (Hash_k = SHA-256(Canonical_k || Hash_k-1)). This mathematical link detects out-of-order alterations, row tampering, or unauthorized record deletion.
            </p>
            <p className="text-[11px] text-slate-500 italic">
              Formal Limitation Disclosure: A hash chain in SQLite guarantees tamper-evidence against application-level modifications; absolute immutability against direct host file system rewrite requires external WORM storage.
            </p>
          </div>

          {/* Filters Bar */}
          {isAdmin && (
            <div className="flex flex-wrap items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
              >
                <option value="">All Event Types</option>
                <option value="AUTH_LOGIN_SUCCESS">AUTH_LOGIN_SUCCESS</option>
                <option value="AUTH_LOGIN_FAILED">AUTH_LOGIN_FAILED</option>
                <option value="USER_CREATED">USER_CREATED</option>
                <option value="CASE_CREATED">CASE_CREATED</option>
                <option value="CASE_CLOSED">CASE_CLOSED</option>
                <option value="CASE_REPORT_EXPORTED">CASE_REPORT_EXPORTED</option>
                <option value="ASSESSMENT_PERFORMED">ASSESSMENT_PERFORMED</option>
                <option value="TRANSACTION_CSV_UPLOADED">TRANSACTION_CSV_UPLOADED</option>
              </select>

              <button
                type="button"
                onClick={loadAuditLogs}
                className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition"
              >
                Refresh Log
              </button>
            </div>
          )}

          {/* Table */}
          {loadingLogs ? (
            <div className="py-16 flex justify-center">
              <LoadingSpinner />
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-white text-xs text-slate-500">
              {isAdmin ? 'No audit entries found matching the filter.' : 'Audit logs require Administrator privileges.'}
            </div>
          ) : (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-4">Event Type</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Reference</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 font-mono">Event Digest (SHA-256)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60 font-mono text-[11px]">
                      <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-sans font-semibold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[10px]">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-800">
                        {log.actor_username}{' '}
                        {log.actor_role && (
                          <span className="text-[10px] text-slate-400 font-mono">({log.actor_role})</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-sans">
                        {log.record_reference || '—'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-1.5 py-0.2 rounded text-[9px] font-sans font-bold ${
                            log.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 truncate max-w-xs" title={log.event_hash}>
                        {log.event_hash}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 2: ACCESS CONTROL & IAM ================= */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          {isAdmin ? (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Platform Identity & Access Management (IAM)
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Authorized role assignments and administrative account management. Role changes are verified and audited.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(true)}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition shrink-0 self-start sm:self-auto"
                >
                  + Provision New Account
                </button>
              </div>

              {loadingUsers ? (
                <div className="py-16 flex justify-center">
                  <LoadingSpinner />
                </div>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
                        <th className="py-3 px-4">Username</th>
                        <th className="py-3 px-4">Full Name & Email</th>
                        <th className="py-3 px-4">Role Assignment</th>
                        <th className="py-3 px-4">Account Status</th>
                        <th className="py-3 px-4">Last Login</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {users.map((u) => {
                        const isSelf = u.id === currentUser?.id
                        return (
                          <tr key={u.id} className="hover:bg-slate-50/60">
                            <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                              <div className="flex items-center gap-1.5">
                                <span>{u.username}</span>
                                {isSelf && (
                                  <span className="text-[9px] font-sans font-bold bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded font-mono">
                                    YOU
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3.5 px-4">
                              <div className="font-semibold text-slate-800">{u.full_name || '—'}</div>
                              <div className="text-[11px] text-slate-400 font-mono">{u.email}</div>
                            </td>
                            <td className="py-3.5 px-4">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                    u.role === 'ADMIN'
                                      ? 'bg-purple-100 text-purple-800 border-purple-300'
                                      : u.role === 'ANALYST'
                                      ? 'bg-blue-100 text-blue-800 border-blue-300'
                                      : 'bg-slate-100 text-slate-700 border-slate-300'
                                  }`}
                                >
                                  {u.role}
                                </span>
                                <select
                                  value={u.role}
                                  disabled={isSelf}
                                  onChange={(e) => {
                                    const targetRole = e.target.value as UserRole
                                    if (targetRole !== u.role) {
                                      setRoleChangeTarget({ user: u, newRole: targetRole })
                                    }
                                  }}
                                  className="text-[10px] bg-white border border-slate-300 rounded px-1.5 py-0.5 font-medium text-slate-700 hover:border-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
                                  title={isSelf ? 'Self-demotion is restricted by system policy' : 'Modify user role'}
                                >
                                  <option value="ADMIN">ADMIN</option>
                                  <option value="ANALYST">ANALYST</option>
                                  <option value="VIEWER">VIEWER</option>
                                </select>
                              </div>
                            </td>
                            <td className="py-3.5 px-4">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-600'
                                }`}
                              >
                                {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                              {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
                            </td>
                            <td className="py-3.5 px-4 text-right">
                              <button
                                type="button"
                                disabled={isSelf}
                                onClick={() => handleToggleUser(u)}
                                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                                  isSelf
                                    ? 'text-slate-400 bg-slate-100 cursor-not-allowed'
                                    : u.is_active
                                    ? 'text-rose-700 bg-rose-50 hover:bg-rose-100'
                                    : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
                                }`}
                                title={isSelf ? 'Cannot deactivate your own account' : undefined}
                              >
                                {u.is_active ? 'Deactivate' : 'Reactivate'}
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1">
              <h4 className="font-bold text-amber-900">Access Control Administration Restricted</h4>
              <p className="text-amber-800">
                User provisioning, deactivation, and role assignments require <strong>ADMIN</strong> privileges. Your active role is <strong>{role}</strong>.
              </p>
            </div>
          )}

          {/* Role Permissions Reference Policy Matrix */}
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Role-Based Access Policy Matrix (RBAC Enforcement)
            </h4>
            <p className="text-xs text-slate-500">
              Each API request transmits a JWT bearer token verified by the FastAPI backend dependency injection pipeline. Violations return HTTP 403 Forbidden.
            </p>

            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold text-[11px]">
                    <th className="py-2.5 px-3">System Module / Endpoint Scope</th>
                    <th className="py-2.5 px-3 text-center">Auditor (Viewer)</th>
                    <th className="py-2.5 px-3 text-center">Risk Analyst</th>
                    <th className="py-2.5 px-3 text-center">Security Administrator</th>
                    <th className="py-2.5 px-3">Backend Security Rule</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">Executive Dashboard & Analytics</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Read</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Read</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Full</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_viewer</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">Transaction Analysis & Ingestion</td>
                    <td className="py-2 px-3 text-center text-slate-500">Read-Only</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Create / Assess</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Full</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_analyst</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">Batch CSV Upload Pipeline</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Upload / Validate</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Full</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_analyst</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">Investigation Case Management</td>
                    <td className="py-2 px-3 text-center text-slate-500">Read-Only</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Notes / Close / Link</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Full</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_analyst</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">ML Supervised Training Pipeline</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Execute Training</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_admin</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">Cryptographic Audit Chain Verification</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Verify Hashes</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_admin</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-medium text-slate-800">User Management & Role Assignment</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-rose-500 font-bold">✗ 403 Forbidden</td>
                    <td className="py-2 px-3 text-center text-emerald-600 font-bold">✓ Manage Roles</td>
                    <td className="py-2 px-3 font-mono text-[10px] text-slate-500">require_admin</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Role Modification */}
      {roleChangeTarget && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-2 text-slate-900">
              <span className="text-xl">🛡️</span>
              <h3 className="text-base font-bold">
                Confirm Administrative Role Change
              </h3>
            </div>

            {roleError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs">
                {roleError}
              </div>
            )}

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2 text-slate-700">
              <p>
                You are modifying the authorization role for account:
              </p>
              <div className="p-2.5 bg-white rounded-lg border border-slate-200 space-y-1">
                <div className="font-mono font-bold text-slate-900">
                  @{roleChangeTarget.user.username}
                </div>
                <div className="text-[11px] text-slate-500">
                  {roleChangeTarget.user.full_name || roleChangeTarget.user.email}
                </div>
                <div className="flex items-center gap-2 pt-1 font-semibold text-xs">
                  <span className="line-through text-slate-400">{roleChangeTarget.user.role}</span>
                  <span>➔</span>
                  <span className="font-bold text-purple-700">{roleChangeTarget.newRole}</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed pt-1">
                This administrative action is enforced directly on the backend. A new cryptographic event (<code className="bg-slate-100 px-1 py-0.5 rounded font-mono">USER_ROLE_UPDATED</code>) will be appended to the SHA-256 audit hash chain.
              </p>
            </div>

            <div className="flex justify-end space-x-2.5 pt-2">
              <button
                type="button"
                disabled={roleUpdating}
                onClick={() => {
                  setRoleChangeTarget(null)
                  setRoleError(null)
                }}
                className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={roleUpdating}
                onClick={handleConfirmRoleChange}
                className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center space-x-1.5"
              >
                {roleUpdating && <LoadingSpinner />}
                <span>Confirm & Update Role</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 3: DIAGNOSTICS & READINESS ================= */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-xs">
            <h4 className="font-bold text-slate-900">Application Readiness & Dependency Diagnostics</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[11px] text-slate-500 font-semibold block">Liveness Status</span>
                <span className="text-base font-bold text-emerald-600 mt-1 block">ONLINE (200 OK)</span>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[11px] text-slate-500 font-semibold block">SQLite Connection</span>
                <span className="text-base font-bold text-emerald-600 mt-1 block">
                  {readiness?.database === 'connected' ? 'CONNECTED' : 'CHECKING...'}
                </span>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[11px] text-slate-500 font-semibold block">Expert Rules Loaded</span>
                <span className="text-base font-bold text-blue-600 mt-1 block">
                  {readiness ? `${readiness.knowledge_base_rules} Active Rules` : '7 Rules'}
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={loadDiagnostics}
              className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition"
            >
              Re-probe System Readiness
            </button>
          </div>
        </div>
      )}

      {/* Modal: Create User */}
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-900">Provision Platform Account</h3>
              <button
                type="button"
                onClick={() => setShowAddUserModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Username *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. investigator_dan"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. dan@finguard.ai"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Daniel Miller"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Access Role</label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as UserRole)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="ANALYST">ANALYST</option>
                    <option value="VIEWER">VIEWER</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Initial Password *</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    placeholder="Min 8 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(false)}
                  className="px-3.5 py-1.5 text-slate-600 hover:bg-slate-100 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
