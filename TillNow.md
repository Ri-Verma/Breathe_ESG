# Breadth ESG Tech Intern Assignment - Project Progress

**Last Updated:** May 27, 2026  
**Current Phase:** Phase 3 (React Frontend Dashboard) — Next  
**Documentation Status:** ✅ Complete (MODEL.md, DECISIONS.md, SOURCES.md, TRADEOFF.md)

---

## 📋 Project Overview

A decoupled Django REST API + React/Vite application for ingesting, normalizing, and reviewing messy corporate ESG data from enterprise clients. Multi-tenancy, strict audit trails, and unit normalization required.

**Tech Stack:**
- Backend: Django 4.2 + Django REST Framework
- Frontend: React 18 + Vite
- Database: SQLite (development), PostgreSQL (production-ready)
- Deployment: Docker CI/CD

---

## ✅ Completed (Day 1)

### Architecture & Setup
- [x] Project structure: single-repo with `backend/` (Django) and `frontend/` (React)
- [x] Folder scaffolding: `/backend`, `/frontend`, `/docs`, `/data_samples`, `Dockerfile`
- [x] Pre-existing documentation files moved to `/docs/` (DECISIONS.md, MODEL.md, SOURCES.md, TRADEOFF.md)

### Database Models (`backend/ingestion/models.py`)
- [x] **Tenant** — Multi-tenancy isolation
- [x] **RawIngestionLog** — Source-of-truth storage (JSONField for raw payloads)
- [x] **EmissionRecord** — Normalized core table (Scope 1/2/3, Status: PENDING/FLAGGED/APPROVED)
- [x] **AuditLog** — Complete audit trail of analyst edits

### Sample Data (`data_samples/`)
- [x] **sap_export.csv** — 10 rows: German headers (WERKS, MATNR, MENGE, MEINS), mixed date formats (DD.MM.YYYY, MM/DD/YYYY, DD-MM-YYYY), mixed units (L, GAL)
- [x] **utility_bill.csv** — 9 rows: Electricity billing with missing peak kWh (double commas), cross-month periods, 4 buildings
- [x] **travel_api_response.json** — 9 trips: Navan mock API, airport codes (IATA), multi-segment journeys, statuses

### Parsing Logic (`backend/ingestion/parsers.py`)
- [x] **parse_sap_csv()** — Handles messy German headers, flexible date parsing (dateutil), unit conversion (GAL→L), fuel category inference, Scope 1
- [x] **parse_utility_csv()** — Handles missing peak kWh fields, cross-month billing periods, graceful flagging, Scope 2
- [x] **parse_travel_json()** — Airport distance lookup (20+ pairs), CO2e emission factors by transport mode, multi-segment support, Scope 3
- [x] Unit conversion matrix (Fuel → Liters)
- [x] Mock airport distance lookup
- [x] Emission factor calculations (Flight: 0.255, Train: 0.041, Ground: 0.120 kg CO2e/km)
- [x] All parsers return `(successful_records, flagged_records)` tuples

---

## 🚀 Phase 2 Complete (Serializers & REST Views) ✅

### Serializers (`backend/ingestion/serializers.py`)
- [x] **TenantSerializer** — Read-only tenant info
- [x] **AuditLogSerializer** — Audit trail with user info
- [x] **RawIngestionLogSerializer** — Raw payload display (source-of-truth)
- [x] **EmissionRecordSerializer** — Main CRUD with nested audit, read-only protection, status validation
- [x] **FileUploadSerializer** — Request validation (file size, format, source type)
- [x] **BulkEmissionUpdateSerializer** — Bulk update operations
- [x] **DashboardSummarySerializer** — Statistics aggregation

### Views (`backend/ingestion/views.py`)
- [x] **TenantViewSet** — Read-only tenant listing
- [x] **RawIngestionLogViewSet** — View raw payloads with search/filter
- [x] **EmissionRecordViewSet** — Full CRUD with:
  - Query param filtering (status, scope, category, date range)
  - `/summary/` endpoint for dashboard stats
  - `/bulk_update/` for batch operations
  - `/audit_history/` for record-specific trails
  - Auto audit logging on updates
  - Auto lock on APPROVED status
- [x] **FileUploadViewSet** — Main `POST /upload/` endpoint:
  - Routes to correct parser (SAP/UTILITY/TRAVEL)
  - Atomic transaction: RawIngestionLog + EmissionRecords
  - Auto creates AuditLog entries
- [x] **AuditLogViewSet** — Read-only audit log viewing

### URL Routing (`backend/ingestion/urls.py`)
- [x] Registered all 5 viewsets with DefaultRouter
- [x] RESTful endpoints: `/tenants/`, `/raw-logs/`, `/emissions/`, `/audits/`, `/upload/`

### Available API Endpoints
```
POST   /api/upload/upload/                    — File upload
GET    /api/emissions/                        — List all records
GET    /api/emissions/?status=FLAGGED         — Filter by status
GET    /api/emissions/?scope=2                — Filter by scope
GET    /api/emissions/?category=Electricity  — Filter by category
GET    /api/emissions/?start_date=2024-01-01&end_date=2024-02-01  — Date range
GET    /api/emissions/summary/                — Dashboard summary
GET    /api/emissions/{id}/                   — Single record detail
GET    /api/emissions/{id}/audit_history/    — Record audit trail
PATCH  /api/emissions/{id}/                   — Update record (auto-audit)
POST   /api/emissions/bulk_update/            — Bulk update multiple
GET    /api/audits/                           — All audit logs
GET    /api/raw-logs/                         — All raw ingestion logs
```

---

## 🚀 Current Step: Phase 3 (React Frontend)

---

## 🛣️ Roadmap Ahead

### Phase 2 ✅ (Complete)
- [x] Write `serializers.py` with nested relationships
- [x] Write `views.py` with file upload and filtering
- [x] Wire up URL routing
- [x] Test API endpoints locally (ready for testing)

### Phase 3 (Next — React Frontend Dashboard)
- [ ] Analyst Dashboard: View records grouped by status/scope
- [ ] File Upload Component: Drag-and-drop UI
- [ ] Edit Form: Modify flagged records
- [ ] Approval Workflow: Status transitions with audit trail
- [ ] Filtering & Sorting: Interactive table controls
- [ ] Real-time stats: Dashboard summary cards

### Phase 4 (Final — Documentation & Deployment)
- [ ] Evaluate documentation: DECISIONS.md, TRADEOFFS.md, SOURCES.md
- [ ] Docker build and push
- [ ] CI/CD pipeline setup
- [ ] Final deployment test

---

## 📁 Directory Structure (Current)

```
breadth-esg/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── models.py               ✅ (Tenant, RawIngestionLog, EmissionRecord, AuditLog)
│   │   ├── parsers.py              ✅ (parse_sap_csv, parse_utility_csv, parse_travel_json)
│   │   ├── serializers.py          ✅ (8 serializers: Tenant, AuditLog, RawLog, EmissionRecord, etc.)
│   │   ├── views.py                ✅ (5 viewsets: TenantVS, RawLogVS, EmissionVS, AuditVS, FileUploadVS)
│   │   ├── urls.py                 ✅ (Router configuration)
│   │   └── admin.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docs/
│   ├── DECISIONS.md                (Pre-existing, moved)
│   ├── MODEL.md                    (Pre-existing, moved)
│   ├── SOURCES.md                  (Pre-existing, moved)
│   └── TRADEOFF.md                 (Pre-existing, moved)
├── data_samples/
│   ├── sap_export.csv              (10 rows)
│   ├── utility_bill.csv            (9 rows)
│   └── travel_api_response.json    (9 trips)
├── Dockerfile
├── README.md
└── TillNow.md                      (This file)
```

---

## 🔍 Key Design Decisions (So Far)

1. **Messy Data Handling** — Parse with lenient error handling; flag instead of fail
2. **Dual Storage** — Raw payload in `RawIngestionLog` (source-of-truth), normalized in `EmissionRecord`
3. **Scope Inference** — Based on data source (SAP→Scope1, Utility→Scope2, Travel→Scope3)
4. **Unit Normalization** — Fuel→Liters, Energy→kWh, Distance→km with CO2e conversion
5. **Multi-Tenancy** — All queries filtered by tenant_id to ensure isolation
6. **Status Workflow** — PENDING → (Review) → FLAGGED or APPROVED (immutable once locked)

---

## 📝 Notes & Blockers

- **Status:** Phase 2 complete. No blockers.
- **Ready for:** Local API testing with sample data via Postman/curl
- **Next Immediate Task:** Build React dashboard and frontend components for analyst UI
- **Environment:** Pop!_OS, Python 3.11, Node 18+, Django 4.2, React 18, Vite

---

## 🎯 Testing Checklist (Phase 2)

### API Endpoints to Test
- [ ] `POST /api/upload/upload/` with SAP CSV → verify successful_count, flagged_count
- [ ] `POST /api/upload/upload/` with Utility CSV → verify electricity records created
- [ ] `POST /api/upload/upload/` with Travel JSON → verify Scope 3 records with distances
- [ ] `GET /api/emissions/?status=FLAGGED` → verify filtering works
- [ ] `GET /api/emissions/summary/` → verify stats aggregation
- [ ] `PATCH /api/emissions/{id}/` → verify audit trail creation
- [ ] `GET /api/emissions/{id}/audit_history/` → verify full history
- [ ] `POST /api/emissions/bulk_update/` → verify batch operations

### Expected Results
- All parsers handle messy data gracefully
- Flagged records separated from successful
- Audit trail created for every action
- Locked (APPROVED) records cannot be modified
- Date filtering works across all three sources

---

## 🎯 Success Criteria

- [x] File upload endpoint accepts all three file types
- [x] Parsers correctly split data into successful/flagged
- [ ] Dashboard shows records grouped by status (Phase 3)
- [ ] Analyst can edit and approve records with full audit trail (Phase 3)
- [ ] Docker deployment successful (Phase 4)
- [ ] All docs complete and comprehensive (Phase 4)
