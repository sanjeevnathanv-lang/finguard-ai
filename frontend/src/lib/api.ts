export interface Transaction {
  id: number
  reference: string
  timestamp: string
  amount: string | number
  currency: string
  sender_reference: string | null
  receiver_reference: string | null
  transaction_type: string
  channel: string
  status: string
  dataset_provenance: string
  is_synthetic: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface TransactionCreatePayload {
  reference?: string
  timestamp?: string
  amount: number
  currency: string
  sender_reference?: string
  receiver_reference?: string
  transaction_type: string
  channel: string
  status?: string
  notes?: string
}

export interface TransactionFilterParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  currency?: string
  transaction_type?: string
  channel?: string
  start_date?: string
  end_date?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface TransactionPaginatedResponse {
  items: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CSVRowError {
  row_number: number
  field: string | null
  error_message: string
}

export interface CSVUploadResponse {
  import_reference: string
  filename: string
  total_rows: number
  imported_rows: number
  skipped_rows: number
  rejected_rows: number
  errors: CSVRowError[]
  duration_ms: number
  message: string
}

export interface DashboardMetrics {
  total_transactions: number
  flagged_transactions: number
  status_distribution: Record<string, number>
  volume_by_currency: Record<string, number>
  recent_transactions_count: number
  latest_transaction_timestamp: string | null
  dataset_summary: Record<string, number>
  system_health: string
}

export interface ResetMetricsResponse {
  status: string
  message: string
  transactions_deleted: number
  assessments_deleted: number
  cases_deleted: number
  dataset_imports_deleted: number
  metrics?: DashboardMetrics
}

export interface HealthResponse {
  status: string
}

// Phase 3: Expert System Schemas
export interface RuleCondition {
  fact_name: string
  operator: string
  value?: any
}

export interface RuleConclusion {
  conclusion_type: string
  key: string
  value: any
  severity: string
  weight: number
  message: string
}

export interface RuleSchema {
  rule_id: string
  version: string
  name: string
  description: string
  category: string
  priority: number
  logical_operator: string
  conditions: RuleCondition[]
  conclusions: RuleConclusion[]
  rationale: string
  is_active: boolean
}

export interface RuleActivationRecord {
  rule_id: string
  rule_name: string
  cycle: number
  priority: number
  category: string
  conditions_evaluated: string[]
  derived_facts: Record<string, any>
  conclusions: Record<string, any>[]
  rationale: string
}

export interface ConflictRecord {
  conflict_key: string
  competing_rules: string[]
  competing_values: Record<string, string>
  winning_rule_id: string
  winning_value: string
  resolution_strategy: string
  explanation: string
}

export interface InferenceTrace {
  engine_version: string
  knowledge_base_version: string
  evaluation_timestamp: string
  total_cycles: number
  initial_facts: Record<string, any>
  derived_facts: Record<string, any>
  activated_rules: RuleActivationRecord[]
  untriggered_rule_ids: string[]
  conflicts_detected: ConflictRecord[]
  final_recommendation: string
  final_conclusions: Record<string, any>
  overall_severity: string
  risk_score: number
  human_readable_summary: string
}

export interface AssessmentResponse {
  assessment_id: number
  transaction_id: number | null
  transaction_reference: string | null
  final_recommendation: string
  overall_severity: string
  risk_score: number
  rules_triggered_count: number
  created_at: string
  trace: InferenceTrace
  hybrid_report?: HybridAssessmentReport | null
  model_version?: string | null
}

// Phase 4: Feature Engineering, Anomaly Detection & Machine Learning Schemas

export interface FeatureVector {
  feature_schema_version: string
  transaction_id: number | null
  transaction_reference: string
  timestamp: string
  currency: string
  amount: number
  hour_of_day: number
  day_of_week: number
  is_weekend: number
  is_night: number
  channel: string
  transaction_type: string
  has_sender: number
  has_receiver: number
  has_notes: number
  sender_txn_count_1h: number
  sender_txn_count_24h: number
  sender_txn_count_7d: number
  seconds_since_prev_txn: number | null
  sender_hist_amount_mean: number | null
  sender_hist_amount_max: number | null
  sender_hist_amount_std: number | null
  amount_to_mean_ratio: number
  amount_to_max_ratio: number
  amount_zscore: number
}

export interface AnomalyInferenceResult {
  model_name: string
  model_version: string
  model_type: string
  is_anomaly: boolean
  anomaly_score: number
  anomaly_signal: string
  top_feature_contributions: Record<string, number>
  evaluation_basis: string
  disclaimer: string
}

export interface HybridAssessmentReport {
  assessment_id?: number
  transaction_id?: number
  transaction_reference: string
  timestamp: string
  orchestrator_version: string
  knowledge_base_version: string
  feature_schema_version: string
  rule_engine: {
    recommendation: string
    severity: string
    risk_score: number
    activated_rules_count: number
    activated_rules: any[]
    untriggered_rule_ids: string[]
    conflicts_detected: any[]
    human_readable_summary: string
  }
  ml_intelligence: AnomalyInferenceResult | null
  ml_status: string
  feature_vector: FeatureVector
  synthesis_verdict: string
  synthesis_severity: string
  concordance_analysis: string
  recommendation_rationale: string
  investigation_priority: string
  academic_disclaimer: string
}

export interface ModelReadinessReport {
  supervised_model_status: string
  unsupervised_model_status: string
  active_unsupervised_model: string | null
  unsupervised_model_version: string | null
  total_persisted_transactions: number
  minimum_transactions_for_anomaly_model: number
  supervised_label_requirements: {
    required_label_field: string
    label_definition: string
    lifecycle_status_warning: string
    minimum_positive_cases_required: number
    minimum_total_labelled_cases_required: number
  }
  feature_schema_version: string
  features_registered: string[]
}

export interface ModelEvaluationMetrics {
  model_id: string
  model_version: string
  algorithm: string
  trained_at: string
  is_supervised: boolean
  status: string
  dataset_fingerprint: string
  training_sample_count: number
  evaluation_sample_count: number
  metrics: Record<string, any>
  confusion_matrix: number[][] | null
  limitations: string[]
}

export interface TrainModelRequest {
  algorithm?: string
  test_size?: number
  time_aware_split?: boolean
  class_weight?: string
}

export interface TransactionPatternAnalytics {
  total_analyzed_transactions: number
  query_timestamp: string
  currency_distribution: Record<string, number>
  channel_distribution: Record<string, number>
  transaction_type_distribution: Record<string, number>
  hourly_distribution: Record<string, number>
  day_of_week_distribution: Record<string, number>
  top_active_senders: {
    sender_reference: string
    currency: string
    transaction_count: number
    total_volume: number
  }[]
  average_amounts_by_currency: Record<string, number>
  max_amounts_by_currency: Record<string, number>
}

// API Client Functions

let inMemoryToken: string | null = null

export function setAuthToken(token: string | null) {
  inMemoryToken = token
  if (token) {
    try {
      sessionStorage.setItem('fg_auth_token', token)
    } catch {}
  } else {
    try {
      sessionStorage.removeItem('fg_auth_token')
    } catch {}
  }
}

export function getAuthToken(): string | null {
  if (inMemoryToken) return inMemoryToken
  try {
    const stored = sessionStorage.getItem('fg_auth_token')
    if (stored) {
      inMemoryToken = stored
      return stored
    }
  } catch {}
  return null
}

export function clearAuthToken() {
  setAuthToken(null)
}

export async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const token = getAuthToken()
  const headers = new Headers(init?.headers || {})

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  // Generate clean correlation ID
  if (!headers.has('X-Correlation-ID')) {
    const randomCid = 'web-' + Math.random().toString(36).substring(2, 10)
    headers.set('X-Correlation-ID', randomCid)
  }

  return fetch(url, { ...init, headers })
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch('/health')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Health check failed: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const response = await authFetch('/api/dashboard')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Dashboard request failed: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function resetTransactionsAndMetricsApi(): Promise<ResetMetricsResponse> {
  const response = await authFetch('/api/dashboard/reset-metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) {
    let detail = `Failed to reset metrics (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getTransactions(
  params: TransactionFilterParams = {}
): Promise<TransactionPaginatedResponse> {
  const query = new URLSearchParams()
  if (params.page) query.set('page', params.page.toString())
  if (params.page_size) query.set('page_size', params.page_size.toString())
  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  if (params.currency) query.set('currency', params.currency)
  if (params.transaction_type) query.set('transaction_type', params.transaction_type)
  if (params.channel) query.set('channel', params.channel)
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.end_date) query.set('end_date', params.end_date)
  if (params.sort_by) query.set('sort_by', params.sort_by)
  if (params.sort_order) query.set('sort_order', params.sort_order)

  const url = `/api/transactions${query.toString() ? `?${query.toString()}` : ''}`
  const response = await authFetch(url)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch transactions: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getTransactionById(id: number): Promise<Transaction> {
  const response = await authFetch(`/api/transactions/${id}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Transaction #${id} not found (${response.status}): ${text}`)
  }
  return response.json()
}

export async function createTransaction(payload: TransactionCreatePayload): Promise<Transaction> {
  const response = await authFetch('/api/transactions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Error ${response.status}`
    try {
      const errJson = await response.json()
      detail = errJson.detail || JSON.stringify(errJson)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function uploadTransactionsCSV(file: File): Promise<CSVUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await authFetch('/api/transactions/upload', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    let detail = `Upload error: ${response.status}`
    try {
      const errJson = await response.json()
      detail = errJson.detail || JSON.stringify(errJson)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }

  return response.json()
}

// Phase 3: Expert System API Functions

export async function getExpertRules(): Promise<RuleSchema[]> {
  const response = await authFetch('/api/expert-system/rules')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch expert rules: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getExpertRuleById(ruleId: string): Promise<RuleSchema> {
  const response = await authFetch(`/api/expert-system/rules/${ruleId}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Rule ${ruleId} not found (${response.status}): ${text}`)
  }
  return response.json()
}

export async function evaluateCustomFacts(facts: { name: string; value: any }[]): Promise<InferenceTrace> {
  const response = await authFetch('/api/expert-system/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ facts }),
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Inference evaluation failed: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function assessTransaction(transactionId: number): Promise<AssessmentResponse> {
  const response = await authFetch(`/api/transactions/${transactionId}/assess`, {
    method: 'POST',
  })
  if (!response.ok) {
    let detail = `Assessment failed: ${response.status}`
    try {
      const errJson = await response.json()
      detail = errJson.detail || JSON.stringify(errJson)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getTransactionAssessments(transactionId: number): Promise<AssessmentResponse[]> {
  const response = await authFetch(`/api/transactions/${transactionId}/assessments`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch assessment history: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getAssessmentById(assessmentId: number): Promise<AssessmentResponse> {
  const response = await authFetch(`/api/assessments/${assessmentId}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch assessment: ${response.status} – ${text}`)
  }
  return response.json()
}

// Phase 4: Machine Learning, Model Readiness & Pattern Intelligence API Functions

export async function getModelStatus(): Promise<ModelReadinessReport> {
  const response = await authFetch('/api/model/status')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch model status: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getModelEvaluation(): Promise<ModelEvaluationMetrics> {
  const response = await authFetch('/api/model/evaluation')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch model evaluation: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function trainSupervisedModel(payload: TrainModelRequest): Promise<ModelEvaluationMetrics> {
  const response = await authFetch('/api/model/train', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Training failed: ${response.status}`
    try {
      const errJson = await response.json()
      detail = errJson.detail?.message || errJson.detail || JSON.stringify(errJson)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getTransactionPatterns(currency?: string): Promise<TransactionPatternAnalytics> {
  const url = currency ? `/api/analytics/transaction-patterns?currency=${currency}` : '/api/analytics/transaction-patterns'
  const response = await authFetch(url)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch transaction patterns: ${response.status} – ${text}`)
  }
  return response.json()
}

// Phase 5: Investigation Case Management, Timeline & Relational Analytics

export type CaseStatus = 'OPEN' | 'IN_REVIEW' | 'WAITING_FOR_INFORMATION' | 'CLOSED'
export type CasePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type CaseDisposition = 'UNVERIFIED_SUSPICION' | 'CONFIRMED_LEGITIMATE' | 'CONFIRMED_FRAUD' | 'INCONCLUSIVE'

export interface CaseTimelineEvent {
  id: number
  case_id: number
  event_type: string
  title: string
  description?: string | null
  source: string
  actor?: string | null
  event_timestamp: string
  metadata?: any
}

export interface CaseLinkedTransaction {
  id: number
  transaction_id: number
  transaction_reference: string
  timestamp: string
  amount: number | string
  currency: string
  transaction_type: string
  channel: string
  status: string
  sender_reference?: string | null
  receiver_reference?: string | null
  linking_reason?: string | null
  linked_at: string
  latest_assessment?: {
    id: number
    final_recommendation: string
    overall_severity: string
    risk_score: number
    rules_triggered_count: number
    engine_version: string
    model_version?: string
    created_at: string
  } | null
}

export interface CaseItem {
  id: number
  case_reference: string
  title: string
  summary?: string | null
  status: CaseStatus
  priority: CasePriority
  assigned_reviewer?: string | null
  reviewer_notes?: string | null
  final_disposition?: CaseDisposition | null
  disposition_notes?: string | null
  closed_at?: string | null
  created_at: string
  updated_at: string
  linked_transactions_count: number
  events_count: number
  transactions?: CaseLinkedTransaction[]
  events?: CaseTimelineEvent[]
}

export interface CaseListResponse {
  items: CaseItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface RelatedTransaction {
  transaction_id: number
  transaction_reference: string
  timestamp: string
  amount: number | string
  currency: string
  transaction_type: string
  channel: string
  status: string
  sender_reference?: string | null
  receiver_reference?: string | null
  relationship_reasons: string[]
  match_strength: 'HIGH' | 'MEDIUM' | 'INFORMATIONAL'
  is_already_linked: boolean
}

export interface CaseExportResponse {
  case_reference: string
  title: string
  status: string
  priority: string
  assigned_reviewer?: string | null
  created_at: string
  closed_at?: string | null
  final_disposition?: string | null
  disposition_notes?: string | null
  total_linked_transactions: number
  total_timeline_events: number
  executive_summary: string
  report_markdown: string
  report_json: any
}

export interface CaseCreatePayload {
  title: string
  summary?: string
  priority?: CasePriority
  assigned_reviewer?: string
  initial_transaction_ids?: number[]
  linking_reason?: string
  initial_note?: string
}

export interface CaseUpdatePayload {
  title?: string
  summary?: string
  status?: CaseStatus
  priority?: CasePriority
  assigned_reviewer?: string
  reviewer_notes?: string
}

export interface CaseClosePayload {
  final_disposition: CaseDisposition
  disposition_notes: string
  reviewer_name?: string
}

export async function getCases(params?: {
  status?: string
  priority?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<CaseListResponse> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.priority) query.set('priority', params.priority)
  if (params?.search) query.set('search', params.search)
  if (params?.page) query.set('page', params.page.toString())
  if (params?.page_size) query.set('page_size', params.page_size.toString())

  const url = query.toString() ? `/api/cases?${query.toString()}` : '/api/cases'
  const response = await authFetch(url)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch cases: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getCaseById(caseId: number): Promise<CaseItem> {
  const response = await authFetch(`/api/cases/${caseId}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch case #${caseId}: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function createCase(payload: CaseCreatePayload): Promise<CaseItem> {
  const response = await authFetch('/api/cases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Failed to create case: ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function updateCase(caseId: number, payload: CaseUpdatePayload): Promise<CaseItem> {
  const response = await authFetch(`/api/cases/${caseId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Failed to update case: ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function linkTransactionToCase(caseId: number, transactionId: number, linkingReason?: string): Promise<CaseItem> {
  const response = await authFetch(`/api/cases/${caseId}/transactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transaction_id: transactionId,
      linking_reason: linkingReason || 'Manually linked by reviewer',
    }),
  })
  if (!response.ok) {
    let detail = `Failed to link transaction: ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function unlinkTransactionFromCase(caseId: number, transactionId: number): Promise<CaseItem> {
  const response = await authFetch(`/api/cases/${caseId}/transactions/${transactionId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to unlink transaction: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function addCaseNote(caseId: number, note: string, author?: string): Promise<CaseTimelineEvent> {
  const response = await authFetch(`/api/cases/${caseId}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note, author: author || 'Reviewer' }),
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to add note: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function closeCase(caseId: number, payload: CaseClosePayload): Promise<CaseItem> {
  const response = await authFetch(`/api/cases/${caseId}/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Failed to close case: ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getCaseTimeline(caseId: number, ascending: boolean = true): Promise<CaseTimelineEvent[]> {
  const response = await authFetch(`/api/cases/${caseId}/timeline?ascending=${ascending}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch timeline: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getRelatedTransactions(caseId: number): Promise<RelatedTransaction[]> {
  const response = await authFetch(`/api/cases/${caseId}/related-transactions`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch related transactions: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function exportCaseReport(caseId: number): Promise<CaseExportResponse> {
  const response = await authFetch(`/api/cases/${caseId}/export`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to export case report: ${response.status} – ${text}`)
  }
  return response.json()
}

// Phase 6: Security Hardening, Access Control, Audit Integrity & System Health

export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER'

export interface UserProfile {
  id: number
  username: string
  email: string
  full_name?: string | null
  role: UserRole
  is_active: boolean
  last_login_at?: string | null
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in_minutes: number
  user: UserProfile
}

export interface AuditLogEntry {
  id: number
  event_type: string
  timestamp: string
  actor_username: string
  actor_role?: string | null
  record_reference?: string | null
  status: string
  ip_address?: string | null
  metadata_json?: string | null
  previous_hash?: string | null
  event_hash: string
}

export interface AuditLogResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  page_size: number
}

export interface AuditVerificationResult {
  is_valid: boolean
  total_records_checked: number
  status: string
  message: string
  tampered_record_id?: number | null
  latest_hash?: string | null
}

export interface SystemReadiness {
  status: string
  database: string
  knowledge_base_rules: number
  environment: string
}

export async function loginApi(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    let detail = `Authentication failed (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  const data: LoginResponse = await response.json()
  setAuthToken(data.access_token)
  return data
}

export async function getCurrentUserApi(): Promise<UserProfile> {
  const response = await authFetch('/api/auth/me')
  if (!response.ok) {
    throw new Error(`Failed to fetch current user (${response.status})`)
  }
  return response.json()
}

export async function logoutApi(): Promise<void> {
  try {
    await authFetch('/api/auth/logout', { method: 'POST' })
  } finally {
    clearAuthToken()
  }
}

export async function changePasswordApi(currentPassword: string, newPassword: string): Promise<any> {
  const response = await authFetch('/api/auth/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
  if (!response.ok) {
    let detail = `Password change failed (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getUsersApi(): Promise<UserProfile[]> {
  const response = await authFetch('/api/users')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch users: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function createUserApi(payload: {
  username: string
  email: string
  password: string
  full_name?: string
  role: UserRole
}): Promise<UserProfile> {
  const response = await authFetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    let detail = `Failed to create user (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function updateUserStatusApi(userId: number, isActive: boolean): Promise<UserProfile> {
  const response = await authFetch(`/api/users/${userId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_active: isActive }),
  })
  if (!response.ok) {
    let detail = `Failed to update user status (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function updateUserRoleApi(userId: number, role: UserRole): Promise<UserProfile> {
  const response = await authFetch(`/api/users/${userId}/role`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  })
  if (!response.ok) {
    let detail = `Failed to update user role (${response.status})`
    try {
      const err = await response.json()
      detail = err.detail || JSON.stringify(err)
    } catch {
      detail = await response.text()
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getAuditLogsApi(params?: {
  event_type?: string
  actor_username?: string
  record_reference?: string
  page?: number
  page_size?: number
}): Promise<AuditLogResponse> {
  const query = new URLSearchParams()
  if (params?.event_type) query.set('event_type', params.event_type)
  if (params?.actor_username) query.set('actor_username', params.actor_username)
  if (params?.record_reference) query.set('record_reference', params.record_reference)
  if (params?.page) query.set('page', params.page.toString())
  if (params?.page_size) query.set('page_size', params.page_size.toString())

  const url = query.toString() ? `/api/audit?${query.toString()}` : '/api/audit'
  const response = await authFetch(url)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to fetch audit log: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function verifyAuditChainApi(): Promise<AuditVerificationResult> {
  const response = await authFetch('/api/audit/verify')
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Audit verification request failed: ${response.status} – ${text}`)
  }
  return response.json()
}

export async function getSystemReadinessApi(): Promise<SystemReadiness> {
  const response = await fetch('/api/health/ready')
  if (!response.ok) {
    throw new Error(`System is unready or database disconnected (${response.status})`)
  }
  return response.json()
}
