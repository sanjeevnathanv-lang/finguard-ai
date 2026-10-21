import React, { useEffect, useState } from 'react'
import { getExpertRules, evaluateCustomFacts, RuleSchema, InferenceTrace } from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function ExpertRulesExplorer() {
  const [rules, setRules] = useState<RuleSchema[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')

  // Sandbox state
  const [activeTab, setActiveTab] = useState<'rules' | 'sandbox'>('rules')
  const [sandboxAmount, setSandboxAmount] = useState<number>(350000)
  const [sandboxCurrency, setSandboxCurrency] = useState<string>('INR')
  const [sandboxHour, setSandboxHour] = useState<number>(3)
  const [sandboxVelocity, setSandboxVelocity] = useState<number>(1)
  const [sandboxChannel, setSandboxChannel] = useState<string>('ONLINE')
  const [sandboxEvaluating, setSandboxEvaluating] = useState<boolean>(false)
  const [sandboxTrace, setSandboxTrace] = useState<InferenceTrace | null>(null)
  const [sandboxError, setSandboxError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getExpertRules()
      .then((data) => {
        setRules(data)
        setError(null)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const categories = ['ALL', ...Array.from(new Set(rules.map((r) => r.category)))]

  const filteredRules =
    selectedCategory === 'ALL' ? rules : rules.filter((r) => r.category === selectedCategory)

  const handleRunSandbox = async () => {
    setSandboxEvaluating(true)
    setSandboxError(null)
    setSandboxTrace(null)
    try {
      const facts = [
        { name: 'amount', value: Number(sandboxAmount) },
        { name: 'currency', value: sandboxCurrency },
        { name: 'hour_of_day', value: Number(sandboxHour) },
        { name: 'sender_txn_count_1h', value: Number(sandboxVelocity) },
        { name: 'channel', value: sandboxChannel },
        { name: 'sender_reference', value: 'SANDBOX-SND-01' },
        { name: 'receiver_reference', value: 'SANDBOX-RCV-01' },
      ]
      const trace = await evaluateCustomFacts(facts)
      setSandboxTrace(trace)
    } catch (err: any) {
      setSandboxError(err.message || 'Sandbox evaluation failed')
    } finally {
      setSandboxEvaluating(false)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Expert Rules Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Declarative knowledge representation, formal IF–THEN rules, and forward-chaining deduction.
          </p>
        </div>

        <div className="flex space-x-2">
          <button
            type="button"
            onClick={() => setActiveTab('rules')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition ${
              activeTab === 'rules'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Rules Knowledge Base ({rules.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sandbox')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition ${
              activeTab === 'sandbox'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Interactive Fact Sandbox
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
          <strong>Failed to load rules:</strong> {error}
        </div>
      )}

      {/* Tab 1: Rules Knowledge Base Explorer */}
      {activeTab === 'rules' && (
        <div className="space-y-5">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 mr-1">Categories:</span>
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                  selectedCategory === cat
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="py-20 text-center space-y-3">
              <LoadingSpinner />
              <p className="text-xs text-slate-500">Retrieving knowledge base rules...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredRules.map((rule) => (
                <div
                  key={rule.rule_id}
                  className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-3 hover:border-slate-300 transition"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-bold text-slate-900">{rule.name}</h3>
                        <code className="text-xs font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                          {rule.rule_id}
                        </code>
                        <span className="text-[10px] text-slate-400 font-mono">v{rule.version}</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">{rule.description}</p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                        Priority: {rule.priority}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                        {rule.category}
                      </span>
                    </div>
                  </div>

                  {/* Conditions & Logical Operator */}
                  <div className="space-y-1.5 text-xs">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-400 uppercase text-[10px]">Conditions</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 font-bold">
                        MATCH {rule.logical_operator} (
                        {rule.logical_operator === 'ALL' ? 'Logical AND' : 'Logical OR'})
                      </span>
                    </div>

                    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-200/60 space-y-1">
                      {rule.conditions.map((cond, idx) => (
                        <div key={idx} className="font-mono text-[11px] text-slate-700 flex items-center space-x-2">
                          <span className="text-blue-600 font-semibold">{cond.fact_name}</span>
                          <span className="text-slate-400 font-bold">{cond.operator}</span>
                          <span className="text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                            {cond.value !== undefined && cond.value !== null ? String(cond.value) : 'EXISTS'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Conclusions & Actions */}
                  <div className="space-y-1.5 text-xs">
                    <span className="font-bold text-slate-400 uppercase text-[10px]">Conclusions & Assertions</span>
                    <div className="space-y-1">
                      {rule.conclusions.map((conc, idx) => (
                        <div
                          key={idx}
                          className="p-2 rounded bg-slate-50 border border-slate-200/60 flex items-center justify-between text-[11px]"
                        >
                          <div>
                            <span className="font-bold text-slate-800">[{conc.conclusion_type}]</span>{' '}
                            <code className="text-blue-700 font-semibold">{conc.key}</code> &rarr;{' '}
                            <span className="font-semibold text-slate-900">{String(conc.value)}</span>
                            <div className="text-[10px] text-slate-500">{conc.message}</div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] text-slate-500 font-mono">Weight: {conc.weight}</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                              {conc.severity}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Rationale */}
                  <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                    <strong>Regulatory / Domain Rationale:</strong> {rule.rationale}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Interactive Fact Sandbox */}
      {activeTab === 'sandbox' && (
        <div className="space-y-5">
          <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Forward Chaining Fact Sandbox</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Input dynamic transaction parameters and observe multi-step inference cycles, derived working memory, and conflict resolution live.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Amount</label>
                <input
                  type="number"
                  value={sandboxAmount}
                  onChange={(e) => setSandboxAmount(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Currency</label>
                <select
                  value={sandboxCurrency}
                  onChange={(e) => setSandboxCurrency(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Hour of Day (UTC: 0–23)</label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={sandboxHour}
                  onChange={(e) => setSandboxHour(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">1-Hour Account Velocity</label>
                <input
                  type="number"
                  min="1"
                  value={sandboxVelocity}
                  onChange={(e) => setSandboxVelocity(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Channel</label>
                <select
                  value={sandboxChannel}
                  onChange={(e) => setSandboxChannel(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
                >
                  <option value="ONLINE">ONLINE</option>
                  <option value="MOBILE_APP">MOBILE_APP</option>
                  <option value="ATM">ATM</option>
                  <option value="POS">POS</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleRunSandbox}
                  disabled={sandboxEvaluating}
                  className="w-full py-2 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition shadow-xs flex items-center justify-center space-x-2"
                >
                  {sandboxEvaluating && <LoadingSpinner />}
                  <span>Run Inference Engine &rarr;</span>
                </button>
              </div>
            </div>

            {sandboxError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800">
                {sandboxError}
              </div>
            )}
          </div>

          {/* Sandbox Results */}
          {sandboxTrace && (
            <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl space-y-5">
              <div className="flex justify-between items-center border-b border-slate-200 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                    Deduction Trace Output
                  </h3>
                  <p className="text-xs text-slate-500">
                    Completed in {sandboxTrace.total_cycles} deduction cycle(s) • Final Verdict:{' '}
                    <span className="font-bold text-blue-700">{sandboxTrace.final_recommendation}</span>
                  </p>
                </div>
                <span className="px-3 py-1 rounded bg-slate-200 text-slate-800 font-bold text-xs font-mono">
                  Risk Score: {sandboxTrace.risk_score} / 10.0
                </span>
              </div>

              {/* Activated Rules in Sandbox */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-700 uppercase">Activated Rules Chain:</span>
                {sandboxTrace.activated_rules.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No rules activated for the provided facts.</p>
                ) : (
                  <div className="space-y-2">
                    {sandboxTrace.activated_rules.map((act, i) => (
                      <div key={i} className="p-3 bg-white rounded border border-slate-200 text-xs space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-900">
                            Cycle {act.cycle}: {act.rule_name}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            Priority: {act.priority}
                          </span>
                        </div>
                        <p className="text-slate-600 text-[11px]">{act.rationale}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Working Memory Derived Facts */}
              {Object.keys(sandboxTrace.derived_facts).length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-700 uppercase">
                    Dynamically Derived Facts Asserted into Working Memory:
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    {Object.entries(sandboxTrace.derived_facts).map(([k, v]) => (
                      <div key={k} className="p-2 bg-white rounded border border-slate-200 flex justify-between">
                        <span className="text-blue-700 font-semibold">{k}</span>
                        <span className="text-slate-900 font-bold">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Audit Summary */}
              <div className="p-3 bg-blue-50/70 border border-blue-200 rounded text-[11px] text-blue-950 font-mono whitespace-pre-wrap">
                {sandboxTrace.human_readable_summary}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
