# FinGuard AI — Backend Documentation

FastAPI backend for FinGuard AI financial fraud intelligence, expert rules, and transaction data layer.

## Architecture (Phase 2)

- **Framework**: FastAPI with Pydantic v2 validation.
- **Data Persistence**: SQLAlchemy 2.0 ORM with local SQLite storage (`sqlite:///./finguard.db`).
- **Session Management**: Scoped generator-based dependency (`get_db`) with automatic teardown and `StaticPool` isolation in testing.
- **Security & Integrity**: Strict monetary Decimal precision, ISO 4217 currency checks, UTC normalization, duplicate prevention, and atomic transactional batch ingestion.

## Database Schema

### `transactions` Table
| Column | Type | Constraints / Description |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `reference` | String(64) | Unique business reference, indexed |
| `timestamp` | DateTime(UTC) | Transaction occurrence timestamp, indexed |
| `amount` | Numeric(18, 4) | Monetary value (> 0, non-NaN/inf) |
| `currency` | String(3) | ISO 4217 code (INR, USD, EUR, etc.), indexed |
| `sender_reference` | String(128) | Pseudonymized sender/account token |
| `receiver_reference`| String(128) | Pseudonymized merchant/receiver token |
| `transaction_type` | String(32) | PAYMENT, TRANSFER, WITHDRAWAL, etc. |
| `channel` | String(32) | ONLINE, MOBILE_APP, ATM, POS, BRANCH |
| `status` | String(32) | COMPLETED, PENDING, FLAGGED, FAILED, CANCELLED |
| `dataset_provenance`| String(64) | MANUAL_ENTRY, CSV_IMPORT:\<filename\>, SYNTHETIC_SEED |
| `is_synthetic` | Boolean | True for deterministic test fixtures, False for authentic |
| `created_at` | DateTime(UTC) | Record creation timestamp |
| `updated_at` | DateTime(UTC) | Record modification timestamp |

### `dataset_imports` Table
Tracks audit provenance for CSV batch ingestion batches (`import_reference`, `filename`, `total_rows`, `imported_rows`, `rejected_rows`, `status`).

## API Endpoints

- `GET /health` — Service health check (`{"status": "ok"}`).
- `GET /api/dashboard` — Live database-derived metrics (total volume, status counts, currency breakdown).
- `GET /api/transactions` — Paginated, filtered, and sorted transactions.
- `GET /api/transactions/{id}` — Individual transaction inspection.
- `POST /api/transactions` — Create single validated transaction record.
- `POST /api/transactions/upload` — Multipart CSV file ingestion with schema validation and row error report.
- `POST /api/demo/seed` — Seed deterministic synthetic transactions (50 by default).

## Local Development & Testing Commands (PowerShell)

```powershell
# Navigate to backend
cd "C:\Users\Sanjeev Nathan V\Downloads\findgaurd ai\backend"

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run automated test suite
pytest -v

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
