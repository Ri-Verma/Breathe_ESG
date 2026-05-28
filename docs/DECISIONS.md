# Architecture Decisions

This document records every ambiguity resolved during design and what was chosen, why, and what we'd ask the PM to clarify.

---

## Decision 1: Ingestion Mechanism

**Ambiguity:** How do we get data from clients? Real-time API? Batch file upload? Manual paste?

**Chosen:** File upload (CSV/JSON) for all three sources.

**Why:**
- **SAP:** Enterprise clients don't expose SAP APIs to external parties. They export IDocs as flat CSV files (often with German headers). File upload is practical.
- **Utility:** Utilities rarely offer APIs to businesses (except large enterprise contracts). Facilities teams export CSV from portals or copy-paste from bills. File upload is realistic.
- **Travel:** While Navan/Concur APIs exist, they require enterprise OAuth. For a 4-day MVP, we mock the API response and allow JSON upload. In production, we'd implement OAuth + scheduled API pulls.

**What we're NOT handling:** Real-time API polling (future Phase 2).

**PM Question:** Should we build OAuth integration for Navan/Concur immediately, or is mocked JSON sufficient for pilot?

---

## Decision 2: SAP Data Format

**Ambiguity:** SAP exports in dozens of formats (IDoc, OData, BAPI, flat CSV). Which is realistic?

**Chosen:** Flat CSV export with IDoc-like structure.

**Why:**
- IDoc (`ORDERS`, `INVOIC`) is SAP's legacy EDI format. Exports to flat CSV contain:
  - German column headers (WERKS=plant, MATNR=material, MENGE=quantity, MEINS=unit)
  - Mixed date formats (DD.MM.YYYY, MM/DD/YYYY depending on SAP instance config)
  - Mixed units (L for liters, GAL for gallons, sometimes inconsistent)
  - Plant codes (P100, P200) that require external lookup tables
- This is what actual enterprise clients send us (we researched SAP export documentation)

**What we're NOT handling:**
- OData services (complex, requires SAP Gateway setup)
- BAPI remote calls (requires Middleware)
- PDF invoices (OCR too brittle for 4-day sprint)

**PM Question:** Do clients use standard SAP material master (MAKT table) lookups, or is plant code mapping custom per client?

---

## Decision 3: Utility Data Format

**Ambiguity:** Utilities deliver data as PDFs, portal CSVs, or APIs. Which?

**Chosen:** Portal CSV export.

**Why:**
- Most facilities teams receive monthly CSV exports from utility portals (e.g., Enel Connect, EDF Web)
- CSV contains meter readings, billing periods (often 15-45 days, crossing calendar months), peak/off-peak splits, sometimes missing fields
- PDF bills require OCR, which is unreliable and distracts from core logic in a 4-day sprint
- APIs are rare (except in OECD regions with smart meters)

**What we handle:**
- Billing periods that don't align with calendar months (e.g., Jan 15 – Feb 14)
- Missing peak/off-peak fields (double commas in CSV)
- Multiple meters per building
- kWh normalization (no conversion needed)

**What we're NOT handling:**
- PDF parsing (OCR brittle)
- API integrations to specific utilities
- Tariff structures (peak rates vs. off-peak) — we flag if missing, but don't recalculate consumption

**PM Question:** Do we need to ingest tariff cost data to calculate Scope 2 emissions, or just consumption (kWh)?

---

## Decision 4: Travel Data Format

**Ambiguity:** Navan/Concur APIs exist, but require OAuth. For MVP, how?

**Chosen:** Mock JSON payload based on actual Navan API schema.

**Why:**
- OAuth setup adds 2+ days of integration work
- Navan API provides trip segments with origin/destination airport codes (IATA: JFK, LHR, SFO)
- Distances between airports are NOT provided by API; we calculate via lookup table
- JSON upload allows us to demonstrate parsing, distance calculation, and CO2e factors without API infrastructure

**What we handle:**
- Airport code → distance lookup (20+ common routes)
- Multi-segment trips (flight + ground)
- Emission factors by transport mode (Flight: 0.255, Train: 0.041, Ground: 0.120 kg CO2e/km)
- Filtering by trip status (COMPLETED vs. CANCELLED)

**What we're NOT handling:**
- Real OAuth/Navan API (Phase 2)
- Hotel stays, meals, car rentals (Scope 3 but outside MVP scope)
- Actual distance API (e.g., Google Maps) — only hardcoded lookup

**PM Question:** Should we integrate with actual Navan OAuth for pilot customers, or delay until Phase 2?

---

## Decision 5: Unit Normalization Strategy

**Ambiguity:** How do we handle inconsistent units across sources?

**Chosen:** Store both original and normalized units.

**Why:**
- **Auditor requirement:** Auditors want to see original values ("client sent 500 GAL")
- **Calculation requirement:** Carbon math needs standard units (all liters, all kWh)
- **Validation:** If normalization math is questioned, we show both

**Conversion matrix:**
```python
{
  'GAL': 3.78541,   # US Gallon → Liters
  'L': 1.0,
  'kWh': 1.0,       # No conversion needed
  'km': 1.0,        # No conversion needed
}
```

**Scope 3 travel:** Distance in km × emission factor (kg CO2e/km) = normalized_value in kgCO2e

**PM Question:** Are there source-specific conversion rules (e.g., diesel vs. gasoline emission factors)?

---

## Decision 6: Flagging Strategy

**Ambiguity:** When data is messy, do we reject or flag?

**Chosen:** Flag, don't reject. Parse leniently.

**Why:**
- Analyst should see bad data, not a upload failure
- Flagged records trigger dashboard alerts
- Analyst can manually override (e.g., "this unit should be L, not unknown")
- Audit trail logs the override

**Flagging triggers:**
- Missing required fields (no date, no quantity)
- Unrecognized unit (e.g., 'BBL' for barrels)
- Invalid date format (can't parse)
- Missing distance (for travel)
- Missing peak/offpeak split (for utility, but not critical)

**PM Question:** Should auto-reject (fail fast) or auto-flag (analyst reviews)? We chose flag for user experience.

---

## Decision 7: Analyst Approval Workflow

**Ambiguity:** How do flagged records get fixed and approved?

**Chosen:** Dashboard edit + status transitions + locking.

**Why:**
- Analyst can manually fix and update `normalized_value`, `normalized_unit`, `category`
- Status transition: `PENDING` → `FLAGGED` (if issues) or `APPROVED` (if clean)
- Once `APPROVED`, record is locked (`is_locked=True`)
- Every edit creates audit trail entry
- Non-engineer users can operate this (business analyst, sustainability lead)

**What we're NOT handling:** Delegated approval workflows (e.g., L1 Analyst → L2 Manager → Auditor).

**PM Question:** Should different user roles (Analyst vs. Manager) have different approval authorities?

---

## Decision 8: Data Isolation (Multi-Tenancy)

**Ambiguity:** How do we prevent Tenant A from seeing Tenant B's data?

**Chosen:** Foreign key at table level + query filtering.

**Why:**
- Every table (RawIngestionLog, EmissionRecord, AuditLog) has `tenant_id`
- All Django queries include `.filter(tenant=current_tenant)` (enforced in viewset)
- No shared tables across tenants
- Future: can add row-level encryption for additional security

**What we're NOT handling:** Per-user permissions within a tenant (Phase 2).

**PM Question:** Should we support role-based access within a tenant (e.g., "this analyst can only see Scope 2 records")?

---

## Decision 9: State Management

**Ambiguity:** How do we prevent analysts from editing APPROVED records?

**Chosen:** `is_locked` boolean + status validation.

**Why:**
- If status == 'APPROVED', then `is_locked = True`
- Serializer validation rejects updates to locked records
- Prevents accidental overwrite of data sent to auditors
- UX shows "🔒 Locked" badge

**What we're NOT handling:** Workflow engine (Temporal, Celery) for multi-step approvals.

---

## Decision 10: Batch vs. Single Record Upload

**Ambiguity:** Do analysts upload one record at a time or entire files?

**Chosen:** Entire files (SAP CSV with 1000 rows → 1 RawIngestionLog + 1000 EmissionRecords).

**Why:**
- Realistic: facilities teams send monthly SAP extracts, not one row per upload
- More efficient: single parsing pass, single audit trail entry for upload event
- Logical: file-level traceability (which SAP export generated these records?)

**PM Question:** Should we support single-row corrections via API, or only re-upload entire files?

---

## Decision 11: CORS and Frontend Integration Proxy

**Ambiguity:** How to handle CORS and API requests during local development and testing.

**Chosen:** Vite dev server API proxy.

**Why:**
- Avoids configuring permissive CORS headers on the Django backend during development.
- Configured in `frontend/vite.config.js` to route all requests starting with `/api` to `http://localhost:8000` transparently.
- Simplifies testing since the frontend and backend appear to run on the same origin from the browser's perspective.

**PM Question:** Should we provide a production reverse proxy configuration (e.g., Nginx) or rely on Django CORS settings for staging?

---

## Decision 12: Anonymous User Handling in Audit Logs

**Ambiguity:** How to record changes and ingestion events in the audit log when user authentication is bypassed (e.g., local development or anonymous file ingestion).

**Chosen:** Allow `user` field in `AuditLog` to be null / blank.

**Why:**
- Prevents database constraint failures during initial setup and testing when uploads or updates are done anonymously.
- Retains complete historical traceability (timestamps, action details, state diffs) even when not linked to a specific authenticated user.
- Readily supports transition to user accounts and session/JWT authentication.

**PM Question:** For production, should we require authentication for all endpoints (including file upload) or fallback to a "System" service account for automated uploads?

---

## What We Didn't Ask the PM (But Should Have)

1. **Emission factors:** Are Scope 3 travel factors (0.255 kg CO2e/km for flights) company-specific or industry standard?
2. **Scope 2 calculation:** Do we calculate emissions from kWh + grid carbon intensity (varies by region/utility), or just store kWh?
3. **Material master:** Do SAP material codes (MATNR) map to standard commodity codes (e.g., UNSPSC), or is lookup custom per client?
4. **Audit retention:** How long must we retain raw payloads and audit logs? 7 years? Forever?
5. **Multi-year:** Does analyst need year-over-year comparison, or just current-year ingestion?

---

## Subset of Each Source We're Handling

### SAP
- ✅ Fuel & procurement (diesel, gasoline, oils)
- ✅ German headers + mixed date formats
- ✅ Mixed units (L, GAL)
- ❌ Material master lookups (we accept MATNR as-is)
- ❌ Plant hierarchy (we store plant code but don't map to location)

### Utility
- ✅ Electricity consumption (kWh)
- ✅ Billing periods crossing calendar months
- ✅ Missing peak/offpeak fields
- ✅ Multiple meters per building
- ❌ Tariff structures (cost data)
- ❌ Demand charges (kW)
- ❌ Gas, water, waste streams

### Travel
- ✅ Flights (distance lookup from airport codes)
- ✅ Train, ground transport
- ✅ Multi-segment trips
- ✅ Cabin class (economy vs. business factor)
- ❌ Hotels, meals, rental cars
- ❌ Real distance API (hardcoded lookup only)
- ❌ Actual Navan OAuth (mocked JSON upload)