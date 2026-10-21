import React, { useEffect, useState } from 'react'
import {
  getTransactions,
  createTransaction,
  assessTransaction,
  Transaction,
  TransactionFilterParams,
  TransactionCreatePayload,
  AssessmentResponse,
} from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'
import AssessmentModal from '../components/AssessmentModal'
import { useAuth } from '../lib/auth'

export default function TransactionAnalysis() {
  const { role } = useAuth()
  const isViewer = role === 'VIEWER'

  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [currencyFilter, setCurrencyFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [channelFilter, setChannelFilter] = useState('')
  const [sortBy, setSortBy] = useState('timestamp')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Modals
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  // Expert Assessment State
  const [activeAssessment, setActiveAssessment] = useState<AssessmentResponse | null>(null)
  const [assessingId, setAssessingId] = useState<number | null>(null)
  const [assessmentError, setAssessmentError] = useState<string | null>(null)

  const handleAssess = async (txnId: number) => {
    setAssessingId(txnId)
    setAssessmentError(null)
    try {
      const res = await assessTransaction(txnId)
      setActiveAssessment(res)
    } catch (err: any) {
      setAssessmentError(err.message || 'Failed to assess transaction')
    } finally {
      setAssessingId(null)
    }
  }

  // New Transaction Form State
  const [newTxn, setNewTxn] = useState<TransactionCreatePayload>({
    amount: 1000,
    currency: 'INR',
    transaction_type: 'PAYMENT',
    channel: 'MOBILE_APP',
    status: 'COMPLETED',
    sender_reference: '',
    receiver_reference: '',
    notes: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: TransactionFilterParams = {
        page,
        page_size: pageSize,
        search: searchTerm.trim() || undefined,
        status: statusFilter || undefined,
        currency: currencyFilter || undefined,
        transaction_type: typeFilter || undefined,
        channel: channelFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }
      const data = await getTransactions(params)
      setTransactions(data.items)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (err: any) {
      setError(err.message || 'Error fetching transactions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [page, pageSize, statusFilter, currencyFilter, typeFilter, channelFilter, sortBy, sortOrder])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadData()
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateSubmitting(true)
    setCreateError(null)
    try {
      if (newTxn.amount <= 0) {
        throw new Error('Amount must be greater than zero.')
      }
      await createTransaction({
        ...newTxn,
        amount: Number(newTxn.amount),
      })
      setShowCreateModal(false)
      setNewTxn({
        amount: 1000,
        currency: 'INR',
        transaction_type: 'PAYMENT',
        channel: 'MOBILE_APP',
        status: 'COMPLETED',
        sender_reference: '',
        receiver_reference: '',
        notes: '',
      })
      loadData()
    } catch (err: any) {
      setCreateError(err.message)
    } finally {
      setCreateSubmitting(false)
    }
  }

  const formatAmount = (curr: string, amount: string | number) => {
    const num = Number(amount)
    return `${curr} ${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatDate = (dateStr: string) => {
    try {
      const dt = new Date(dateStr)
      return dt.toLocaleString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transaction Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time financial transaction records, multi-parameter filtering, and schema inspection.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => loadData()}
            className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition shadow-sm"
          >
            Refresh
          </button>
          <button
            type="button"
            disabled={isViewer}
            onClick={() => setShowCreateModal(true)}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition shadow-sm ${
              isViewer
                ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                : 'text-white bg-blue-600 hover:bg-blue-700'
            }`}
            title={isViewer ? 'Creating transactions requires Analyst or Admin role' : 'Create transaction'}
          >
            + Create Transaction
          </button>
        </div>
      </div>

      {isViewer && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold">Viewer Access Mode:</span>
            <span>You have read-only permissions. Creating new transactions or executing AI risk assessments requires Analyst or Admin role.</span>
          </div>
          <span className="font-mono text-[10px] bg-amber-100 px-2 py-0.5 rounded border border-amber-300">RBAC Enforced</span>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[240px]">
            <input
              type="text"
              placeholder="Search by reference, sender, or receiver..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 transition"
          >
            Search
          </button>

          {searchTerm && (
            <button
              type="button"
              onClick={() => {
                setSearchTerm('')
                setPage(1)
                setTimeout(loadData, 0)
              }}
              className="text-xs text-slate-500 hover:text-slate-700 underline"
            >
              Clear
            </button>
          )}
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-200/60 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs"
            >
              <option value="">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="PENDING">Pending</option>
              <option value="FLAGGED">Flagged</option>
              <option value="FAILED">Failed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 font-medium">Currency:</span>
            <select
              value={currencyFilter}
              onChange={(e) => {
                setCurrencyFilter(e.target.value)
                setPage(1)
              }}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs"
            >
              <option value="">All Currencies</option>
              <option value="INR">INR (₹)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 font-medium">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value)
                setPage(1)
              }}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs"
            >
              <option value="">All Types</option>
              <option value="PAYMENT">Payment</option>
              <option value="TRANSFER">Transfer</option>
              <option value="WITHDRAWAL">Withdrawal</option>
              <option value="DEPOSIT">Deposit</option>
              <option value="PURCHASE">Purchase</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 font-medium">Channel:</span>
            <select
              value={channelFilter}
              onChange={(e) => {
                setChannelFilter(e.target.value)
                setPage(1)
              }}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs"
            >
              <option value="">All Channels</option>
              <option value="ONLINE">Online</option>
              <option value="MOBILE_APP">Mobile App</option>
              <option value="ATM">ATM</option>
              <option value="POS">POS Terminal</option>
              <option value="BRANCH">Branch</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 ml-auto">
            <span className="text-slate-500 font-medium">Sort By:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs"
            >
              <option value="timestamp">Timestamp</option>
              <option value="amount">Amount</option>
              <option value="reference">Reference</option>
              <option value="status">Status</option>
            </select>
            <button
              type="button"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-2 py-1 border border-slate-300 rounded-md bg-white text-xs font-semibold hover:bg-slate-100"
            >
              {sortOrder.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
          <strong>Data Fetch Error:</strong> {error}
        </div>
      )}

      {/* Transactions Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-500">
            <LoadingSpinner />
            <span className="text-xs">Querying database records...</span>
          </div>
        ) : transactions.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <div className="text-slate-400 text-3xl font-light">⊘</div>
            <h3 className="text-sm font-semibold text-slate-700">No Transactions Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No records match your selected filters. Try clearing search parameters or create a new transaction.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Type / Channel</th>
                  <th className="py-3 px-4">Parties</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Provenance</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((txn) => {
                  let badge = 'bg-slate-100 text-slate-700'
                  if (txn.status === 'COMPLETED') badge = 'bg-emerald-100 text-emerald-800'
                  if (txn.status === 'PENDING') badge = 'bg-amber-100 text-amber-800'
                  if (txn.status === 'FLAGGED') badge = 'bg-rose-100 text-rose-800'
                  if (txn.status === 'FAILED') badge = 'bg-red-100 text-red-800'

                  return (
                    <tr key={txn.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-blue-600">
                        <button
                          type="button"
                          onClick={() => setSelectedTxn(txn)}
                          className="hover:underline text-left font-mono"
                        >
                          {txn.reference}
                        </button>
                      </td>
                      <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                        {formatDate(txn.timestamp)}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-900 font-mono whitespace-nowrap">
                        {formatAmount(txn.currency, txn.amount)}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        <div className="font-medium">{txn.transaction_type}</div>
                        <div className="text-[10px] text-slate-400">{txn.channel}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                        <div>S: {txn.sender_reference || '—'}</div>
                        <div className="text-slate-400">R: {txn.receiver_reference || '—'}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide ${badge}`}>
                          {txn.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] bg-slate-50 text-slate-700 border border-slate-200 font-medium">
                          {txn.dataset_provenance.startsWith('CSV_IMPORT:')
                            ? `CSV: ${txn.dataset_provenance.replace('CSV_IMPORT:', '')}`
                            : 'Live / API'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleAssess(txn.id)}
                          disabled={assessingId === txn.id || isViewer}
                          className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                          title={isViewer ? 'Assessing transactions requires Analyst or Admin role' : 'Run Forward-Chaining Expert AI Inference'}
                        >
                          {assessingId === txn.id ? 'Evaluating...' : '⚡ Assess'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedTxn(txn)}
                          className="text-xs text-slate-600 hover:text-slate-800 font-medium"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t border-slate-200 gap-3 text-xs text-slate-600">
          <div>
            Showing <span className="font-semibold">{transactions.length}</span> of{' '}
            <span className="font-semibold">{total}</span> total transactions
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
              className="border border-slate-300 rounded px-2 py-1 bg-white text-xs"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>

            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="px-2 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-2.5 py-1 border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Details Modal */}
      {selectedTxn && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-start border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Transaction Specification</h3>
                <p className="text-xs font-mono text-blue-600 mt-0.5">{selectedTxn.reference}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedTxn(null)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-400 uppercase font-semibold">Amount & Currency</span>
                <p className="font-bold text-slate-900 text-sm mt-0.5">
                  {formatAmount(selectedTxn.currency, selectedTxn.amount)}
                </p>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-semibold">Status</span>
                <p className="font-semibold text-slate-800 mt-0.5">{selectedTxn.status}</p>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-semibold">Transaction Type</span>
                <p className="text-slate-800 mt-0.5">{selectedTxn.transaction_type}</p>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-semibold">Channel</span>
                <p className="text-slate-800 mt-0.5">{selectedTxn.channel}</p>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-semibold">Sender Reference</span>
                <p className="font-mono text-slate-700 mt-0.5">{selectedTxn.sender_reference || 'None'}</p>
              </div>
              <div>
                <span className="text-slate-400 uppercase font-semibold">Receiver Reference</span>
                <p className="font-mono text-slate-700 mt-0.5">{selectedTxn.receiver_reference || 'None'}</p>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400 uppercase font-semibold">Normalized UTC Timestamp</span>
                <p className="font-mono text-slate-700 mt-0.5">{selectedTxn.timestamp}</p>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400 uppercase font-semibold">Provenance Channel</span>
                <p className="text-slate-700 mt-0.5 font-medium">
                  {selectedTxn.dataset_provenance.startsWith('CSV_IMPORT:')
                    ? `Batch Ingested (${selectedTxn.dataset_provenance.replace('CSV_IMPORT:', '')})`
                    : 'Real-Time Direct Ingestion'}
                </p>
              </div>
              {selectedTxn.notes && (
                <div className="col-span-2 bg-slate-50 p-2.5 rounded border border-slate-200">
                  <span className="text-slate-400 uppercase font-semibold">Context Notes</span>
                  <p className="text-slate-700 mt-0.5">{selectedTxn.notes}</p>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-between items-center">
              <button
                type="button"
                onClick={() => handleAssess(selectedTxn.id)}
                disabled={assessingId === selectedTxn.id}
                className="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition flex items-center space-x-1.5"
              >
                <span>⚡ Run Expert System Assessment</span>
              </button>
              <button
                type="button"
                onClick={() => setSelectedTxn(null)}
                className="px-4 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Transaction Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-900">Record Real-Time Transaction</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Amount *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={newTxn.amount}
                    onChange={(e) => setNewTxn({ ...newTxn, amount: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Currency *</label>
                  <select
                    value={newTxn.currency}
                    onChange={(e) => setNewTxn({ ...newTxn, currency: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
                  >
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Transaction Type *</label>
                  <select
                    value={newTxn.transaction_type}
                    onChange={(e) => setNewTxn({ ...newTxn, transaction_type: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
                  >
                    <option value="PAYMENT">Payment</option>
                    <option value="TRANSFER">Transfer</option>
                    <option value="WITHDRAWAL">Withdrawal</option>
                    <option value="DEPOSIT">Deposit</option>
                    <option value="PURCHASE">Purchase</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Channel *</label>
                  <select
                    value={newTxn.channel}
                    onChange={(e) => setNewTxn({ ...newTxn, channel: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
                  >
                    <option value="MOBILE_APP">Mobile App</option>
                    <option value="ONLINE">Online Portal</option>
                    <option value="ATM">ATM</option>
                    <option value="POS">POS Terminal</option>
                    <option value="BRANCH">Bank Branch</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Sender Reference</label>
                  <input
                    type="text"
                    placeholder="e.g. USR-ACCT-101"
                    value={newTxn.sender_reference || ''}
                    onChange={(e) => setNewTxn({ ...newTxn, sender_reference: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-medium mb-1">Receiver Reference</label>
                  <input
                    type="text"
                    placeholder="e.g. MERCH-789"
                    value={newTxn.receiver_reference || ''}
                    onChange={(e) => setNewTxn({ ...newTxn, receiver_reference: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-md"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-medium mb-1">Custom Reference (Optional)</label>
                <input
                  type="text"
                  placeholder="Leave empty to auto-generate unique ID"
                  value={newTxn.reference || ''}
                  onChange={(e) => setNewTxn({ ...newTxn, reference: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-medium mb-1">Operational Context / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Optional background details for expert assessment..."
                  value={newTxn.notes || ''}
                  onChange={(e) => setNewTxn({ ...newTxn, notes: e.target.value })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md"
                />
              </div>

              <div className="pt-3 border-t border-slate-200 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-slate-600 hover:bg-slate-100 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-4 py-1.5 font-semibold text-white bg-blue-600 rounded hover:bg-blue-700 flex items-center space-x-1"
                >
                  {createSubmitting && <LoadingSpinner />}
                  <span>Save Transaction</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assessment Error Notification */}
      {assessmentError && (
        <div className="fixed bottom-6 right-6 max-w-md bg-rose-50 border border-rose-300 rounded-xl p-4 shadow-xl z-50 flex items-start space-x-3">
          <div className="text-rose-600 font-bold text-base">⚠</div>
          <div className="flex-1 text-xs">
            <h4 className="font-bold text-rose-900">Expert System Assessment Failed</h4>
            <p className="text-rose-700 mt-0.5">{assessmentError}</p>
          </div>
          <button
            type="button"
            onClick={() => setAssessmentError(null)}
            className="text-rose-500 hover:text-rose-800 text-sm font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Expert System Audit Modal */}
      <AssessmentModal
        assessment={activeAssessment}
        onClose={() => setActiveAssessment(null)}
      />
    </div>
  )
}
