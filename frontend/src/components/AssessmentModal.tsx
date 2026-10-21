import React, { useState } from 'react'
import { AssessmentResponse } from '../lib/api'

interface AssessmentModalProps {
  assessment: AssessmentResponse | null
  onClose: () => void
}

export default function AssessmentModal({ assessment, onClose }: AssessmentModalProps) {
  const [activeTab, setActiveTab] = useState<'hybrid' | 'rules' | 'ml' | 'features'>('hybrid')

  if (!assessment) return null

  const trace = assessment.trace
  const hybrid = assessment.hybrid_report
  const ml = hybrid?.ml_intelligence
  const feat = hybrid?.feature_vector

  const getRecommendationBadge = (rec: string) => {
    switch (rec) {
      case 'STANDARD_PROCESSING':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      case 'HUMAN_SUPERVISORY_REVIEW':
        return 'bg-amber-100 text-amber-900 border-amber-300'
      case 'EXPEDITED_SECURITY_INTERVENTION':
        return 'bg-rose-100 text-rose-900 border-rose-300'
      case 'SUPERVISORY_SPOT_CHECK':
        return 'bg-purple-100 text-purple-900 border-purple-300'
      default:
        return 'bg-blue-100 text-blue-900 border-blue-300'
    }
  }

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-600 text-white'
      case 'HIGH':
        return 'bg-rose-500 text-white'
      case 'MEDIUM':
        return 'bg-amber-500 text-white'
      case 'LOW':
        return 'bg-blue-500 text-white'
      default:
        return 'bg-slate-500 text-white'
    }
  }

  const getAnomalyBadge = (signal?: string) => {
    switch (signal) {
      case 'HIGH_ANOMALY':
        return 'bg-rose-100 text-rose-800 border-rose-300'
      case 'ELEVATED_ANOMALY':
        return 'bg-amber-100 text-amber-800 border-amber-300'
      case 'NORMAL':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300'
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-4xl w-full p-6 space-y-5 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                Hybrid AI Decision-Support Assessment
              </span>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
                KB v{trace.knowledge_base_version} • ML {assessment.model_version || 'IsolationForest v1.0'}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 mt-1">
              Transaction: {assessment.transaction_reference || `ID #${assessment.transaction_id}`}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Assessed on {new Date(assessment.created_at).toLocaleString()} • Forward-Chaining Deduction + Empirical Outlier Scoring
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-xl font-bold px-2 py-1"
          >
            ✕
          </button>
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-slate-200 space-x-2 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('hybrid')}
            className={`pb-2 px-3 border-b-2 transition ${
              activeTab === 'hybrid'
                ? 'border-blue-600 text-blue-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            ⚖ Hybrid Synthesis & Concordance
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('rules')}
            className={`pb-2 px-3 border-b-2 transition ${
              activeTab === 'rules'
                ? 'border-blue-600 text-blue-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            📜 Rule-Based Evidence ({assessment.rules_triggered_count})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('ml')}
            className={`pb-2 px-3 border-b-2 transition ${
              activeTab === 'ml'
                ? 'border-blue-600 text-blue-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            🤖 ML & Anomaly Signal {ml ? `(${ml.anomaly_signal})` : ''}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('features')}
            className={`pb-2 px-3 border-b-2 transition ${
              activeTab === 'features'
                ? 'border-blue-600 text-blue-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            🔍 Feature Engineering Snapshot
          </button>
        </div>

        {/* Tab Contents */}
        <div className="overflow-y-auto space-y-5 pr-1 text-xs flex-1">
          {/* TAB 1: HYBRID SYNTHESIS */}
          {activeTab === 'hybrid' && (
            <div className="space-y-4">
              {/* Top Verdict Tiles */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl border bg-slate-50 border-slate-200 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Synthesized Recommendation</span>
                  <div className="pt-1">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${getRecommendationBadge(assessment.final_recommendation)}`}>
                      {assessment.final_recommendation.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl border bg-slate-50 border-slate-200 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Composite Severity</span>
                  <div className="pt-1 flex items-center space-x-2">
                    <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${getSeverityBadge(assessment.overall_severity)}`}>
                      {assessment.overall_severity}
                    </span>
                    <span className="text-slate-600 font-semibold font-mono">
                      Rule Weight: {assessment.risk_score} / 10
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl border bg-slate-50 border-slate-200 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Investigation Priority</span>
                  <div className="text-base font-bold text-slate-900 pt-0.5">
                    {hybrid?.investigation_priority || 'ROUTINE'}
                  </div>
                </div>
              </div>

              {/* Concordance Analysis Banner */}
              <div className="p-4 bg-blue-50/80 border border-blue-200 rounded-xl space-y-2">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-blue-950 uppercase tracking-wider text-[11px]">
                    Multi-Paradigm Concordance Analysis
                  </h3>
                  <span className="text-[10px] font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                    Rules vs. ML
                  </span>
                </div>
                <p className="text-xs text-blue-900 leading-relaxed">
                  {hybrid?.concordance_analysis || (
                    trace.activated_rules.length > 0
                      ? 'Rule engine triggered specific risk criteria.'
                      : 'Standard straight-through baseline validated.'
                  )}
                </p>
                {hybrid?.recommendation_rationale && (
                  <p className="text-[11px] text-blue-800/80 pt-1 border-t border-blue-200/60 font-mono">
                    {hybrid.recommendation_rationale}
                  </p>
                )}
              </div>

              {/* Comparison Matrix */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-3">
                <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Component Diagnostic Matrix
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">Rule-Based Expert System</span>
                      <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">Active</span>
                    </div>
                    <div className="text-slate-600 space-y-1">
                      <div>Triggered Rules: <strong className="text-slate-900">{assessment.rules_triggered_count}</strong></div>
                      <div>Deduction Cycles: <strong className="text-slate-900">{trace.total_cycles}</strong></div>
                      <div>Primary Action: <strong className="text-slate-900">{trace.final_recommendation}</strong></div>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">Unsupervised Isolation Forest</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${getAnomalyBadge(ml?.anomaly_signal)}`}>
                        {ml?.anomaly_signal || 'UNAVAILABLE'}
                      </span>
                    </div>
                    <div className="text-slate-600 space-y-1">
                      <div>Anomaly Magnitude: <strong className="text-slate-900">{ml ? `${(ml.anomaly_score * 100).toFixed(1)}%` : 'N/A'}</strong></div>
                      <div>Outlier Classification: <strong className="text-slate-900">{ml?.is_anomaly ? 'Outlier Flagged' : 'Nominal'}</strong></div>
                      <div>Model Basis: <strong className="text-slate-900">{ml?.model_name || 'N/A'}</strong></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Academic Disclaimer */}
              <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-[11px] text-amber-900">
                <strong>Academic Prototype Notice:</strong> FinGuard AI is a financial risk review platform.
                Outputs are advisory signals for human financial investigators, not definitive fraud accusations.
              </div>
            </div>
          )}

          {/* TAB 2: RULE EVIDENCE */}
          {activeTab === 'rules' && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <h3 className="font-bold text-slate-900 text-xs">Human-Readable Audit Trace</h3>
                <pre className="text-[11px] font-sans text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {trace.human_readable_summary}
                </pre>
              </div>

              {/* Activated Rules */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                  Activated Rules by Deduction Cycle ({trace.activated_rules.length})
                </h4>
                {trace.activated_rules.length === 0 ? (
                  <div className="p-4 text-center bg-slate-50 border border-slate-200 rounded-lg text-slate-500">
                    No specialized risk rules activated for this transaction. Standard straight-through parameters confirmed.
                  </div>
                ) : (
                  trace.activated_rules.map((rule) => (
                    <div key={rule.rule_id} className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900">{rule.rule_name}</span>
                            <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                              {rule.rule_id}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            Category: {rule.category} • Cycle {rule.cycle} • Priority: {rule.priority}
                          </p>
                        </div>
                      </div>
                      <p className="text-slate-700 italic text-[11px]">{rule.rationale}</p>
                      {rule.conditions_evaluated.length > 0 && (
                        <div className="bg-slate-50 p-2.5 rounded border border-slate-200 text-[11px]">
                          <span className="font-semibold text-slate-600">Satisfied Antecedents:</span>
                          <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-700">
                            {rule.conditions_evaluated.map((c, i) => (
                              <li key={i}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* Conflict Records */}
              {trace.conflicts_detected.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
                  <h4 className="font-bold text-amber-950 uppercase tracking-wider text-[11px]">
                    Deterministic Conflict Resolutions ({trace.conflicts_detected.length})
                  </h4>
                  {trace.conflicts_detected.map((conf, i) => (
                    <div key={i} className="text-[11px] text-amber-900 bg-amber-100/60 p-3 rounded border border-amber-200/80 space-y-1">
                      <div className="font-bold">Conflict on Conclusion Key: &apos;{conf.conflict_key}&apos;</div>
                      <p>{conf.explanation}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MACHINE LEARNING & ANOMALY */}
          {activeTab === 'ml' && (
            <div className="space-y-4">
              {ml ? (
                <div className="space-y-4">
                  {/* Gauge Card */}
                  <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-800 uppercase">Empirical Outlier Score</span>
                      <span className={`px-2.5 py-0.5 rounded text-xs font-bold border ${getAnomalyBadge(ml.anomaly_signal)}`}>
                        {ml.anomaly_signal}
                      </span>
                    </div>

                    {/* Progress Gauge */}
                    <div className="space-y-1.5">
                      <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            ml.anomaly_score >= 0.7
                              ? 'bg-rose-500'
                              : ml.anomaly_score >= 0.45
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, ml.anomaly_score * 100))}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                        <span>0.0 (Nominal)</span>
                        <span className="font-bold text-slate-700">{(ml.anomaly_score * 100).toFixed(1)}% Outlier Magnitude</span>
                        <span>1.0 (Critical Outlier)</span>
                      </div>
                    </div>

                    <p className="text-slate-600 text-[11px]">
                      Basis: {ml.evaluation_basis}
                    </p>
                  </div>

                  {/* Top Feature Contributions */}
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                    <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                      Top Deviating Features Against Baseline
                    </h4>
                    {Object.keys(ml.top_feature_contributions).length === 0 ? (
                      <p className="text-slate-500 italic">No significant feature divergence from empirical baseline detected.</p>
                    ) : (
                      <div className="space-y-2">
                        {Object.entries(ml.top_feature_contributions).map(([fName, score]) => (
                          <div key={fName} className="flex justify-between items-center p-2.5 bg-white rounded border border-slate-200">
                            <span className="font-mono font-medium text-slate-800">{fName}</span>
                            <span className="font-mono text-slate-600 font-bold">
                              +{score.toFixed(2)}σ deviation
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Operational Disclaimer */}
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 text-[11px]">
                    <strong>Scientific Disclaimer:</strong> {ml.disclaimer}
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-slate-500">
                  <div className="text-2xl">⏳</div>
                  <h4 className="font-semibold text-slate-800">Unsupervised Baseline Establishing</h4>
                  <p className="text-xs max-w-md mx-auto">
                    The Isolation Forest baseline requires at least 10 historical transaction records to establish an empirical distribution.
                    Current status: {hybrid?.ml_status || 'UNAVAILABLE_INSUFFICIENT_BASELINE'}.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: FEATURE SNAPSHOT */}
          {activeTab === 'features' && feat && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Amount & Currency</span>
                  <div className="font-bold text-slate-900 mt-0.5">{feat.currency} {feat.amount.toLocaleString()}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Hour (UTC)</span>
                  <div className="font-bold text-slate-900 mt-0.5">{feat.hour_of_day}:00 {feat.is_night ? '(Night Window)' : ''}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Velocity 1h / 24h</span>
                  <div className="font-bold text-slate-900 mt-0.5">{feat.sender_txn_count_1h} / {feat.sender_txn_count_24h}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Time Since Last Txn</span>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {feat.seconds_since_prev_txn !== null ? `${Math.round(feat.seconds_since_prev_txn / 60)} min` : 'First Seen'}
                  </div>
                </div>
              </div>

              {/* Currency-Compatible Behavioral Ratios */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2">
                <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Compatible-Currency Behavioral Deviation
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-600">
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">Amount-to-Mean Ratio</span>
                    <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">{feat.amount_to_mean_ratio}x</div>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">Amount-to-Max Ratio</span>
                    <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">{feat.amount_to_max_ratio}x</div>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase">Z-Score Deviation</span>
                    <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">{feat.amount_zscore}σ</div>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 italic">
                  Note: Behavioral statistics are computed strictly over historical records matching currency &apos;{feat.currency}&apos; with complete anti-leakage protection.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-200 flex justify-between items-center text-xs">
          <span className="text-slate-500 text-[11px]">
            Audit Snapshot Stored in SQLite DB (ID #{assessment.assessment_id})
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 font-semibold text-white bg-slate-900 rounded-lg hover:bg-slate-800 transition"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  )
}
