import React, { useEffect, useState } from 'react'
import {
  getModelStatus,
  getModelEvaluation,
  trainSupervisedModel,
  getTransactionPatterns,
  ModelReadinessReport,
  ModelEvaluationMetrics,
  TransactionPatternAnalytics,
} from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../lib/auth'

export default function ModelEvaluation() {
  const { role } = useAuth()
  const isAdmin = role === 'ADMIN'

  const [readiness, setReadiness] = useState<ModelReadinessReport | null>(null)
  const [evaluation, setEvaluation] = useState<ModelEvaluationMetrics | null>(null)
  const [patterns, setPatterns] = useState<TransactionPatternAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [currencyFilter, setCurrencyFilter] = useState<string>('')

  // Training Form State
  const [selectedAlgo, setSelectedAlgo] = useState<'LOGISTIC_REGRESSION' | 'DECISION_TREE'>('LOGISTIC_REGRESSION')
  const [testSize, setTestSize] = useState<number>(0.25)
  const [timeAwareSplit, setTimeAwareSplit] = useState<boolean>(true)
  const [training, setTraining] = useState<boolean>(false)
  const [trainError, setTrainError] = useState<string | null>(null)
  const [trainSuccess, setTrainSuccess] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [r, p] = await Promise.all([
        getModelStatus(),
        getTransactionPatterns(currencyFilter || undefined),
      ])
      setReadiness(r)
      setPatterns(p)

      // Try fetching existing evaluation (may 404 if untrained)
      try {
        const ev = await getModelEvaluation()
        setEvaluation(ev)
      } catch {
        setEvaluation(null)
      }
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [currencyFilter])

  const handleTrainSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setTraining(true)
    setTrainError(null)
    setTrainSuccess(null)

    try {
      const res = await trainSupervisedModel({
        algorithm: selectedAlgo,
        test_size: Number(testSize),
        time_aware_split: timeAwareSplit,
      })
      setEvaluation(res)
      setTrainSuccess(`Supervised ${selectedAlgo} model trained successfully. F1 Score: ${res.metrics.f1_score}`)
      await loadData()
    } catch (err: any) {
      setTrainError(err.message || 'Training failed')
    } finally {
      setTraining(false)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto text-slate-800">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              Phase 4 Pattern Intelligence & Model Evaluation
            </span>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
              Hybrid Multi-Paradigm
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Machine Learning & Pattern Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Transparent model readiness reporting, data-gated supervised training, and empirical transaction distributions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadData()}
          disabled={loading}
          className="px-3.5 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition shadow-sm self-start md:self-auto"
        >
          Refresh Data
        </button>
      </div>

      {loading && !readiness ? (
        <div className="py-24 text-center space-y-3">
          <LoadingSpinner />
          <p className="text-xs text-slate-500">Querying model registry & transaction pattern distributions...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Section 1: Model Readiness Report */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Supervised Readiness Card */}
            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
              <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Supervised Classification Pipeline</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Ground-Truth Label Requirements</p>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                    readiness?.supervised_model_status === 'TRAINED_ACTIVE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : readiness?.supervised_model_status === 'READY_FOR_TRAINING'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-amber-100 text-amber-900'
                  }`}
                >
                  {readiness?.supervised_model_status || 'UNKNOWN'}
                </span>
              </div>

              <div className="text-xs space-y-2 text-slate-600">
                <p>
                  Supervised classifiers require verified binary ground-truth labels (confirmed chargebacks or investigator dispositions).
                </p>
                <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-[11px] text-amber-900 space-y-1">
                  <div className="font-semibold">⚠️ Critical Operational Distinction:</div>
                  <p>
                    Transaction lifecycle status (<code className="font-mono text-amber-950 font-bold">COMPLETED, PENDING, FLAGGED, FAILED</code>)
                    represents payment settlement states, <strong>NOT</strong> confirmed fraud determinations.
                  </p>
                </div>
              </div>
            </div>

            {/* Unsupervised Anomaly Card */}
            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
              <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Unsupervised Outlier Detection</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Empirical Baseline Intelligence</p>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                    readiness?.unsupervised_model_status === 'AVAILABLE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {readiness?.unsupervised_model_status || 'PENDING'}
                </span>
              </div>

              <div className="text-xs space-y-2 text-slate-600">
                <p>
                  Active Algorithm: <strong>{readiness?.active_unsupervised_model || 'Isolation Forest (Pending baseline)'}</strong>
                </p>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 bg-slate-50 rounded border border-slate-200">
                    <span className="text-slate-400">Total Persisted Records:</span>
                    <div className="font-bold text-slate-900 mt-0.5 font-mono">{readiness?.total_persisted_transactions || 0}</div>
                  </div>
                  <div className="p-2 bg-slate-50 rounded border border-slate-200">
                    <span className="text-slate-400">Baseline Requirement:</span>
                    <div className="font-bold text-slate-900 mt-0.5 font-mono">≥ 10 Records</div>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500">
                  Feature Schema: v{readiness?.feature_schema_version || '1.0.0'} ({readiness?.features_registered.length || 0} numerical features).
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Data-Gated Supervised Training Pipeline */}
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Supervised Model Training Pipeline</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Controlled execution over verified ground-truth disposition labels
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">Anti-Leakage Chronological Split</span>
            </div>

            {trainError && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 space-y-1">
                <div className="font-bold flex items-center space-x-1">
                  <span>⛔ Training Refused:</span>
                  <span>Ground-Truth Data Requirements Not Met</span>
                </div>
                <p className="text-[11px] text-rose-700">{trainError}</p>
              </div>
            )}

            {trainSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800">
                {trainSuccess}
              </div>
            )}

            <form onSubmit={handleTrainSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs items-end">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Algorithm</label>
                <select
                  value={selectedAlgo}
                  onChange={(e) => setSelectedAlgo(e.target.value as any)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white text-xs"
                >
                  <option value="LOGISTIC_REGRESSION">Logistic Regression (L2 Balanced)</option>
                  <option value="DECISION_TREE">Decision Tree (Max Depth 5)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Held-Out Test Size</label>
                <select
                  value={testSize}
                  onChange={(e) => setTestSize(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white text-xs"
                >
                  <option value={0.20}>20% Held-Out</option>
                  <option value={0.25}>25% Held-Out (Standard)</option>
                  <option value={0.33}>33% Held-Out</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 pb-2">
                <input
                  type="checkbox"
                  id="timeAware"
                  checked={timeAwareSplit}
                  onChange={(e) => setTimeAwareSplit(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="timeAware" className="font-semibold text-slate-700 text-xs">
                  Time-Aware Split (No Lookahead)
                </label>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={training || !isAdmin}
                  className={`w-full px-4 py-2 text-xs font-semibold rounded-lg transition shadow-sm flex items-center justify-center space-x-1.5 ${
                    !isAdmin
                      ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                      : 'text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50'
                  }`}
                  title={!isAdmin ? 'Training models requires Admin role' : 'Execute training run'}
                >
                  {training && <LoadingSpinner />}
                  <span>{isAdmin ? 'Execute Training Run' : 'Admin Role Required'}</span>
                </button>
              </div>
            </form>

            {/* Evaluation Results if trained */}
            {evaluation && (
              <div className="mt-4 pt-4 border-t border-slate-200 space-y-3">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                    Held-Out Test Evaluation ({evaluation.algorithm})
                  </h4>
                  <span className="text-[10px] font-mono text-slate-500">
                    Trained: {new Date(evaluation.trained_at).toLocaleString()} • Fingerprint: {evaluation.dataset_fingerprint}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">Precision</span>
                    <div className="text-lg font-bold text-slate-900 mt-0.5 font-mono">
                      {(evaluation.metrics.precision * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">Recall</span>
                    <div className="text-lg font-bold text-slate-900 mt-0.5 font-mono">
                      {(evaluation.metrics.recall * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">F1-Score</span>
                    <div className="text-lg font-bold text-blue-600 mt-0.5 font-mono">
                      {evaluation.metrics.f1_score.toFixed(3)}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">ROC-AUC / PR-AUC</span>
                    <div className="text-lg font-bold text-slate-900 mt-0.5 font-mono">
                      {evaluation.metrics.roc_auc ? evaluation.metrics.roc_auc.toFixed(3) : 'N/A'}
                    </div>
                  </div>
                </div>

                {evaluation.confusion_matrix && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <span className="text-[11px] font-semibold text-slate-600">Confusion Matrix (Held-Out Test Set):</span>
                    <div className="font-mono text-xs text-slate-800">
                      <div>True Legitimate: {evaluation.confusion_matrix[0]?.[0]} | False Positive: {evaluation.confusion_matrix[0]?.[1]}</div>
                      <div>False Negative: {evaluation.confusion_matrix[1]?.[0]} | True Fraud: {evaluation.confusion_matrix[1]?.[1]}</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Section 3: Persisted Transaction Pattern Intelligence */}
          <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-3 gap-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Persisted Transaction Pattern Intelligence</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Empirical distributions across {patterns?.total_analyzed_transactions || 0} active database records
                </p>
              </div>

              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-500 font-medium">Currency Filter:</span>
                <select
                  value={currencyFilter}
                  onChange={(e) => setCurrencyFilter(e.target.value)}
                  className="px-2.5 py-1 border border-slate-300 rounded bg-white text-xs font-semibold"
                >
                  <option value="">All Currencies</option>
                  <option value="INR">INR</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>

            {/* Pattern Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Channel Distribution */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Channel Distribution</h4>
                {patterns && Object.keys(patterns.channel_distribution).length > 0 ? (
                  <div className="space-y-1.5 text-xs">
                    {Object.entries(patterns.channel_distribution).map(([ch, count]) => (
                      <div key={ch} className="flex justify-between items-center">
                        <span className="text-slate-600 font-medium">{ch}</span>
                        <span className="font-mono font-bold text-slate-900">{count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No transactions recorded.</p>
                )}
              </div>

              {/* Transaction Type Breakdown */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Transaction Classification</h4>
                {patterns && Object.keys(patterns.transaction_type_distribution).length > 0 ? (
                  <div className="space-y-1.5 text-xs">
                    {Object.entries(patterns.transaction_type_distribution).map(([tt, count]) => (
                      <div key={tt} className="flex justify-between items-center">
                        <span className="text-slate-600 font-medium">{tt}</span>
                        <span className="font-mono font-bold text-slate-900">{count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No transactions recorded.</p>
                )}
              </div>

              {/* Average Amounts by Currency */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Compatible-Currency Means</h4>
                {patterns && Object.keys(patterns.average_amounts_by_currency).length > 0 ? (
                  <div className="space-y-1.5 text-xs">
                    {Object.entries(patterns.average_amounts_by_currency).map(([c, avg]) => (
                      <div key={c} className="flex justify-between items-center">
                        <span className="text-slate-600 font-medium">{c} Average</span>
                        <span className="font-mono font-bold text-slate-900">{c} {avg.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No amounts recorded.</p>
                )}
              </div>
            </div>

            {/* Top Active Senders Table */}
            {patterns && patterns.top_active_senders.length > 0 && (
              <div className="pt-2 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Top Active Originating Senders (Repeat Rates)
                </h4>
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                      <tr>
                        <th className="py-2 px-3">Sender Identifier</th>
                        <th className="py-2 px-3">Currency</th>
                        <th className="py-2 px-3">Total Operations</th>
                        <th className="py-2 px-3 text-right">Aggregated Volume</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {patterns.top_active_senders.map((s, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-mono font-medium text-slate-900">{s.sender_reference}</td>
                          <td className="py-2 px-3 font-mono">{s.currency}</td>
                          <td className="py-2 px-3 font-bold text-slate-800">{s.transaction_count}</td>
                          <td className="py-2 px-3 text-right font-mono font-semibold">
                            {s.currency} {s.total_volume.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
