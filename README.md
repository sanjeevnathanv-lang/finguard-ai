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

## Deployment Guide (Unified Full-Stack)

FinGuard AI is architected as a **unified full-stack repository**. The FastAPI backend automatically serves the compiled React Single Page Application (SPA) alongside the `/api` REST endpoints from a single server and port.

### Option 1: 1-Click Deploy on Render (Recommended)

1. Push this repository to your GitHub account.
2. Sign in to [Render](https://render.com) and click **New +** $\to$ **Blueprint** (or connect your GitHub repository).
3. Select this repo. Render will automatically detect [`render.yaml`](render.yaml) and configure:
   - **Build Command**: `npm --prefix frontend install && npm --prefix frontend run build && pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
4. Click **Apply**. Your full-stack FinGuard AI application will be live at `https://your-app.onrender.com`.

### Option 2: Deploy with Docker / Docker Compose

A production-ready multi-stage [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) are included at the root:

```bash
# Build and run with Docker Compose
docker compose up --build -d

# Open http://localhost:8000 in your browser
```

### Option 3: Deploy on Railway / Heroku / Dokku

A root [`Procfile`](Procfile) is provided:
```bash
web: uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}
```
In your Railway/Heroku project settings:
- Add a buildpack for Node.js: `heroku/nodejs` (or build frontend via `npm --prefix frontend run build`)
- Add a buildpack for Python: `heroku/python`
- Deploy branch `main`.

### Option 4: Run Unified Full-Stack Locally

You can run both the frontend UI and backend API on a single port (`8000`) without running two separate servers:

```bash
# 1. Build the React frontend
npm run build

# 2. Start the unified FastAPI server
npm start
# or: uvicorn app.main:app --app-dir backend --port 8000
```
Visit `http://localhost:8000` to access the full application.

---

## Quick Start (Local Development)

### Terminal 1: Backend
```powershell
cd "backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs at `http://127.0.0.1:8000`. Interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Terminal 2: Frontend
```powershell
cd "frontend"
npm run dev
```
Dashboard opens at `http://localhost:5173`.

### Automated Test Suite
```powershell
cd "backend"
.\venv\Scripts\python.exe -m pytest -v
```
All 60 tests pass across database persistence, constraint enforcement, pagination, CSV schema validation, dashboard metrics, forward-chaining deduction, multi-step rule cycles, deterministic conflict resolution, feature extraction anti-leakage invariants, currency segregation, Isolation Forest anomaly scoring, data-gated supervised training, hybrid orchestration, access control, audit verification, and unified metrics reset.


---
*Notice: All demonstration records generated through the seed endpoint or sample CSV are synthetic and clearly marked with `is_synthetic: true`.*
