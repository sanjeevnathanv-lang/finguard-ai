# FinGuard AI — Financial Transaction Intelligence & Expert System

FinGuard AI is a full-stack financial transaction fraud detection and risk assessment platform demonstrating traditional AI techniques (knowledge representation, rule-based systems, forward chaining, empirical anomaly detection, and decision trees) combined with modern data infrastructure.

## Project Structure

```text
findgaurd ai/
├─ backend/
│  ├─ app/
│  │  ├─ ai/
│  │  │  ├─ facts.py                 # Fact, FactSet, typed working memory
│  │  │  ├─ rules.py                 # RuleCondition, RuleConclusion, Rule AST
│  │  │  ├─ knowledge_base.py        # Declarative rule knowledge base v1.0.0
│  │  │  ├─ conflict_resolution.py   # Deterministic conflict resolution arbitrator
│  │  │  ├─ explanation.py           # InferenceTrace and human-readable explanation
│  │  │  ├─ inference_engine.py      # Forward-chaining match-resolve-act engine
│  │  │  └─ schemas.py               # Pydantic schemas for rule queries & evaluation
│  │  ├─ ml/
│  │  │  ├─ features.py              # Anti-leakage feature extraction (v1.0.0, 24 dimensions)
│  │  │  ├─ anomaly.py               # Unsupervised Isolation Forest outlier detector
│  │  │  ├─ trainer.py               # Data-gated supervised training pipeline
│  │  │  ├─ registry.py              # Model registry, readiness report & baseline fitting
│  │  │  └─ schemas.py               # Pydantic schemas for features, readiness, and metrics
│  │  ├─ api/
│  │  │  ├─ dashboard.py             # Dashboard metrics derived from DB
│  │  │  ├─ transactions.py          # CRUD, filtering, sorting, CSV ingestion
│  │  │  ├─ expert_system.py         # Knowledge base introspection & custom evaluation
│  │  │  ├─ assessments.py           # Transaction-to-assessment workflow endpoints
│  │  │  ├─ models.py                # Model readiness, evaluation & training endpoints
│  │  │  └─ analytics.py             # Persisted transaction pattern intelligence endpoints
│  │  ├─ core/
│  │  │  └─ config.py                # Environment settings and CORS
│  │  ├─ db/
│  │  │  ├─ models.py                # SQLAlchemy 2.0 ORM entities (Transactions, Assessments)
│  │  │  └─ session.py               # Engine & session management
│  │  ├─ schemas/
│  │  │  └─ transaction.py           # Pydantic v2 validation contracts
│  │  ├─ services/
│  │  │  ├─ fact_extractor.py        # Multi-feature & velocity DB fact extraction
│  │  │  ├─ assessment_service.py    # Assessment persistence and orchestration
│  │  │  ├─ hybrid_service.py        # Multi-paradigm Rules + ML hybrid orchestration
│  │  │  ├─ analytics_service.py     # Transaction pattern intelligence aggregator
│  │  │  └─ transaction_service.py   # Repository, business logic, CSV parsing
│  │  └─ main.py                     # FastAPI application & lifespan
│  ├─ tests/
│  │  ├─ conftest.py                 # Isolated SQLite in-memory test fixtures
│  │  ├─ test_endpoints.py           # Health & dashboard integration tests
│  │  ├─ test_phase2_transactions.py # Phase 2 transactions & CSV test suite
│  │  ├─ test_phase3_expert_system.py# Phase 3 forward-chaining & rules test suite
│  │  └─ test_phase4_ml_hybrid.py    # Phase 4 features, anomaly, training & hybrid suite
│  ├─ pytest.ini
│  ├─ requirements.txt
│  └─ README.md
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  │  ├─ Sidebar.tsx              # Navigation sidebar with Phase milestones
│  │  │  ├─ StatusBadge.tsx          # Engine status indicators
│  │  │  ├─ LoadingSpinner.tsx       # Async loading spinner
│  │  │  └─ AssessmentModal.tsx      # 4-tab Hybrid AI explainable inference audit modal
│  │  ├─ routes/
│  │  │  ├─ Dashboard.tsx            # Live database-backed metrics dashboard
│  │  │  ├─ TransactionAnalysis.tsx  # Filterable table with per-transaction Expert AI assessment
│  │  │  ├─ CSVImport.tsx            # CSV file drag-and-drop & row error review
│  │  │  ├─ ExpertRulesExplorer.tsx  # Knowledge base viewer & interactive inference sandbox
│  │  │  └─ ModelEvaluation.tsx      # Model readiness report, training sandbox & pattern analytics
│  │  ├─ lib/
│  │  │  └─ api.ts                   # Typed REST API client (Transactions, Rules, Hybrid, ML)
│  │  ├─ App.tsx                     # Root layout & active route switch
│  │  ├─ main.tsx
│  │  └─ index.css
│  ├─ index.html
│  ├─ package.json
│  ├─ vite.config.ts                 # Vite config with PostCSS & backend reverse proxy
│  ├─ tailwind.config.js
│  └─ tsconfig.json
├─ .gitignore
├─ .env.example
└─ README.md
```

## Quick Start (Windows PowerShell)

### Terminal 1: Backend
```powershell
cd "C:\Users\Sanjeev Nathan V\Downloads\findgaurd ai\backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs at `http://127.0.0.1:8000`. Interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Terminal 2: Frontend
```powershell
cd "C:\Users\Sanjeev Nathan V\Downloads\findgaurd ai\frontend"
npm run dev
```
Dashboard opens at `http://localhost:5173`.

### Automated Test Suite
```powershell
cd "C:\Users\Sanjeev Nathan V\Downloads\findgaurd ai\backend"
.\venv\Scripts\python.exe -m pytest -v
```
All 34 tests pass across database persistence, constraint enforcement, pagination, CSV schema validation, dashboard metrics, forward-chaining deduction, multi-step rule cycles, deterministic conflict resolution, feature extraction anti-leakage invariants, currency segregation, Isolation Forest anomaly scoring, data-gated supervised training, and hybrid orchestration.

---
*Notice: All demonstration records generated through the seed endpoint or sample CSV are synthetic and clearly marked with `is_synthetic: true`.*
