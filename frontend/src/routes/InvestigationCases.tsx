import React, { useEffect, useState } from 'react'
import {
  getCases,
  getCaseById,
  createCase,
  updateCase,
  linkTransactionToCase,
  unlinkTransactionFromCase,
  addCaseNote,
  closeCase,
  getCaseTimeline,
  getRelatedTransactions,
  exportCaseReport,
  CaseItem,
  CaseStatus,
  CasePriority,
  CaseDisposition,
  CaseTimelineEvent,
  RelatedTransaction,
  CaseExportResponse,
} from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../lib/auth'

export default function InvestigationCases() {
  const { role, user } = useAuth()
  const isViewer = role === 'VIEWER'

  // Navigation / Selected Case
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<'transactions' | 'related' | 'timeline' | 'notes'>('transactions')

  // Case List state
  const [cases, setCases] = useState<CaseItem[]>([])
  const [totalCases, setTotalCases] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(15)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [priorityFilter, setPriorityFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Detail Sub-states
  const [timeline, setTimeline] = useState<CaseTimelineEvent[]>([])
  const [timelineAsc, setTimelineAsc] = useState<boolean>(true)
  const [relatedTxns, setRelatedTxns] = useState<RelatedTransaction[]>([])
  const [loadingRelated, setLoadingRelated] = useState<boolean>(false)

  // Modals & Action States
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false)
  const [showCloseModal, setShowCloseModal] = useState<boolean>(false)
  const [showExportModal, setShowExportModal] = useState<boolean>(false)
  const [exportData, setExportData] = useState<CaseExportResponse | null>(null)

  // Forms
  const [newTitle, setNewTitle] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [newPriority, setNewPriority] = useState<CasePriority>('MEDIUM')
  const [newReviewer, setNewReviewer] = useState('')
  const [newInitialTxnId, setNewInitialTxnId] = useState('')
  const [newInitialNote, setNewInitialNote] = useState('')

  const [closeDisposition, setCloseDisposition] = useState<CaseDisposition>('UNVERIFIED_SUSPICION')
  const [closeNotes, setCloseNotes] = useState('')
  const [closeReviewer, setCloseReviewer] = useState('')

  const [noteInput, setNoteInput] = useState('')
  const [noteAuthor, setNoteAuthor] = useState('')

  const [linkTxnIdInput, setLinkTxnIdInput] = useState('')
  const [linkReasonInput, setLinkReasonInput] = useState('')

  // Load cases list
  const loadCaseList = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getCases({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        search: searchQuery || undefined,
        page,
        page_size: pageSize,
      })
      setCases(res.items)
      setTotalCases(res.total)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cases')
    } finally {
      setLoading(false)
    }
  }

  // Load selected case details
  const loadCaseDetail = async (id: number) => {
    try {
      const data = await getCaseById(id)
      setSelectedCase(data)
      // fetch timeline
      const tl = await getCaseTimeline(id, timelineAsc)
      setTimeline(tl)
    } catch (err: any) {
      console.error(err)
      setError(err.message)
    }
  }

  // Load related transactions
  const loadRelated = async (id: number) => {
    setLoadingRelated(true)
    try {
      const rel = await getRelatedTransactions(id)
      setRelatedTxns(rel)
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoadingRelated(false)
    }
  }

  useEffect(() => {
    if (selectedCaseId === null) {
      loadCaseList()
    } else {
      loadCaseDetail(selectedCaseId)
      if (activeSubTab === 'related') {
        loadRelated(selectedCaseId)
      }
    }
  }, [selectedCaseId, page, statusFilter, priorityFilter, activeSubTab, timelineAsc])

  // Handle case creation
  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const initTxns = newInitialTxnId.trim() ? [parseInt(newInitialTxnId.trim(), 10)] : undefined
      const created = await createCase({
        title: newTitle.trim(),
        summary: newSummary.trim() || undefined,
        priority: newPriority,
        assigned_reviewer: newReviewer.trim() || undefined,
        initial_transaction_ids: initTxns,
        initial_note: newInitialNote.trim() || undefined,
      })
      setShowCreateModal(false)
      // Reset form
      setNewTitle('')
      setNewSummary('')
      setNewReviewer('')
      setNewInitialTxnId('')
      setNewInitialNote('')
      // Open created case
      setSelectedCaseId(created.id)
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle closing case
  const handleCloseCase = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCaseId) return
    try {
      await closeCase(selectedCaseId, {
        final_disposition: closeDisposition,
        disposition_notes: closeNotes.trim(),
        reviewer_name: closeReviewer.trim() || undefined,
      })
      setShowCloseModal(false)
      setCloseNotes('')
      await loadCaseDetail(selectedCaseId)
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle adding reviewer note
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCaseId || !noteInput.trim()) return
    try {
      await addCaseNote(selectedCaseId, noteInput.trim(), noteAuthor.trim() || undefined)
      setNoteInput('')
      await loadCaseDetail(selectedCaseId)
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle linking transaction
  const handleLinkTransaction = async (txnId: number, reason?: string) => {
    if (!selectedCaseId) return
    try {
      await linkTransactionToCase(selectedCaseId, txnId, reason)
      setLinkTxnIdInput('')
      setLinkReasonInput('')
      await loadCaseDetail(selectedCaseId)
      if (activeSubTab === 'related') {
        loadRelated(selectedCaseId)
      }
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle unlinking transaction
  const handleUnlinkTransaction = async (txnId: number) => {
    if (!selectedCaseId) return
    if (!confirm('Are you sure you want to unlink this transaction from the case?')) return
    try {
      await unlinkTransactionFromCase(selectedCaseId, txnId)
      await loadCaseDetail(selectedCaseId)
      if (activeSubTab === 'related') {
        loadRelated(selectedCaseId)
      }
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle status update
  const handleStatusChange = async (newStatus: CaseStatus) => {
    if (!selectedCaseId) return
    try {
      await updateCase(selectedCaseId, { status: newStatus })
      await loadCaseDetail(selectedCaseId)
    } catch (err: any) {
      alert(err.message)
    }
  }

  // Handle report export
  const handleExport = async () => {
    if (!selectedCaseId) return
    try {
      const rep = await exportCaseReport(selectedCaseId)
      setExportData(rep)
      setShowExportModal(true)
    } catch (err: any) {
      alert(err.message)
    }
  }

  const downloadMarkdownReport = () => {
    if (!exportData) return
    const blob = new Blob([exportData.report_markdown], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${exportData.case_reference}_Investigation_Report.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Helper styles
  const getPriorityBadge = (p: CasePriority) => {
    switch (p) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300'
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-300'
      case 'MEDIUM':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'LOW':
        return 'bg-slate-100 text-slate-700 border-slate-300'
    }
  }

  const getStatusBadge = (s: CaseStatus) => {
    switch (s) {
      case 'OPEN':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300'
      case 'IN_REVIEW':
        return 'bg-indigo-50 text-indigo-700 border-indigo-300'
      case 'WAITING_FOR_INFORMATION':
        return 'bg-amber-50 text-amber-700 border-amber-300'
      case 'CLOSED':
        return 'bg-slate-200 text-slate-700 border-slate-400'
    }
  }

  const getDispositionBadge = (d: CaseDisposition) => {
    switch (d) {
      case 'CONFIRMED_FRAUD':
        return 'bg-red-600 text-white'
      case 'CONFIRMED_LEGITIMATE':
        return 'bg-emerald-600 text-white'
      case 'UNVERIFIED_SUSPICION':
        return 'bg-amber-500 text-white'
      case 'INCONCLUSIVE':
        return 'bg-slate-600 text-white'
    }
  }

  // Quick statistics calculation
  const openCount = cases.filter((c) => c.status === 'OPEN').length
  const inReviewCount = cases.filter((c) => c.status === 'IN_REVIEW').length
  const closedCount = cases.filter((c) => c.status === 'CLOSED').length

  // ================= RENDER =================

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            {selectedCaseId !== null && (
              <button
                type="button"
                onClick={() => {
                  setSelectedCaseId(null)
                  setSelectedCase(null)
                }}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 mr-2"
              >
                ← Back to Cases
              </button>
            )}
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {selectedCaseId === null ? 'Investigation Case Management' : selectedCase?.case_reference}
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {selectedCaseId === null
              ? 'Multi-transaction risk investigation, evidence timeline, relational clustering, and audit governance'
              : selectedCase?.title}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedCaseId === null ? (
            <button
              type="button"
              disabled={isViewer}
              onClick={() => {
                if (user?.username) {
                  setNewReviewer(user.username)
                }
                setShowCreateModal(true)
              }}
              className={`px-3.5 py-2 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5 ${
                isViewer ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
              }`}
              title={isViewer ? 'Creating cases requires Analyst or Admin role' : 'Create new case'}
            >
              <span>+ New Investigation Case</span>
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={handleExport}
                className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1"
              >
                <span>Export Report</span>
              </button>
              {selectedCase?.status !== 'CLOSED' ? (
                <button
                  type="button"
                  disabled={isViewer}
                  onClick={() => {
                    if (user?.username) {
                      setCloseReviewer(user.username)
                    }
                    setShowCloseModal(true)
                  }}
                  className={`px-3 py-1.5 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1 ${
                    isViewer ? 'bg-slate-400 cursor-not-allowed' : 'bg-slate-900 hover:bg-black'
                  }`}
                  title={isViewer ? 'Closing cases requires Analyst or Admin role' : 'Close case'}
                >
                  <span>Close Investigation</span>
                </button>
              ) : (
                <button
                  type="button"
                  disabled={isViewer}
                  onClick={() => handleStatusChange('IN_REVIEW')}
                  className={`px-3 py-1.5 border text-xs font-semibold rounded-lg shadow-xs transition ${
                    isViewer
                      ? 'border-slate-200 text-slate-400 cursor-not-allowed'
                      : 'border-amber-300 text-amber-800 hover:bg-amber-50'
                  }`}
                >
                  Reopen Case
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {isViewer && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold">Viewer Access Mode:</span>
            <span>You have read-only privileges. Creating cases, adding notes, linking transactions, and case dispositions require Analyst or Admin role.</span>
          </div>
          <span className="font-mono text-[10px] bg-amber-100 px-2 py-0.5 rounded border border-amber-300">RBAC Enforced</span>
        </div>
      )}

      {/* ================= CASE LIST VIEW ================= */}
      {selectedCaseId === null ? (
        <div className="space-y-5">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total In Scope</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{totalCases}</p>
            </div>
            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/40 shadow-xs">
              <span className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Open Queue</span>
              <p className="text-2xl font-bold text-emerald-900 mt-1">{openCount}</p>
            </div>
            <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 shadow-xs">
              <span className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider">In Review</span>
              <p className="text-2xl font-bold text-indigo-900 mt-1">{inReviewCount}</p>
            </div>
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider">Resolved / Closed</span>
              <p className="text-2xl font-bold text-slate-800 mt-1">{closedCount}</p>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
            <input
              type="text"
              placeholder="Search reference, title, reviewer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs w-64 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-700 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="IN_REVIEW">IN_REVIEW</option>
              <option value="WAITING_FOR_INFORMATION">WAITING_FOR_INFORMATION</option>
              <option value="CLOSED">CLOSED</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-700 focus:outline-none"
            >
              <option value="">All Priorities</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
            <button
              type="button"
              onClick={loadCaseList}
              className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition"
            >
              Refresh
            </button>
          </div>

          {/* Cases Table */}
          {loading ? (
            <div className="py-20 flex justify-center">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 font-medium">
              {error}
            </div>
          ) : cases.length === 0 ? (
            <div className="py-16 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-white space-y-3">
              <div className="w-10 h-10 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
                📁
              </div>
              <h3 className="text-sm font-bold text-slate-800">No Investigation Cases Found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No cases match the selected criteria. Create an investigation case to correlate multiple transactions, review audit evidence, and record dispositions.
              </p>
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition"
              >
                Open First Case
              </button>
            </div>
          ) : (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
                    <th className="py-3 px-4">Case Reference</th>
                    <th className="py-3 px-4">Title & Context</th>
                    <th className="py-3 px-4">Review Priority</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Assignee</th>
                    <th className="py-3 px-4 text-center">Linked Txns</th>
                    <th className="py-3 px-4">Created</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cases.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => setSelectedCaseId(c.id)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-600">{c.case_reference}</td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 max-w-xs truncate">{c.title}</div>
                        {c.summary && <div className="text-[11px] text-slate-500 max-w-xs truncate">{c.summary}</div>}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${getPriorityBadge(
                            c.priority
                          )}`}
                        >
                          {c.priority}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-semibold border ${getStatusBadge(
                            c.status
                          )}`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-700 font-medium">
                        {c.assigned_reviewer || <span className="text-slate-400 italic">Unassigned</span>}
                      </td>
                      <td className="py-3.5 px-4 text-center font-mono font-bold text-slate-800">
                        {c.linked_transactions_count}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                        {new Date(c.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedCaseId(c.id)
                          }}
                          className="px-2.5 py-1 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition"
                        >
                          Examine →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        /* ================= CASE DETAIL VIEW ================= */
        <div className="space-y-6">
          {/* Case Detail Banner */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className="font-mono text-sm font-bold text-blue-600 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-lg">
                    {selectedCase?.case_reference}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${getStatusBadge(
                      selectedCase?.status || 'OPEN'
                    )}`}
                  >
                    {selectedCase?.status}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getPriorityBadge(
                      selectedCase?.priority || 'MEDIUM'
                    )}`}
                    title="Review priority level for triage, not a confirmed fraud verdict."
                  >
                    Priority: {selectedCase?.priority}
                  </span>
                  {selectedCase?.final_disposition && (
                    <span
                      className={`px-2.5 py-0.5 rounded-md text-xs font-bold tracking-tight shadow-xs ${getDispositionBadge(
                        selectedCase.final_disposition
                      )}`}
                    >
                      Disposition: {selectedCase.final_disposition}
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-bold text-slate-900">{selectedCase?.title}</h2>
                {selectedCase?.summary && (
                  <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">{selectedCase.summary}</p>
                )}
              </div>

              {/* Status & Assignee Quick Actions */}
              <div className="flex flex-col items-end gap-2 shrink-0">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>Assigned Reviewer:</span>
                  <span className="font-semibold text-slate-800">
                    {selectedCase?.assigned_reviewer || 'Unassigned'}
                  </span>
                </div>
                {selectedCase?.status !== 'CLOSED' && (
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500">Change Status:</span>
                    <select
                      value={selectedCase?.status}
                      disabled={isViewer}
                      onChange={(e) => handleStatusChange(e.target.value as CaseStatus)}
                      className="px-2.5 py-1 text-xs border border-slate-300 rounded-md bg-white font-medium disabled:bg-slate-100 disabled:text-slate-400"
                    >
                      <option value="OPEN">OPEN</option>
                      <option value="IN_REVIEW">IN_REVIEW</option>
                      <option value="WAITING_FOR_INFORMATION">WAITING_FOR_INFO</option>
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* Disposition Details (if closed) */}
            {selectedCase?.status === 'CLOSED' && (
              <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">Final Reviewer Disposition:</span>
                  <span className="text-slate-500">
                    Closed on {new Date(selectedCase.closed_at || '').toLocaleString()}
                  </span>
                </div>
                <p className="text-slate-700 italic">"{selectedCase.disposition_notes}"</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Note: The disposition represents the investigator's structured outcome after reviewing linked evidence.
                </p>
              </div>
            )}
          </div>

          {/* Sub Navigation Tabs */}
          <div className="flex border-b border-slate-200 space-x-6 text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveSubTab('transactions')}
              className={`pb-3 transition-colors ${
                activeSubTab === 'transactions'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Linked Transactions ({selectedCase?.transactions?.length || 0})
            </button>
            <button
              type="button"
              onClick={() => setActiveSubTab('related')}
              className={`pb-3 transition-colors ${
                activeSubTab === 'related'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Relational Intelligence & Candidates
            </button>
            <button
              type="button"
              onClick={() => setActiveSubTab('timeline')}
              className={`pb-3 transition-colors ${
                activeSubTab === 'timeline'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Unified Evidence Timeline ({timeline.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveSubTab('notes')}
              className={`pb-3 transition-colors ${
                activeSubTab === 'notes'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Reviewer Notes Log
            </button>
          </div>

          {/* ================= TAB 1: LINKED TRANSACTIONS ================= */}
          {activeSubTab === 'transactions' && (
            <div className="space-y-4">
              {/* Manual Link Input */}
              {selectedCase?.status !== 'CLOSED' && !isViewer && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center gap-3">
                  <span className="text-xs font-bold text-slate-700">Link Transaction:</span>
                  <input
                    type="number"
                    placeholder="Transaction ID (e.g. 1)"
                    value={linkTxnIdInput}
                    onChange={(e) => setLinkTxnIdInput(e.target.value)}
                    className="px-2.5 py-1 text-xs border border-slate-300 rounded-md bg-white w-40"
                  />
                  <input
                    type="text"
                    placeholder="Linking rationale (optional)"
                    value={linkReasonInput}
                    onChange={(e) => setLinkReasonInput(e.target.value)}
                    className="px-2.5 py-1 text-xs border border-slate-300 rounded-md bg-white flex-1 min-w-[200px]"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const idNum = parseInt(linkTxnIdInput, 10)
                      if (!idNum) return alert('Enter a valid numeric transaction ID')
                      handleLinkTransaction(idNum, linkReasonInput)
                    }}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-xs transition"
                  >
                    + Link to Case
                  </button>
                </div>
              )}

              {/* Transactions Table */}
              {!selectedCase?.transactions || selectedCase.transactions.length === 0 ? (
                <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-white text-xs text-slate-500">
                  No transactions currently linked to this investigation case.
                </div>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
                        <th className="py-3 px-4">Reference</th>
                        <th className="py-3 px-4">Amount</th>
                        <th className="py-3 px-4">Channel / Type</th>
                        <th className="py-3 px-4">Counterparties</th>
                        <th className="py-3 px-4">Timestamp</th>
                        <th className="py-3 px-4">AI Assessment Snapshot</th>
                        <th className="py-3 px-4">Linking Reason</th>
                        {selectedCase?.status !== 'CLOSED' && !isViewer && <th className="py-3 px-4 text-right">Action</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedCase.transactions.map((t) => (
                        <tr key={t.id} className="hover:bg-slate-50/60">
                          <td className="py-3 px-4 font-mono font-bold text-slate-900">{t.transaction_reference}</td>
                          <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                            {Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })} {t.currency}
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-semibold text-slate-800">{t.channel}</span>
                            <span className="text-slate-400 text-[10px] block">{t.transaction_type}</span>
                          </td>
                          <td className="py-3 px-4 text-[11px]">
                            <div className="text-slate-700">From: {t.sender_reference || 'N/A'}</div>
                            <div className="text-slate-700">To: {t.receiver_reference || 'N/A'}</div>
                          </td>
                          <td className="py-3 px-4 text-slate-500 text-[11px]">
                            {new Date(t.timestamp).toLocaleString()}
                          </td>
                          <td className="py-3 px-4">
                            {t.latest_assessment ? (
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-1.5">
                                  <span
                                    className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                                      t.latest_assessment.overall_severity === 'HIGH' ||
                                      t.latest_assessment.overall_severity === 'CRITICAL'
                                        ? 'bg-red-100 text-red-800'
                                        : 'bg-blue-100 text-blue-800'
                                    }`}
                                  >
                                    {t.latest_assessment.final_recommendation}
                                  </span>
                                  <span className="font-mono text-[10px] text-slate-600">
                                    {t.latest_assessment.risk_score.toFixed(1)}/100
                                  </span>
                                </div>
                                <span className="text-[10px] text-slate-400 block">
                                  {t.latest_assessment.rules_triggered_count} rules fired
                                </span>
                              </div>
                            ) : (
                              <span className="text-slate-400 italic text-[11px]">Unassessed</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-slate-600 text-[11px] max-w-xs truncate">
                            {t.linking_reason || 'Manual review'}
                          </td>
                          {selectedCase?.status !== 'CLOSED' && !isViewer && (
                            <td className="py-3 px-4 text-right">
                              <button
                                type="button"
                                onClick={() => handleUnlinkTransaction(t.transaction_id)}
                                className="px-2 py-0.5 text-[10px] font-semibold text-rose-600 hover:text-rose-800 bg-rose-50 hover:bg-rose-100 rounded transition"
                              >
                                Unlink
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ================= TAB 2: RELATIONAL INTELLIGENCE ================= */}
          {activeSubTab === 'related' && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl text-xs space-y-1">
                <h4 className="font-bold text-blue-900">Explainable Relational Inspection Engine</h4>
                <p className="text-blue-800 leading-relaxed">
                  FinGuard AI inspects active database transactions to discover shared counterparties (sender / receiver), temporal proximity (±24h window), and channel clustering relative to the transactions already linked to this case. Matching criteria are strictly factual and do not assert fraud guilt.
                </p>
              </div>

              {loadingRelated ? (
                <div className="py-16 flex justify-center">
                  <LoadingSpinner />
                </div>
              ) : relatedTxns.length === 0 ? (
                <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-white text-xs text-slate-500">
                  No additional relational candidates found matching the linked counterparties or temporal windows.
                </div>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
                        <th className="py-3 px-4">Candidate Reference</th>
                        <th className="py-3 px-4">Amount</th>
                        <th className="py-3 px-4">Match Strength</th>
                        <th className="py-3 px-4">Explainable Matching Reasons</th>
                        <th className="py-3 px-4">Timestamp</th>
                        <th className="py-3 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {relatedTxns.map((r) => (
                        <tr key={r.transaction_id} className="hover:bg-slate-50/60">
                          <td className="py-3 px-4 font-mono font-bold text-slate-900">{r.transaction_reference}</td>
                          <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                            {Number(r.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })} {r.currency}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                                r.match_strength === 'HIGH'
                                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                                  : r.match_strength === 'MEDIUM'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                  : 'bg-slate-100 text-slate-700 border border-slate-300'
                              }`}
                            >
                              {r.match_strength}
                            </span>
                          </td>
                          <td className="py-3 px-4 max-w-md">
                            <ul className="list-disc list-inside space-y-0.5 text-[11px] text-slate-700">
                              {r.relationship_reasons.map((reason, idx) => (
                                <li key={idx}>{reason}</li>
                              ))}
                            </ul>
                          </td>
                          <td className="py-3 px-4 text-slate-500 text-[11px]">
                            {new Date(r.timestamp).toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {r.is_already_linked ? (
                              <span className="text-[11px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                Linked
                              </span>
                            ) : (
                              selectedCase?.status !== 'CLOSED' && !isViewer && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    handleLinkTransaction(
                                      r.transaction_id,
                                      `Relational match: ${r.relationship_reasons[0]}`
                                    )
                                  }
                                  className="px-2.5 py-1 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition"
                                >
                                  + Link Candidate
                                </button>
                              )
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ================= TAB 3: EVIDENCE TIMELINE ================= */}
          {activeSubTab === 'timeline' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-600 pb-1">
                <span>Multi-Source Unified Audit Trail ({timeline.length} events)</span>
                <button
                  type="button"
                  onClick={() => setTimelineAsc(!timelineAsc)}
                  className="font-semibold text-blue-600 hover:text-blue-800"
                >
                  Order: {timelineAsc ? 'Oldest First (Chronological) ↑' : 'Newest First ↓'}
                </button>
              </div>

              {timeline.length === 0 ? (
                <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-white text-xs text-slate-500">
                  No timeline events recorded yet.
                </div>
              ) : (
                <div className="relative pl-6 border-l-2 border-slate-200 space-y-6">
                  {timeline.map((ev, idx) => {
                    const isSystem = ev.source === 'SYSTEM'
                    const isAI = ev.source === 'AI_EXPERT_SYSTEM'
                    const isTxn = ev.source === 'TRANSACTION_LEDGER'
                    return (
                      <div key={idx} className="relative group">
                        {/* Dot */}
                        <div
                          className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white shadow-xs ${
                            isAI
                              ? 'bg-purple-600'
                              : isTxn
                              ? 'bg-emerald-600'
                              : isSystem
                              ? 'bg-blue-600'
                              : 'bg-amber-600'
                          }`}
                        />

                        {/* Card */}
                        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs text-xs space-y-1">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900">{ev.title}</span>
                              <span
                                className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold ${
                                  isAI
                                    ? 'bg-purple-50 text-purple-700'
                                    : isTxn
                                    ? 'bg-emerald-50 text-emerald-700'
                                    : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {ev.source}
                              </span>
                            </div>
                            <span className="text-[11px] text-slate-400 font-mono">
                              {new Date(ev.event_timestamp).toLocaleString()} UTC
                            </span>
                          </div>

                          {ev.description && <p className="text-slate-600 leading-relaxed">{ev.description}</p>}

                          {ev.actor && (
                            <div className="text-[11px] text-slate-500 font-medium">Actor: {ev.actor}</div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* ================= TAB 4: REVIEWER NOTES ================= */}
          {activeSubTab === 'notes' && (
            <div className="space-y-4">
              {/* Existing Notes Display */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Investigator Audit Notes</h4>
                {selectedCase?.reviewer_notes ? (
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed">
                    {selectedCase.reviewer_notes}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No investigator notes recorded yet.</p>
                )}
              </div>

              {/* Add Note Form */}
              {selectedCase?.status !== 'CLOSED' && (
                isViewer ? (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-500 italic">
                    Adding notes is disabled in Viewer mode. Please switch to Analyst or Admin to contribute findings.
                  </div>
                ) : (
                  <form
                    onSubmit={handleAddNote}
                    className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3 text-xs"
                  >
                    <h4 className="font-bold text-slate-800">Add New Investigator Note</h4>
                    <textarea
                      rows={3}
                      placeholder="Enter factual observations, customer contact results, or supporting evidence..."
                      value={noteInput}
                      onChange={(e) => setNoteInput(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      required
                    />
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        placeholder="Investigator name (default: Reviewer)"
                        value={noteAuthor || user?.username || ''}
                        onChange={(e) => setNoteAuthor(e.target.value)}
                        className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs w-60"
                      />
                      <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-xs transition"
                      >
                        Post Note & Log Event
                      </button>
                    </div>
                  </form>
                )
              )}
            </div>
          )}
        </div>
      )}

      {/* ================= MODAL: CREATE CASE ================= */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-900">Open New Investigation Case</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Case Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. High-Velocity International Outflows"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Review Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as CasePriority)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assigned Investigator</label>
                  <input
                    type="text"
                    placeholder="e.g. Lead Analyst Sarah"
                    value={newReviewer}
                    onChange={(e) => setNewReviewer(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Initial Transaction ID (Optional)</label>
                <input
                  type="number"
                  placeholder="e.g. 1 (from transaction ledger)"
                  value={newInitialTxnId}
                  onChange={(e) => setNewInitialTxnId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Case Factual Summary</label>
                <textarea
                  rows={2}
                  placeholder="Context, triggers, or initial alert rationale..."
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Initial Investigator Note</label>
                <textarea
                  rows={2}
                  placeholder="First note recorded in the evidence audit log..."
                  value={newInitialNote}
                  onChange={(e) => setNewInitialNote(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-1.5 text-slate-600 hover:bg-slate-100 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm"
                >
                  Create Investigation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: CLOSE CASE WITH DISPOSITION ================= */}
      {showCloseModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-900">Close Case & Record Disposition</h3>
              <button
                type="button"
                onClick={() => setShowCloseModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCloseCase} className="space-y-4 text-xs">
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-[11px] leading-relaxed">
                Closing an investigation records a formal reviewer disposition in the immutable audit log. Distinct options ensure unverified suspicions are never falsely logged as confirmed fraud.
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Final Reviewer Disposition *</label>
                <select
                  value={closeDisposition}
                  onChange={(e) => setCloseDisposition(e.target.value as CaseDisposition)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white font-semibold text-slate-800"
                >
                  <option value="UNVERIFIED_SUSPICION">UNVERIFIED_SUSPICION — Suspicion unresolved / unconfirmed</option>
                  <option value="CONFIRMED_LEGITIMATE">CONFIRMED_LEGITIMATE — Verified valid customer/business activity</option>
                  <option value="CONFIRMED_FRAUD">CONFIRMED_FRAUD — Confirmed malicious or fraudulent activity</option>
                  <option value="INCONCLUSIVE">INCONCLUSIVE — Incomplete evidence or unresponsive customer</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Investigator Name / Sign-off</label>
                <input
                  type="text"
                  placeholder="e.g. Lead Investigator Alice"
                  value={closeReviewer}
                  onChange={(e) => setCloseReviewer(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Mandatory Disposition Justification *</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Explain why this disposition was reached, cite supporting evidence, customer responses, or audit facts..."
                  value={closeNotes}
                  onChange={(e) => setCloseNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowCloseModal(false)}
                  className="px-3.5 py-1.5 text-slate-600 hover:bg-slate-100 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-slate-900 hover:bg-black text-white font-semibold rounded-lg shadow-sm"
                >
                  Confirm & Close Investigation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: EXPORT REPORT ================= */}
      {showExportModal && exportData && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3 shrink-0">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Investigation Report — {exportData.case_reference}
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Safe export sanitized against spreadsheet formula injection
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowExportModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed select-all">
              {exportData.report_markdown}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-200 shrink-0">
              <span className="text-xs text-slate-500">
                {exportData.total_linked_transactions} transactions · {exportData.total_timeline_events} timeline events
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(exportData.report_markdown)
                    alert('Markdown report copied to clipboard!')
                  }}
                  className="px-3.5 py-1.5 text-slate-700 border border-slate-300 hover:bg-slate-100 rounded-lg text-xs font-semibold"
                >
                  Copy Markdown
                </button>
                <button
                  type="button"
                  onClick={downloadMarkdownReport}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  Download .md File
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
