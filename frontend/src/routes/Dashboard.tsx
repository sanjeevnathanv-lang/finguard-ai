import React, { useEffect, useState } from 'react'
import {
  checkHealth,
  getDashboardMetrics,
  resetTransactionsAndMetricsApi,
  DashboardMetrics,
  HealthResponse,
} from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'

interface DashboardProps {
  onNavigate?: (tab: string) => void
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, m] = await Promise.all([checkHealth(), getDashboardMetrics()])
      setHealth(h)
      setMetrics(m)
    } catch (err: any) {
      setError(err.message || 'Failed to communicate with backend service.')
    } finally {
      setLoading(false)
    }
  }

  const handleRefreshMetrics = async () => {
    setResetting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      const res = await resetTransactionsAndMetricsApi()
      if (res.metrics) {
        setMetrics(res.metrics)
      } else {
        await fetchData()
      }
      setSuccessMessage(
        `All transaction histories and data have been cleared successfully. Dashboard metrics reset to zero (${res.transactions_deleted} transactions purged).`
      )
    } catch (err: any) {
      setError(err.message || 'Failed to clear transactions and refresh metrics.')
    } finally {
      setResetting(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const formatCurrencyValue = (curr: string, val: number) => {
    const symbolMap: Record<string, string> = {
      INR: '₹',
      USD: '$',
      EUR: '€',
      GBP: '£',
    }
    const sym = symbolMap[curr] || curr + ' '
    return `${sym}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Real-Time Financial Surveillance</h1>
          <p className="text-sm text-slate-500 mt-1">
            Live transaction ingestion, real-time metrics, and forward-chaining expert risk evaluation.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={handleRefreshMetrics}
            disabled={loading || resetting}
            title="Click to clear all transaction history and operational data, resetting metrics to zero"
            className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 hover:border-slate-400 active:bg-slate-100 transition shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1.5"
          >
            {resetting ? (
              <>
                <svg className="animate-spin -ml-0.5 mr-1 h-3.5 w-3.5 text-slate-700" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Clearing & Resetting...</span>
              </>
            ) : (
              <span>Refresh Metrics</span>
            )}
          </button>

          <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs">
            <span className="font-semibold text-slate-600">Surveillance Engine:</span>
            {loading ? <LoadingSpinner /> : <StatusBadge connected={health?.status === 'ok'} />}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-900 flex justify-between items-center transition">
          <div className="flex items-center space-x-2">
            <span className="text-emerald-600 font-bold text-base leading-none">✓</span>
            <p className="font-medium">{successMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-xs text-emerald-700 hover:text-emerald-900 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-800 flex justify-between items-center">
          <div>
            <p className="font-semibold">Backend Communication Error</p>
            <p className="mt-0.5 text-rose-700">{error}</p>
          </div>
          <button
            type="button"
            onClick={fetchData}
            className="text-xs bg-rose-100 px-2.5 py-1 rounded hover:bg-rose-200 text-rose-900 font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Core Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Live Transactions</div>
          <div className="mt-2 text-3xl font-bold text-slate-900">
            {metrics ? metrics.total_transactions.toLocaleString() : '—'}
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center space-x-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-emerald-700">Real-Time Ingestion Active</span>
          </div>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Flagged For Review</div>
          <div className="mt-2 text-3xl font-bold text-rose-600">
            {metrics ? metrics.flagged_transactions : 0}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Identified by Expert AI System
          </div>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Recent 7-Day Ingestion</div>
          <div className="mt-2 text-3xl font-bold text-blue-600">
            {metrics ? metrics.recent_transactions_count : '—'}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            {metrics?.latest_transaction_timestamp
              ? `Latest: ${new Date(metrics.latest_transaction_timestamp).toLocaleString()}`
              : 'Awaiting transactions'}
          </div>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Database Engine</div>
          <div className="mt-2 text-xl font-bold text-slate-900">SQLite + SQLAlchemy</div>
          <div className="mt-2 text-xs text-emerald-600 font-medium">
            Active Connection & Schema Verified
          </div>
        </div>
      </div>

      {/* Transaction Volumes by Currency & Status Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Currency Volumes */}
        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
              Transaction Volume by Currency
            </h2>
            <span className="text-xs text-slate-400">Strictly Segregated</span>
          </div>

          {metrics && Object.keys(metrics.volume_by_currency).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(metrics.volume_by_currency).map(([curr, volume]) => (
                <div key={curr} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-200/60">
                  <div className="flex items-center space-x-2">
                    <span className="w-8 h-8 rounded-md bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-xs">
                      {curr}
                    </span>
                    <span className="text-sm font-semibold text-slate-800">{curr} Volume</span>
                  </div>
                  <span className="text-base font-bold text-slate-900 font-mono">
                    {formatCurrencyValue(curr, volume)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              No volume recorded. Awaiting live incoming transactions or CSV batch ingestion.
            </div>
          )}
        </div>

        {/* Status Distribution */}
        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
              Transaction Lifecycle Status
            </h2>
            <span className="text-xs text-slate-400">Operational Breakdown</span>
          </div>

          {metrics && Object.keys(metrics.status_distribution).length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(metrics.status_distribution).map(([statusKey, count]) => {
                let badgeBg = 'bg-slate-50 border-slate-200 text-slate-800'
                if (statusKey === 'COMPLETED') badgeBg = 'bg-emerald-50 border-emerald-200 text-emerald-900'
                if (statusKey === 'PENDING') badgeBg = 'bg-amber-50 border-amber-200 text-amber-900'
                if (statusKey === 'FLAGGED') badgeBg = 'bg-rose-50 border-rose-200 text-rose-900'
                if (statusKey === 'FAILED') badgeBg = 'bg-red-50 border-red-200 text-red-900'

                return (
                  <div key={statusKey} className={`p-3 rounded-lg border ${badgeBg}`}>
                    <div className="text-xs font-semibold uppercase opacity-75">{statusKey}</div>
                    <div className="text-2xl font-bold mt-1">{count}</div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              No status breakdown available.
            </div>
          )}
        </div>
      </div>

      {/* Quick Action Navigation & Guidance */}
      <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800">Real-Time Ingestion & Transaction Analysis</h3>
          <p className="text-xs text-slate-600 mt-0.5">
            Submit live transactions, review streaming records, and execute forward-chaining expert assessments.
          </p>
        </div>
        <div className="flex space-x-3">
          {onNavigate && (
            <>
              <button
                type="button"
                onClick={() => onNavigate('transactions')}
                className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 rounded-lg hover:bg-slate-800 transition shadow-sm"
              >
                Open Transaction Table
              </button>
              <button
                type="button"
                onClick={() => onNavigate('csv_import')}
                className="px-4 py-2 text-xs font-semibold text-blue-600 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition shadow-sm"
              >
                Upload CSV File
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
