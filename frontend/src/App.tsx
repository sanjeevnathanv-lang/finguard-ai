import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './routes/Dashboard'
import TransactionAnalysis from './routes/TransactionAnalysis'
import CSVImport from './routes/CSVImport'
import ExpertRulesExplorer from './routes/ExpertRulesExplorer'
import ModelEvaluation from './routes/ModelEvaluation'
import InvestigationCases from './routes/InvestigationCases'
import AuditGovernance from './routes/AuditGovernance'
import { AuthProvider } from './lib/auth'

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard')

  return (
    <AuthProvider>
      <div className="flex h-screen bg-slate-100 overflow-hidden font-sans text-slate-800">
        <Sidebar active={activeTab} onNavigate={setActiveTab} />
        <main className="flex-1 overflow-y-auto p-8 bg-white">
          {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
          {activeTab === 'transactions' && <TransactionAnalysis />}
          {activeTab === 'csv_import' && <CSVImport onNavigateToTransactions={() => setActiveTab('transactions')} />}
          {activeTab === 'rules' && <ExpertRulesExplorer />}
          {activeTab === 'models' && <ModelEvaluation />}
          {activeTab === 'investigations' && <InvestigationCases />}
          {activeTab === 'access_control' && <AuditGovernance initialTab="users" />}
          {(activeTab === 'governance' || activeTab === 'reports') && <AuditGovernance initialTab="audit" />}

          {/* Future Phase Modules Placeholders */}
          {!['dashboard', 'transactions', 'csv_import', 'rules', 'models', 'investigations', 'governance', 'access_control', 'reports'].includes(activeTab) && (
            <div className="max-w-3xl mx-auto py-16 text-center space-y-4">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 font-bold text-2xl">
                ⚙
              </div>
              <h2 className="text-xl font-bold text-slate-900 capitalize tracking-tight">
                {activeTab.replace('_', ' ')}
              </h2>
              <p className="text-sm text-slate-600 max-w-lg mx-auto">
                This module will be introduced in subsequent phases of the master plan. Phase 6 security hardening, immutable cryptographic audit logging, and role-based access control are fully active now.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('transactions')}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
                >
                  Go to Active Transactions Layer →
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </AuthProvider>
  )
}
