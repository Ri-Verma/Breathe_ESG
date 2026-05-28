# Breadth ESG — Emissions Data Ingestion & Analyst Dashboard

A Django REST API + React dashboard for ingesting messy corporate ESG data from three enterprise sources (SAP, Utility, Travel), normalizing it, and surfacing a review dashboard where analysts can approve rows before audit lock.

## Project Overview

Built for the Breathe ESG Tech Intern Assignment. The platform handles:
- **Multi-source ingestion** — SAP flat files (fuel/procurement), utility portal CSVs (electricity), travel API JSON (flights/ground)
- **Unit normalization** — GAL→L, kWh passthrough, km→kgCO2e with emission factors
- **Scope classification** — Scope 1 (SAP), Scope 2 (Utility), Scope 3 (Travel)
- **Analyst review workflow** — PENDING → FLAGGED / APPROVED (locked for audit)
- **Full audit trail** — Every edit tracked with before/after state diffs
- **Multi-tenancy** — Tenant isolation at the model level

## Project Structure

```
breadth-esg/
├── backend/                        # Django REST API
│   ├── core/                       # Settings, URL routing, WSGI
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── ingestion/                  # Data ingestion app
│   │   ├── models.py               # Tenant, RawIngestionLog, EmissionRecord, AuditLog
│   │   ├── views.py                # 5 ViewSets (Tenant, RawLog, Emission, Audit, Upload)
│   │   ├── serializers.py          # 7 serializers with validation
│   │   ├── parsers.py              # SAP CSV, Utility CSV, Travel JSON parsers
│   │   ├── urls.py                 # DRF Router configuration
│   │   └── migrations/             # Database migrations
│   ├── manage.py
│   ├── db.sqlite3
│   └── requirements.txt
│
├── frontend/                       # React + Vite Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx      # Drag-drop upload with source type selection
│   │   │   ├── Dashboard.jsx       # Summary cards + scope breakdown
│   │   │   ├── MetricsDisplay.jsx  # Filterable/sortable records table
│   │   │   ├── EditRecord.jsx      # Modal for editing records + status transitions
│   │   │   └── AuditTrail.jsx      # Timeline view of record changes
│   │   ├── App.jsx                 # Main orchestrator with state management
│   │   ├── main.jsx                # Entry point
│   │   └── index.css               # Global styles (700+ lines)
│   ├── index.html
│   ├── package.json
│   └── vite.config.js              # Proxy config → Django backend
│
├── docs/                           # Assignment deliverables
│   ├── MODEL.md                    # Data model & why (35% of grade)
│   ├── DECISIONS.md                # Ambiguity resolutions & justifications
│   ├── TRADEOFF.md                 # 3 things deliberately not built
│   └── SOURCES.md                  # Real-world source research
│
├── data_samples/                   # Fabricated realistic sample data
│   ├── sap_export.csv              # SAP flat file (German headers, mixed units)
│   ├── utility_bill.csv            # Utility portal export (missing peak kWh)
│   └── travel_api_response.json    # Navan-style travel API (airport codes)
│
├── Dockerfile                      # Container build (backend + frontend)
└── README.md                       # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for deployment)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` (proxies `/api/*` to Django)

### Quick Test

1. Open `http://localhost:5173`
2. Upload `data_samples/sap_export.csv` with source type "SAP"
3. Dashboard updates with 14 records
4. Filter by status, edit flagged records, approve pending ones
5. View audit trail for any record

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/` | Upload file (CSV/JSON) with source type |
| `GET` | `/api/emissions/` | List all emission records (filterable) |
| `GET` | `/api/emissions/summary/` | Dashboard summary stats |
| `GET` | `/api/emissions/{id}/` | Single record detail |
| `PATCH` | `/api/emissions/{id}/` | Update record (creates audit log) |
| `GET` | `/api/emissions/{id}/audit_history/` | Record's full audit trail |
| `POST` | `/api/emissions/bulk_update/` | Bulk status update |
| `GET` | `/api/tenants/` | List tenants |
| `GET` | `/api/raw-logs/` | Raw ingestion logs (source-of-truth) |
| `GET` | `/api/audits/` | All audit log entries |

### Query Parameters

```
GET /api/emissions/?status=FLAGGED          # Filter by status
GET /api/emissions/?scope=2                 # Filter by scope
GET /api/emissions/?category=Electricity    # Filter by category
GET /api/emissions/?start_date=2024-01-01&end_date=2024-12-31  # Date range
```

## Data Models

### Tenant
Multi-tenancy isolation. Every client organization gets a Tenant record.

### RawIngestionLog
Source-of-truth storage. Stores the exact raw payload (JSONField) before any parsing.

### EmissionRecord
Normalized core table. Fields: scope (1/2/3), category, activity_date, original_value/unit, normalized_value/unit, status (PENDING/FLAGGED/APPROVED), is_locked.

### AuditLog
Tracks every analyst modification. Stores previous_state and new_state as JSON, linked to the modified EmissionRecord and the User who made the change.

## Docker Deployment

```bash
docker build -t breadth-esg .
docker run -p 8000:8000 breadth-esg
```

## Features

### Backend
- **Three-source ingestion** — SAP CSV, Utility CSV, Travel JSON with source-specific parsers
- **Unit normalization** — GAL→L, emission factor calculations (kgCO2e)
- **Flagging engine** — Missing fields, unrecognized units, unknown airport pairs → auto-flagged
- **Audit trail** — Every create/update/approve logged with before/after state
- **Approval lock** — APPROVED records become immutable
- **Multi-tenancy** — Tenant FK on all data models

### Frontend
- **Drag-and-drop upload** — Source type selection (SAP/Utility/Travel)
- **Dashboard overview** — Total records, status counts, scope breakdown chart
- **Records table** — Filter by status/scope/category, sort by date/emissions/status
- **Edit & approve workflow** — Modal form for flagged/pending records
- **Audit trail viewer** — Timeline of all changes with expandable state diffs
- **Notifications** — Success/error feedback with auto-dismiss
- **Responsive design** — Mobile, tablet, desktop tested

## Documentation

See the `/docs/` directory for required assignment deliverables:
- **MODEL.md** — Data model design and justifications
- **DECISIONS.md** — Every ambiguity resolved with rationale
- **TRADEOFF.md** — Three things deliberately not built
- **SOURCES.md** — Real-world research for each data source

## License

MIT License
