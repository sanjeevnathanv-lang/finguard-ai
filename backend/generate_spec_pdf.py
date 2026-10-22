import os
import subprocess
import sys

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FinGuard AI — Complete Technical Specification & Architecture Master Document</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {
      content: counter(page);
    }
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    line-height: 1.55;
    font-size: 10.5pt;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }

  /* Cover Page */
  .cover {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 90vh;
    padding-top: 40px;
    padding-bottom: 20px;
  }

  .cover-badge {
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    font-size: 9pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-bottom: 24px;
  }

  .cover-title {
    font-size: 28pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 16px 0;
    letter-spacing: -0.5px;
  }

  .cover-subtitle {
    font-size: 13pt;
    color: #475569;
    font-weight: 400;
    line-height: 1.45;
    margin: 0 0 35px 0;
    max-width: 90%;
  }

  .cover-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 30px;
    font-size: 9.5pt;
  }

  .cover-meta-item strong {
    color: #0f172a;
    display: block;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }

  .cover-meta-item span {
    color: #334155;
    font-weight: 600;
  }

  .cover-disclaimer {
    margin-top: 40px;
    padding: 14px 18px;
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    border-radius: 4px;
    font-size: 9pt;
    color: #92400e;
    line-height: 1.45;
  }

  /* Headings */
  h1 {
    font-size: 18pt;
    font-weight: 800;
    color: #0f172a;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 6px;
    margin-top: 36px;
    margin-bottom: 16px;
    page-break-after: avoid;
    letter-spacing: -0.3px;
  }

  h2 {
    font-size: 13.5pt;
    font-weight: 700;
    color: #1e3a8a;
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }

  h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #334155;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
  }

  p {
    margin: 0 0 10px 0;
  }

  /* Lists */
  ul, ol {
    margin: 0 0 12px 0;
    padding-left: 22px;
  }

  li {
    margin-bottom: 4px;
  }

  /* Code & Pre */
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
  }

  pre {
    background: #0f172a;
    color: #f8fafc;
    padding: 12px 14px;
    border-radius: 8px;
    font-size: 8pt;
    overflow-x: auto;
    line-height: 1.45;
    margin: 10px 0 14px 0;
    page-break-inside: avoid;
  }

  pre code {
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 18px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }

  th {
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #cbd5e1;
  }

  td {
    padding: 7px 10px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
  }

  tr:nth-child(even) td {
    background: #f8fafc;
  }

  /* Callouts & Alert Boxes */
  .callout {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 12px 0 16px 0;
    font-size: 9pt;
    page-break-inside: avoid;
  }

  .callout-blue {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    color: #1e40af;
  }

  .callout-emerald {
    background: #ecfdf5;
    border-left: 4px solid #10b981;
    color: #065f46;
  }

  .callout-amber {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    color: #92400e;
  }

  .callout-rose {
    background: #fff1f2;
    border-left: 4px solid #f43f5e;
    color: #9f1239;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 7.5pt;
    font-weight: 700;
    font-family: ui-monospace, monospace;
  }

  .badge-blue { background: #dbeafe; color: #1e40af; }
  .badge-purple { background: #f3e8ff; color: #6b21a8; }
  .badge-emerald { background: #d1fae5; color: #065f46; }
  .badge-rose { background: #ffe4e6; color: #9f1239; }
  .badge-amber { background: #fef3c7; color: #92400e; }
  .badge-slate { background: #f1f5f9; color: #475569; }

  /* Architecture Diagrams / Flow Boxes */
  .flow-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 14px;
    margin: 12px 0 16px 0;
    page-break-inside: avoid;
  }

  .flow-row {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: space-between;
  }

  .flow-box {
    flex: 1;
    background: #ffffff;
    border: 1px solid #94a3b8;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
    font-size: 8.5pt;
  }

  .flow-box strong {
    display: block;
    color: #0f172a;
    font-size: 9pt;
    margin-bottom: 2px;
  }

  .flow-box span {
    color: #64748b;
    font-size: 7.5pt;
  }

  .flow-arrow {
    color: #64748b;
    font-weight: bold;
    font-size: 11pt;
  }

  .page-break {
    page-break-after: always;
  }
</style>
</head>
<body>

<!-- ================= COVER PAGE ================= -->
<div class="cover">
  <div>
    <div class="cover-badge">Academic & Engineering Master Specification</div>
    <h1 class="cover-title">FinGuard AI</h1>
    <div class="cover-subtitle">
      Explainable Financial Transaction Risk Review, Rule-Based Expert System, Hybrid Machine Learning & Enterprise Security Platform
    </div>

    <div class="cover-meta-grid">
      <div class="cover-meta-item">
        <strong>Project Discipline</strong>
        <span>Artificial Intelligence & Expert Systems</span>
      </div>
      <div class="cover-meta-item">
        <strong>Implementation Phases</strong>
        <span>Phases 1 through 6 (Fully Completed & Tested)</span>
      </div>
      <div class="cover-meta-item">
        <strong>GitHub Repository</strong>
        <span>github.com/sanjeevnathanv-lang/finguard-ai</span>
      </div>
      <div class="cover-meta-item">
        <strong>Author & Maintainer</strong>
        <span>sanjeevnathanv-lang</span>
      </div>
      <div class="cover-meta-item">
        <strong>Backend Architecture</strong>
        <span>Python 3.14 · FastAPI · SQLAlchemy · SQLite</span>
      </div>
      <div class="cover-meta-item">
        <strong>Frontend Architecture</strong>
        <span>React 18 · TypeScript · Vite · Tailwind CSS</span>
      </div>
      <div class="cover-meta-item">
        <strong>Core AI Paradigms</strong>
        <span>Deterministic Production Rules + Scikit-Learn Isolation Forest</span>
      </div>
      <div class="cover-meta-item">
        <strong>Audit & Integrity</strong>
        <span>SHA-256 Cryptographic Hash Chain · Multi-Role RBAC</span>
      </div>
    </div>
  </div>

  <div>
    <div class="cover-disclaimer">
      <strong>Academic & Non-Autonomous Decision Support Notice:</strong><br>
      FinGuard AI is an explainable decision-support platform designed to assist qualified human financial risk analysts. It deliberately does not automate irreversible banking actions, confiscate balances, or automatically declare fraud. In accordance with responsible AI governance, every finding generates an inspectable reasoning chain with full evidentiary provenance.
    </div>
    <div style="text-align: right; font-size: 8pt; color: #94a3b8; margin-top: 14px;">
      Document Release: v1.0.0 · October 2026
    </div>
  </div>
</div>

<!-- ================= TABLE OF CONTENTS ================= -->
<div class="page-break">
  <h1>Table of Contents</h1>
  <ol style="font-size: 10pt; line-height: 1.8; margin-top: 16px;">
    <li><strong>Executive Summary & System Vision</strong></li>
    <li><strong>Full System Architecture & Technology Stack</strong></li>
    <li><strong>Data Ingestion & Transaction Infrastructure (Phases 1 & 2)</strong></li>
    <li><strong>Rule-Based Expert System Engineering (Phase 3)</strong>
      <ul>
        <li>Forward Chaining Inference Engine</li>
        <li>Conflict Resolution Strategy & Fact Extraction</li>
        <li>Active Knowledge Base Rule Catalog (R001–R007)</li>
      </ul>
    </li>
    <li><strong>Pattern Intelligence & Hybrid Machine Learning (Phase 4)</strong>
      <ul>
        <li>Temporal Anti-Leakage Feature Engineering Pipeline</li>
        <li>Unsupervised Isolation Forest Anomaly Detection</li>
        <li>Data-Gated Supervised Training & Ground-Truth Integrity</li>
        <li>Multi-Paradigm Concordance Matrix</li>
      </ul>
    </li>
    <li><strong>Investigation Case Management & Relational Timeline (Phase 5)</strong>
      <ul>
        <li>Case Lifecycle State Machine</li>
        <li>Relational Entity Clustering & Graph Candidates</li>
        <li>Unified Multi-Source Evidence Timeline</li>
        <li>Formula-Safe Forensic Report Export</li>
      </ul>
    </li>
    <li><strong>Security Hardening, Cryptographic Audit & Reliability (Phase 6)</strong>
      <ul>
        <li>Role-Based Access Control (RBAC) Matrix</li>
        <li>Bcrypt Authentication & Sliding-Window Rate Limiting</li>
        <li>Tamper-Evident SHA-256 Cryptographic Hash Chaining</li>
        <li>Operational Reliability: Foreign Keys, Probes & CRLF Defense</li>
      </ul>
    </li>
    <li><strong>Database Schema & Relational Models Reference</strong></li>
    <li><strong>Complete REST API Specification</strong></li>
    <li><strong>Verification, Test Suites & Quality Assurance</strong></li>
    <li><strong>Installation, Operation & Runbook Guide</strong></li>
  </ol>
</div>

<!-- ================= SECTION 1 ================= -->
<h1>1. Executive Summary & System Vision</h1>
<p>
  <strong>FinGuard AI</strong> is a hybrid financial transaction risk-review and investigative support system engineered as a comprehensive platform for the study and practical application of <em>Artificial Intelligence and Expert Systems</em>. Modern automated risk-scoring engines often act as uninterpretable "black boxes" that output arbitrary probability scores without verifiable reasoning, resulting in regulatory opacity, high false-positive rates, and analyst burnout.
</p>
<p>
  FinGuard AI addresses this challenge through an <strong>explainability-first hybrid paradigm</strong> combining:
</p>
<ul>
  <li><strong>Deterministic Expert Rules</strong>: Human-engineered knowledge encoded as IF-THEN production rules that execute via forward-chaining inference and output verifiable deduction chains.</li>
  <li><strong>Statistical & Anomaly Intelligence</strong>: Unsupervised multidimensional anomaly detection (Isolation Forests) and behavioral feature extraction that isolate statistical outliers without hallucinating fraud certainty.</li>
  <li><strong>Investigation Case Management</strong>: A formal workflow bridging individual transactions into multi-event cases with unified evidence timelines, graph-based relational candidate discovery, and accountable reviewer dispositions.</li>
  <li><strong>Attributable Security & Cryptographic Auditing</strong>: Enterprise-grade RBAC, sliding-window brute-force rate limiting, and a mathematically verifiable SHA-256 hash chain that guarantees audit log tamper-evidence.</li>
</ul>

<div class="callout callout-blue">
  <strong>Guiding Engineering Principle:</strong><br>
  The system operates exclusively on genuine, persisted transaction records uploaded by users or analysts. It strictly rejects fabricated mock assessments, simulated live events, and pseudo-training on operational status fields. Every computation is reproducible and fully attributable.
</div>

<!-- ================= SECTION 2 ================= -->
<h1>2. Full System Architecture & Technology Stack</h1>
<p>
  FinGuard AI is built on a modern decoupled architecture designed for strict type safety, predictable execution, and zero vendor lock-in.
</p>

<div class="flow-container">
  <div class="flow-row">
    <div class="flow-box">
      <strong>User Interface Tier</strong>
      <span>React 18 · TypeScript 5.5 · Vite · Tailwind CSS</span>
    </div>
    <div class="flow-arrow">⇄</div>
    <div class="flow-box">
      <strong>API & Orchestration Tier</strong>
      <span>FastAPI 0.156 · Pydantic v2 · Python 3.14 venv</span>
    </div>
  </div>
  <div class="flow-row">
    <div class="flow-box" style="margin-left: 25%; width: 50%;">
      <strong>Analytical & AI Intelligence Engine</strong>
      <span>Forward-Chaining Engine · Scikit-Learn 1.9 · Audit Chainer</span>
    </div>
  </div>
  <div class="flow-row">
    <div class="flow-box" style="margin-left: 25%; width: 50%;">
      <strong>Persistence & Storage Tier</strong>
      <span>SQLAlchemy 2.1 · SQLite 3 (PRAGMA foreign_keys = ON)</span>
    </div>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th>Layer</th>
      <th>Technologies</th>
      <th>Key Architectural Responsibilities</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Frontend Client</strong></td>
      <td>React 18, TypeScript, Tailwind CSS, Vite</td>
      <td>Single-Page Application (SPA) offering Executive Dashboard, Real-time Transaction Analysis, CSV Batch Ingestion, Rules Explorer, ML Model Sandbox, Case Workspace, and Audit Governance.</td>
    </tr>
    <tr>
      <td><strong>Backend API</strong></td>
      <td>FastAPI, Uvicorn, Pydantic v2, Python 3.14</td>
      <td>Asynchronous REST endpoints, strict schema validation, dependency injection for RBAC, sliding-window rate limiting, and HTTP request correlation tracking.</td>
    </tr>
    <tr>
      <td><strong>Expert System</strong></td>
      <td>Python Custom Rete/Production Engine</td>
      <td>Declarative knowledge base, working memory management, forward chaining match-resolve-act cycles, cycle limit safeguards, and natural language explanation generation.</td>
    </tr>
    <tr>
      <td><strong>Machine Learning</strong></td>
      <td>Scikit-Learn, NumPy, SciPy, Joblib</td>
      <td>24-dimensional feature extraction, temporal anti-leakage history lookup, unsupervised Isolation Forest anomaly scoring, and data-gated supervised training pipeline.</td>
    </tr>
    <tr>
      <td><strong>Persistence</strong></td>
      <td>SQLAlchemy ORM, SQLite, Migrations Engine</td>
      <td>ACID-compliant relational storage, idempotent schema migrations, cascaded foreign-key constraints, and SHA-256 chained audit logs.</td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 3 ================= -->
<div class="page-break"></div>
<h1>3. Data Ingestion & Transaction Infrastructure (Phases 1 & 2)</h1>
<p>
  Transactions are the foundational unit of analysis in FinGuard AI. The data ingestion layer provides both interactive REST-based record entry and high-throughput batch CSV file ingestion.
</p>

<h2>3.1 Transaction Data Contract</h2>
<p>Every transaction record is stored with strict typing and schema constraints:</p>
<ul>
  <li><code>transaction_reference</code>: Unique business identifier (e.g., <code>TXN-20261021-001</code>). Collisions trigger HTTP 409 Conflict.</li>
  <li><code>timestamp</code>: UTC ISO 8601 datetime.</li>
  <li><code>amount</code>: Non-zero positive numerical currency value.</li>
  <li><code>currency</code>: Standard ISO currency code (<code>INR</code>, <code>USD</code>, <code>EUR</code>, <code>GBP</code>).</li>
  <li><code>sender_account</code> & <code>receiver_account</code>: Alphanumeric counterparty account strings.</li>
  <li><code>transaction_type</code>: Enumerated category (<code>PAYMENT</code>, <code>TRANSFER</code>, <code>WITHDRAWAL</code>, <code>DEPOSIT</code>).</li>
  <li><code>channel</code>: Operational routing channel (<code>MOBILE_APP</code>, <code>ONLINE_BANKING</code>, <code>ATM</code>, <code>BRANCH</code>, <code>POS</code>).</li>
  <li><code>status</code>: Operational settlement state (<code>COMPLETED</code>, <code>PENDING</code>, <code>FLAGGED</code>, <code>FAILED</code>, <code>CANCELLED</code>).</li>
  <li><code>dataset_provenance</code>: Explicit tracking of origin (e.g., <code>REALTIME_API</code> or <code>CSV_IMPORT:&lt;filename&gt;</code>).</li>
</ul>

<h2>3.2 Batch CSV Ingestion Pipeline</h2>
<p>The batch ingestion engine (<code>backend/app/api/transactions.py</code>) provides robust data integrity defenses:</p>
<ol>
  <li><strong>File Size & Extension Defense</strong>: Strictly enforces <code>.csv</code> format up to 5 MB (maximum 5,000 records per batch).</li>
  <li><strong>Atomic Transaction Processing</strong>: Validates rows prior to persistence; catastrophic syntax corruptions trigger a rollback, preventing dirty partial writes.</li>
  <li><strong>Reference Deduplication</strong>: Existing references are skipped or rejected with explicit line-number feedback.</li>
  <li><strong>Formula Injection Sanitization</strong>: Input cells starting with spreadsheet execution triggers (<code>=</code>, <code>+</code>, <code>-</code>, <code>@</code>) are neutralized before database persistence.</li>
</ol>

<!-- ================= SECTION 4 ================= -->
<h1>4. Rule-Based Expert System Engineering (Phase 3)</h1>
<p>
  The FinGuard AI Expert System provides fully explainable, transparent risk evaluation. Unlike black-box classifiers, it exposes the complete deductive chain from observed facts to derived conclusions.
</p>

<h2>4.1 Forward-Chaining Inference Engine</h2>
<p>
  The engine operates on a classical <strong>Match-Resolve-Act</strong> cycle:
</p>
<ol>
  <li><strong>Fact Extraction</strong>: Transaction properties and historical velocity metrics (e.g., sender transaction count over 1-hour and 24-hour windows) are asserted into Working Memory as a typed <code>FactSet</code>.</li>
  <li><strong>Pattern Matching</strong>: Antecedent conditions of all active rules in the Knowledge Base are evaluated against the current Working Memory. Satisfied rules form the <em>Conflict Set</em>.</li>
  <li><strong>Conflict Resolution</strong>: If multiple rules are eligible to fire, the arbiter selects rules using deterministic priority:
    $$\text{Rule Priority (descending)} \rightarrow \text{Condition Specificity (descending)} \rightarrow \text{Rule ID (lexicographical)}$$
  </li>
  <li><strong>Rule Execution (Act)</strong>: Winning rules fire, asserting new derived facts (e.g., <code>IS_HIGH_AMOUNT</code>, <code>IS_VELOCITY_BURST</code>) into Working Memory.</li>
  <li><strong>Iterative Chaining</strong>: The engine loops until <em>quiescence</em> (no new rules fire) or until hitting the cycle safety limit ($k_{\max} = 15$). Repeated firing of the same rule on unchanged facts is strictly prevented.</li>
</ol>

<h2>4.2 Active Knowledge Base Rule Catalog</h2>
<p>The system is initialized with seven production rules representing standard financial risk paradigms:</p>

<table>
  <thead>
    <tr>
      <th>Rule ID</th>
      <th>Rule Name</th>
      <th>Priority</th>
      <th>Antecedent Conditions</th>
      <th>Conclusions & Action</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>R001</code></td>
      <td>DATA_DEFICIENCY</td>
      <td>100</td>
      <td><code>sender_account == null</code> OR <code>receiver_account == null</code></td>
      <td>Asserts <code>DATA_QUALITY_ALERT</code>; flags incomplete counterparty metadata.</td>
    </tr>
    <tr>
      <td><code>R002</code></td>
      <td>HIGH_AMOUNT_INR</td>
      <td>80</td>
      <td><code>currency == 'INR'</code> AND <code>amount &ge; 200,000</code></td>
      <td>Asserts <code>IS_HIGH_AMOUNT</code>; adds 25 risk points.</td>
    </tr>
    <tr>
      <td><code>R003</code></td>
      <td>HIGH_AMOUNT_FX</td>
      <td>80</td>
      <td><code>currency IN ['USD','EUR','GBP']</code> AND <code>amount &ge; 5,000</code></td>
      <td>Asserts <code>IS_HIGH_AMOUNT</code>; adds 25 risk points.</td>
    </tr>
    <tr>
      <td><code>R004</code></td>
      <td>LATE_NIGHT_HIGH_VALUE</td>
      <td>85</td>
      <td><code>hour IN [23,0,1,2,3,4]</code> AND <code>IS_HIGH_AMOUNT == true</code></td>
      <td>Asserts <code>SUSPICIOUS_TIMING</code>; adds 30 risk points.</td>
    </tr>
    <tr>
      <td><code>R005</code></td>
      <td>HIGH_VELOCITY_BURST</td>
      <td>90</td>
      <td><code>sender_tx_count_1h &ge; 4</code></td>
      <td>Asserts <code>IS_VELOCITY_BURST</code>; adds 35 risk points.</td>
    </tr>
    <tr>
      <td><code>R006</code></td>
      <td>COMPOUND_HIGH_RISK</td>
      <td>95</td>
      <td><code>IS_HIGH_AMOUNT == true</code> AND <code>IS_VELOCITY_BURST == true</code></td>
      <td>Asserts <code>CRITICAL_SYNDROME</code>; escalates risk score by 40 points.</td>
    </tr>
    <tr>
      <td><code>R007</code></td>
      <td>STANDARD_CLEARANCE</td>
      <td>10</td>
      <td><code>IS_HIGH_AMOUNT == false</code> AND <code>IS_VELOCITY_BURST == false</code></td>
      <td>Asserts <code>ROUTINE_PROFILE</code>; assigns LOW risk level.</td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 5 ================= -->
<div class="page-break"></div>
<h1>5. Pattern Intelligence & Hybrid Machine Learning (Phase 4)</h1>
<p>
  Phase 4 integrates statistical machine learning alongside the deterministic rules engine, establishing a transparent hybrid evaluation framework.
</p>

<h2>5.1 Temporal Anti-Leakage Feature Engineering Pipeline</h2>
<p>
  Machine learning models in fraud detection frequently suffer from <em>data leakage</em>—evaluating historical transactions using aggregate statistics that include future events. FinGuard AI enforces strict temporal boundaries:
</p>
<ul>
  <li><strong>Past-Only Lookups</strong>: Historical metrics (sender mean amount, velocity, standard deviations) query only records where $t_{\text{historical}} < t_{\text{current}}$.</li>
  <li><strong>Currency Segregation</strong>: Sender baseline calculations are strictly partitioned by currency, preventing meaningless aggregations (e.g., averaging INR with USD).</li>
  <li><strong>24-Dimensional Numerical Feature Vector</strong>: Computes normalized log amount, hour-of-day sin/cos circular coordinates, historical z-scores, velocity ratios, and counterparty frequency.</li>
</ul>

<h2>5.2 Unsupervised Isolation Forest Anomaly Detection</h2>
<p>
  When $\ge 10$ historical transactions exist in the database, the system trains an unsupervised <code>IsolationForest</code> (100 estimators, 5% contamination). It outputs:
</p>
<ul>
  <li><strong>Continuous Anomaly Score</strong>: $\text{Score} \in [0.0, 1.0]$, calibrated such that values $> 0.65$ denote statistically elevated outliers.</li>
  <li><strong>Feature Deviation Insights</strong>: Identifies top $\sigma$-deviations showing which dimensions (e.g., amount, burst velocity) contributed to isolation.</li>
  <li><strong>Academic Disclosure</strong>: Explicitly presented as an unsupervised statistical anomaly indicator, not an authoritative fraud verdict.</li>
</ul>

<h2>5.3 Data-Gated Supervised Learning Pipeline</h2>
<p>
  FinGuard AI refuses to train supervised classifiers on settlement statuses (such as <code>COMPLETED</code> or <code>FLAGGED</code>). Instead, it implements a <strong>data-gated architecture</strong>:
</p>
<div class="callout callout-amber">
  <strong>Data-Gating Contract (<code>backend/app/ml/trainer.py</code>):</strong><br>
  Supervised training endpoints require explicit, verified ground-truth disposition labels. If verified labels are absent, degenerate, or single-class, training is cleanly refused with an explanatory HTTP 422 error detailing minimum sample requirements.
</div>

<h2>5.4 Multi-Paradigm Concordance Matrix</h2>
<p>
  The hybrid engine (<code>backend/app/services/hybrid_service.py</code>) compares rule-based conclusions with statistical anomaly scores across a four-quadrant concordance matrix:
</p>
<table>
  <thead>
    <tr>
      <th>Concordance Classification</th>
      <th>Rule Assessment</th>
      <th>ML Anomaly Score</th>
      <th>Operational Triage Recommendation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="badge badge-rose">CONCORDANT_HIGH_RISK</span></td>
      <td>HIGH / CRITICAL</td>
      <td>ELEVATED / HIGH (&gt; 0.65)</td>
      <td>Priority Case Investigation. Both rule heuristics and multidimensional anomaly detection indicate severe risk.</td>
    </tr>
    <tr>
      <td><span class="badge badge-amber">RULE_DRIVEN_EVALUATION</span></td>
      <td>HIGH / CRITICAL</td>
      <td>NORMAL (&le; 0.65)</td>
      <td>Policy Breach Review. Transaction triggers specific domain rule constraints despite falling within statistical norms.</td>
    </tr>
    <tr>
      <td><span class="badge badge-purple">DIVERGENT_ANOMALY_ALERT</span></td>
      <td>LOW / MEDIUM</td>
      <td>ELEVATED / HIGH (&gt; 0.65)</td>
      <td>Exploratory Anomaly Review. Transaction satisfies standard rules but represents a novel statistical outlier.</td>
    </tr>
    <tr>
      <td><span class="badge badge-emerald">CONCORDANT_ROUTINE</span></td>
      <td>LOW</td>
      <td>NORMAL (&le; 0.65)</td>
      <td>Routine Clearance. Both deterministic rules and anomaly models confirm standard transaction profile.</td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 6 ================= -->
<div class="page-break"></div>
<h1>6. Investigation Case Management & Relational Timeline (Phase 5)</h1>
<p>
  Phase 5 transforms FinGuard AI from isolated transaction assessment into an end-to-end investigative workspace.
</p>

<h2>6.1 Case Lifecycle State Machine</h2>
<p>
  Investigation cases transition through a strictly enforced state machine:
</p>
<pre><code>[OPEN]  ----&gt;  [IN_REVIEW]  &lt;---&gt;  [WAITING_FOR_INFORMATION]  ----&gt;  [CLOSED]
  ^                  |                                                  |
  |                  +--------------------------------------------------+
  +----------------------- (Reopen with Audit Log) ---------------------+</code></pre>
<ul>
  <li><strong>Review Priority</strong>: Triage levels (<code>LOW</code>, <code>MEDIUM</code>, <code>HIGH</code>, <code>CRITICAL</code>) indicate review urgency, strictly separated from confirmed fraud guilt.</li>
  <li><strong>Mandatory Final Disposition</strong>: Closure requires recorded justification under one of four formal categories:
    <code>CONFIRMED_FRAUD</code>, <code>CONFIRMED_LEGITIMATE</code>, <code>UNVERIFIED_SUSPICION</code>, or <code>INCONCLUSIVE</code>.
  </li>
</ul>

<h2>6.2 Relational Graph Intelligence</h2>
<p>
  When reviewing a case, the relational inspection engine (<code>backend/app/services/related_analysis_service.py</code>) crawls active transactions to discover relational candidates:
</p>
<ul>
  <li><strong>Shared Counterparties</strong>: Identifies transactions sharing exact sender or receiver accounts with linked case transactions.</li>
  <li><strong>Temporal Proximity</strong>: Identifies activity clusters occurring within a $\pm 24\text{h}$ window.</li>
  <li><strong>Channel Overlap</strong>: Flags recurring routing channels (e.g., repeated ATM bursts).</li>
  <li><strong>Factual Evidence Explanations</strong>: Matches provide clear reasoning (e.g., <em>"Matches sender account ACC-8821 within 2.4 hours"</em>) without drawing unverified legal conclusions.</li>
</ul>

<h2>6.3 Multi-Source Unified Evidence Timeline</h2>
<p>
  The timeline engine (<code>backend/app/services/timeline_service.py</code>) unifies chronological events across three distinct data sources into a single chronological narrative:
</p>
<ol>
  <li><strong>Transaction Ledger Events</strong> (<code>TRANSACTION_OCCURRED</code>): Original transaction executions.</li>
  <li><strong>AI Inference Snapshots</strong> (<code>ASSESSMENT_PERFORMED</code>): Expert system firings, risk scores, and ML anomaly updates.</li>
  <li><strong>Investigative Case Events</strong> (<code>CASE_CREATED</code>, <code>NOTE_POSTED</code>, <code>TRANSACTION_LINKED</code>, <code>CASE_CLOSED</code>): Attributable reviewer actions and notes.</li>
</ol>

<!-- ================= SECTION 7 ================= -->
<div class="page-break"></div>
<h1>7. Security Hardening, Cryptographic Audit & Reliability (Phase 6)</h1>
<p>
  Phase 6 establishes production-grade security, attributable access control, and operational reliability.
</p>

<h2>7.1 Role-Based Access Control (RBAC) Matrix</h2>
<p>
  Access control is enforced at the backend routing level via JWT claims validation. The frontend dynamically reflects role permissions:
</p>
<table>
  <thead>
    <tr>
      <th>System Capability</th>
      <th>Viewer (<code>VIEWER</code>)</th>
      <th>Risk Analyst (<code>ANALYST</code>)</th>
      <th>Security Admin (<code>ADMIN</code>)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Dashboard & Analytics</td>
      <td>Read-Only</td>
      <td>Full Access</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Transaction Ingestion & Creation</td>
      <td>Forbidden (Read-Only)</td>
      <td>Full Access</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Execute AI Risk Assessments</td>
      <td>Forbidden (Read-Only)</td>
      <td>Full Access</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Batch CSV Ingestion</td>
      <td>Forbidden (Read-Only)</td>
      <td>Full Access</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Case Management & Notes</td>
      <td>Forbidden (Read-Only)</td>
      <td>Create, Link, Note, Close</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Supervised Model Training</td>
      <td>Forbidden (403)</td>
      <td>Forbidden (403)</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>Audit Log Ledger & Verification</td>
      <td>Forbidden (403)</td>
      <td>Forbidden (403)</td>
      <td>Full Access</td>
    </tr>
    <tr>
      <td>User Provisioning & Status</td>
      <td>Forbidden (403)</td>
      <td>Forbidden (403)</td>
      <td>Full Access</td>
    </tr>
  </tbody>
</table>

<h2>7.2 Attributable Authentication & Rate Limiting</h2>
<ul>
  <li><strong>Password Hashing</strong>: Passwords are hashed using <code>bcrypt</code> with 12 work rounds. Plaintext passwords are never stored or logged.</li>
  <li><strong>Stateless JWT Tokens</strong>: Session tokens are signed using HMAC-SHA256 with configurable expiry (default 8 hours).</li>
  <li><strong>Sliding-Window Rate Limiter</strong>: Authentication endpoints enforce a sliding-window limit (5 failed attempts per IP/username per 60 seconds), returning HTTP 429 to mitigate brute-force attacks.</li>
</ul>

<h2>7.3 Tamper-Evident SHA-256 Cryptographic Audit Hash Chain</h2>
<p>
  Every sensitive administrative and investigative action creates an immutable, cryptographically chained audit log entry:
</p>
$$\text{Canonical}_k = \text{JSON}(\{ \text{actor}, \text{action}, \text{resource\_type}, \text{resource\_id}, \text{payload}, \text{ts} \})$$
$$\text{Hash}_k = \text{SHA-256}(\text{Canonical}_k \parallel \text{Hash}_{k-1})$$
<p>
  Where $\text{Hash}_0 = \text{"GENESIS\_CHAIN\_ROOT"}$.
</p>
<div class="callout callout-emerald">
  <strong>On-Demand Verification (<code>GET /api/audit/verify</code>):</strong><br>
  The verification algorithm traverses all $N$ records from genesis to the chain head. Any unauthorized row modification, insertion, deletion, or reordering causes hash divergence, identifying the exact tampered record ID.
</div>
<div class="callout callout-amber">
  <strong>Formal Security Boundary Disclosure:</strong><br>
  Cryptographic hash chaining inside the relational database provides tamper-evidence against application-level manipulation and unauthorized SQL updates. Absolute defense against an adversary with physical host-level write access to the SQLite file requires off-system replication to Write-Once-Read-Many (WORM) storage.
</div>

<h2>7.4 Operational Reliability Hardening</h2>
<ul>
  <li><strong>SQLite Foreign Keys</strong>: Enforced explicitly on every connection via <code>PRAGMA foreign_keys = ON;</code> in <code>session.py</code>.</li>
  <li><strong>Header CRLF Injection Defense</strong>: Incoming <code>X-Correlation-ID</code> headers are validated against <code>^[a-zA-Z0-9_\-\.]{1,64}$</code>. Malformed headers are stripped and replaced with a fresh UUID4.</li>
  <li><strong>Liveness & Readiness Probes</strong>: <code>GET /health</code> confirms process responsiveness; <code>GET /api/health/ready</code> verifies database connectivity, migration status, and rule engine initialization.</li>
</ul>

<!-- ================= SECTION 8 ================= -->
<div class="page-break"></div>
<h1>8. Database Schema & Relational Models Reference</h1>
<p>
  The SQLite relational database (<code>backend/finguard.db</code>) schema is managed through versioned idempotent migrations:
</p>

<table>
  <thead>
    <tr>
      <th>Table Name</th>
      <th>Primary Key</th>
      <th>Foreign Keys</th>
      <th>Key Columns & Constraints</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>transactions</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td>None</td>
      <td><code>transaction_reference</code> (UNIQUE), <code>amount</code> (REAL &gt; 0), <code>currency</code>, <code>sender_account</code>, <code>receiver_account</code>, <code>timestamp</code>, <code>dataset_provenance</code></td>
    </tr>
    <tr>
      <td><code>assessments</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td><code>transaction_id</code> &rarr; <code>transactions.id</code></td>
      <td><code>risk_score</code> (INTEGER 0–100), <code>risk_level</code>, <code>rules_triggered_json</code>, <code>inference_trace_json</code>, <code>model_version</code>, <code>hybrid_report_json</code></td>
    </tr>
    <tr>
      <td><code>cases</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td>None</td>
      <td><code>case_reference</code> (UNIQUE), <code>title</code>, <code>summary</code>, <code>status</code>, <code>priority</code>, <code>assigned_reviewer</code>, <code>final_disposition</code>, <code>created_at</code></td>
    </tr>
    <tr>
      <td><code>case_transactions</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td><code>case_id</code> &rarr; <code>cases.id</code><br><code>transaction_id</code> &rarr; <code>transactions.id</code></td>
      <td><code>linking_reason</code>, <code>linked_at</code>. Unique constraint on <code>(case_id, transaction_id)</code>.</td>
    </tr>
    <tr>
      <td><code>case_events</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td><code>case_id</code> &rarr; <code>cases.id</code></td>
      <td><code>event_type</code>, <code>source</code>, <code>actor</code>, <code>event_timestamp</code>, <code>metadata_json</code></td>
    </tr>
    <tr>
      <td><code>users</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td>None</td>
      <td><code>username</code> (UNIQUE), <code>email</code> (UNIQUE), <code>hashed_password</code>, <code>role</code> (<code>ADMIN</code>, <code>ANALYST</code>, <code>VIEWER</code>), <code>is_active</code></td>
    </tr>
    <tr>
      <td><code>audit_log</code></td>
      <td><code>id</code> (INTEGER)</td>
      <td>None</td>
      <td><code>actor_username</code>, <code>action</code>, <code>resource_type</code>, <code>resource_id</code>, <code>correlation_id</code>, <code>event_hash</code> (SHA-256), <code>previous_hash</code></td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 9 ================= -->
<div class="page-break"></div>
<h1>9. Complete REST API Specification</h1>
<p>
  All endpoints reside under <code>/api</code> and require Bearer JWT authentication (except authentication login and public health endpoints):
</p>

<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Method</th>
      <th>Required Role</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>/health</code></td>
      <td>GET</td>
      <td>Public</td>
      <td>Liveness probe returning process status.</td>
    </tr>
    <tr>
      <td><code>/api/health/ready</code></td>
      <td>GET</td>
      <td>Public</td>
      <td>Readiness probe verifying database connection and active rule count.</td>
    </tr>
    <tr>
      <td><code>/api/auth/login</code></td>
      <td>POST</td>
      <td>Public</td>
      <td>Rate-limited authentication endpoint returning JWT bearer token.</td>
    </tr>
    <tr>
      <td><code>/api/auth/me</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Returns profile and role claims of the authenticated user.</td>
    </tr>
    <tr>
      <td><code>/api/dashboard</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Aggregated transaction metrics, volume, currency breakdown, and risk totals.</td>
    </tr>
    <tr>
      <td><code>/api/transactions</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Paginated transaction search with currency, status, channel, and date filters.</td>
    </tr>
    <tr>
      <td><code>/api/transactions</code></td>
      <td>POST</td>
      <td>ANALYST+</td>
      <td>Creates a validated individual transaction record.</td>
    </tr>
    <tr>
      <td><code>/api/transactions/upload-csv</code></td>
      <td>POST</td>
      <td>ANALYST+</td>
      <td>Batch multipart CSV ingestion with schema validation and deduplication.</td>
    </tr>
    <tr>
      <td><code>/api/transactions/{id}/assess</code></td>
      <td>POST</td>
      <td>ANALYST+</td>
      <td>Executes hybrid rule-based inference and ML anomaly evaluation.</td>
    </tr>
    <tr>
      <td><code>/api/rules</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Lists all active production rules in the Expert Knowledge Base.</td>
    </tr>
    <tr>
      <td><code>/api/models/status</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Reports ML model readiness, feature schema version, and anomaly status.</td>
    </tr>
    <tr>
      <td><code>/api/models/train</code></td>
      <td>POST</td>
      <td>ADMIN</td>
      <td>Data-gated supervised classifier training over verified ground-truth labels.</td>
    </tr>
    <tr>
      <td><code>/api/cases</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Paginated investigation cases with status, priority, and search filters.</td>
    </tr>
    <tr>
      <td><code>/api/cases</code></td>
      <td>POST</td>
      <td>ANALYST+</td>
      <td>Creates a new investigation case with initial transaction link.</td>
    </tr>
    <tr>
      <td><code>/api/cases/{id}</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Case details with linked transaction snapshots and notes.</td>
    </tr>
    <tr>
      <td><code>/api/cases/{id}/timeline</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Unified multi-source chronological audit trail of case evidence.</td>
    </tr>
    <tr>
      <td><code>/api/cases/{id}/related</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Relational graph candidates matching counterparties or temporal windows.</td>
    </tr>
    <tr>
      <td><code>/api/cases/{id}/close</code></td>
      <td>POST</td>
      <td>ANALYST+</td>
      <td>Closes case with mandatory reviewer disposition and justification.</td>
    </tr>
    <tr>
      <td><code>/api/cases/{id}/export</code></td>
      <td>GET</td>
      <td>VIEWER+</td>
      <td>Generates forensic Markdown report with formula injection sanitization.</td>
    </tr>
    <tr>
      <td><code>/api/audit</code></td>
      <td>GET</td>
      <td>ADMIN</td>
      <td>Paginated audit log ledger with event type and actor filters.</td>
    </tr>
    <tr>
      <td><code>/api/audit/verify</code></td>
      <td>GET</td>
      <td>ADMIN</td>
      <td>Traverses and mathematically verifies the SHA-256 cryptographic hash chain.</td>
    </tr>
    <tr>
      <td><code>/api/users</code></td>
      <td>GET, POST</td>
      <td>ADMIN</td>
      <td>Lists users and provisions new accounts with assigned roles.</td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 10 ================= -->
<div class="page-break"></div>
<h1>10. Verification, Test Suites & Quality Assurance</h1>
<p>
  FinGuard AI maintains an automated test suite across all architectural layers:
</p>

<table>
  <thead>
    <tr>
      <th>Test Suite Module</th>
      <th>Tests</th>
      <th>Coverage Scope</th>
      <th>Result</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>test_endpoints.py</code></td>
      <td>2</td>
      <td>Baseline FastAPI health probes, CORS configuration, and initial dashboard serialization.</td>
      <td><span class="badge badge-emerald">PASSED (2/2)</span></td>
    </tr>
    <tr>
      <td><code>test_phase2_transactions.py</code></td>
      <td>12</td>
      <td>Transaction creation, uniqueness, validation errors, CSV batch parsing, deduplication, and metrics.</td>
      <td><span class="badge badge-emerald">PASSED (12/12)</span></td>
    </tr>
    <tr>
      <td><code>test_phase3_expert_system.py</code></td>
      <td>10</td>
      <td>Condition operators, multi-step inference chains, conflict resolution, cycle limits, and explanation traces.</td>
      <td><span class="badge badge-emerald">PASSED (10/10)</span></td>
    </tr>
    <tr>
      <td><code>test_phase4_ml_hybrid.py</code></td>
      <td>10</td>
      <td>Feature extraction anti-leakage, currency isolation, Isolation Forest anomaly scoring, and data-gating.</td>
      <td><span class="badge badge-emerald">PASSED (10/10)</span></td>
    </tr>
    <tr>
      <td><code>test_phase5_case_management.py</code></td>
      <td>9</td>
      <td>Case lifecycle transitions, transaction linking, notes, timeline synthesis, and export sanitization.</td>
      <td><span class="badge badge-emerald">PASSED (9/9)</span></td>
    </tr>
    <tr>
      <td><code>test_phase6_security_hardening.py</code></td>
      <td>10</td>
      <td>Bcrypt verification, JWT sessions, brute-force rate limiter, RBAC checks, SHA-256 hash chaining, and probes.</td>
      <td><span class="badge badge-emerald">PASSED (10/10)</span></td>
    </tr>
    <tr>
      <td><strong>Frontend Static Check (<code>tsc</code>)</strong></td>
      <td>&mdash;</td>
      <td>Full TypeScript typecheck across all routes, context providers, and components (<code>npx tsc --noEmit</code>).</td>
      <td><span class="badge badge-emerald">0 ERRORS</span></td>
    </tr>
    <tr>
      <td><strong>Frontend Production Build</strong></td>
      <td>&mdash;</td>
      <td>Vite production bundle compilation, asset minification, and CSS tree-shaking (<code>vite build</code>).</td>
      <td><span class="badge badge-emerald">BUILD CLEAN</span></td>
    </tr>
  </tbody>
</table>

<!-- ================= SECTION 11 ================= -->
<h1>11. Installation, Operation & Runbook Guide</h1>

<h2>11.1 Prerequisites</h2>
<ul>
  <li>Python 3.14 (or 3.11+) with <code>venv</code> module.</li>
  <li>Node.js 18+ and <code>npm</code>.</li>
  <li>Git 2.40+.</li>
</ul>

<h2>11.2 Backend Quickstart</h2>
<pre><code># 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # macOS / Linux

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Start backend server (port 8000)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload</code></pre>

<h2>11.3 Frontend Quickstart</h2>
<pre><code># 1. Navigate to frontend directory
cd frontend

# 2. Install node dependencies
npm install

# 3. Start development server (port 5173 with auto-proxy to port 8000)
npm run dev</code></pre>

<h2>11.4 Seeded Development Credentials</h2>
<p>The system automatically seeds initial accounts for local review and audit testing:</p>
<ul>
  <li><strong>Security Administrator</strong>: <code>username: admin</code> | <code>password: FinGuard@Admin2026!</code> (Full admin privileges)</li>
  <li><strong>Risk Analyst</strong>: <code>username: analyst</code> | <code>password: FinGuard@Analyst2026!</code> (Assessments & Cases)</li>
  <li><strong>Auditor / Viewer</strong>: <code>username: viewer</code> | <code>password: FinGuard@Viewer2026!</code> (Read-Only access)</li>
</ul>

<div style="margin-top: 40px; text-align: center; font-size: 8.5pt; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 14px;">
  FinGuard AI — Official Project Specification & Technical Architecture Master Document · Published October 2026
</div>

</body>
</html>
"""

def generate_pdf():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    downloads_dir = os.path.expanduser("~/Downloads")
    
    html_path = os.path.join(project_root, "FinGuard_AI_Complete_Specification.html")
    pdf_downloads_path = os.path.join(downloads_dir, "FinGuard_AI_Complete_Specification.pdf")
    pdf_project_path = os.path.join(project_root, "FinGuard_AI_Complete_Specification.pdf")
    
    print(f"Writing HTML to: {html_path}")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
        
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        
    if not os.path.exists(chrome_path):
        print(f"Error: Chrome executable not found at standard paths.")
        sys.exit(1)
        
    print(f"Invoking Chrome Headless to render PDF: {pdf_downloads_path}")
    cmd = [
        chrome_path,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_downloads_path}",
        "--no-pdf-header-footer",
        html_path
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Chrome failed with return code {res.returncode}: {res.stderr}")
        sys.exit(1)
        
    print("Chrome rendering complete.")
    
    # Also copy to project root
    if os.path.exists(pdf_downloads_path):
        size = os.path.getsize(pdf_downloads_path)
        print(f"Successfully generated PDF in Downloads: {pdf_downloads_path} ({size:,} bytes)")
        import shutil
        shutil.copyfile(pdf_downloads_path, pdf_project_path)
        print(f"Copied PDF to project root: {pdf_project_path}")
    else:
        print("Error: PDF output file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    generate_pdf()
