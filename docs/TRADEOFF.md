# Three Things We Deliberately Did Not Build (And Why)

---

## Tradeoff 1: Role-Based Access Control (RBAC)

### What We Didn't Build

Per-tenant user roles and permissions. Specifically:
- Analyst can review & edit flagged records
- Manager can only approve
- Auditor can view read-only audit trail
- Admin can manage users and tenants

### Why We Didn't

1. **Time constraint:** RBAC (roles, permissions, middleware) adds 1.5+ days of development in Django
2. **MVP validation:** Pilot customers don't need role separation yet. A single analyst role is sufficient.
3. **Complexity vs. value:** Adds database tables (Role, Permission), serializer validation, viewset filtering — 500+ lines of code for feature not used in first 4 days
4. **Django-guardian exists:** If/when needed, django-guardian provides object-level permissions (drop-in)

### Cost of Not Having It

- **Security risk:** All authenticated users see all tenant data (assuming single tenant in MVP). In production, we'd add tenant-level isolation (already in models, just not enforced at view level yet).
- **User experience:** Can't delegate; one person must do all analysis and approval

### When to Build It

- After pilot feedback: "We need Manager approval before audit handoff"
- Real customer: "Our team has 5 analysts + 2 managers"
- Compliance requirement: "Segregation of duties"

---

## Tradeoff 2: Automated Emission Factor Calculation

### What We Didn't Build

Dynamic emission factors based on:
- **Source-specific data:**
  - Electricity: Grid carbon intensity by region (US: 400–800 gCO2e/kWh depending on state; UK: 200–300 gCO2e/kWh)
  - Flights: Aircraft type (A380 vs. regional jet), load factor (% seats filled), altitude (RFI multiplier for contrails)
  - Fuel: Specific energy content per fuel type, combustion efficiency
- **Time-specific data:**
  - Electricity: Seasonal factors (coal-heavy grid in winter vs. hydro in summer)
  - Travel: Year-over-year grid updates (electricity getting cleaner annually)
- **Audit trail for factors:** Track which factor version was used for which calculation

### Why We Didn't

1. **Data sourcing complexity:** Reliable emission factors come from ICAO (aviation), UK BEIS (electricity), EPA (vehicle). Each requires API or manual sync.
2. **Time investment:** Building a factor management system (versioning, per-region, per-fuel-type) is 2+ days.
3. **Scope 2 especially difficult:** Grid carbon intensity varies by utility, by hour (if using real-time grid data). US EPA publishes regional factors annually; we'd need to sync and version them.
4. **MVP validation:** Pilot customers accept static factors (0.255 kg CO2e/km flight). Refinement comes after feedback.

### What We Do Instead

- **Hardcoded static factors** in `parsers.py`:
  ```python
  emission_factors = {
      'FLIGHT': 0.255,      # kg CO2e per km (average economy)
      'TRAIN': 0.041,       # kg CO2e per km (UK average)
      'GROUND': 0.120,      # kg CO2e per km (car avg)
  }
  ```
- **For electricity:** Store kWh only; downstream system applies grid factor
- **For fuel:** Use simplified combustion math (kg fuel × density × emissions per kg)

### Cost of Not Having It

- **Accuracy loss:** Using global averages instead of regional data over-estimates (e.g., Norway's hydropower grid vs. US coal)
- **Audit questions:** Real auditors will ask "why did you use 0.255 and not 0.240?" We'd need to document factor source.
- **Year-over-year comparisons:** Can't show that grid got cleaner if we use same factor every year

### When to Build It

- Customer asks: "Our auditor wants grid-specific carbon intensity"
- Compliance requirement: ISO 14064-1 mentions factor sourcing
- Scale: 10+ tenants each requesting custom factors
- Phase 2 scope expansion

---

## Tradeoff 3: Real-Time Data Integrations (OAuth + Scheduled Pulls)

### What We Didn't Build

- **Navan/Concur OAuth:** Real API authentication, token refresh, scheduled API pulls
- **Utility API integrations:** EDF, Enel, Schneider Electric APIs (where available) for automatic meter reading sync
- **SAP OData service:** Real connection to SAP systems (requires middleware, network access)

**MVP Approach:** File upload only (CSV/JSON).

### Why We Didn't

1. **Authentication & authorization are separate from business logic:** OAuth, API credentials, key rotation — best handled with proper DevOps infrastructure (AWS Secrets Manager, HashiCorp Vault).
2. **Scheduled polling complexity:** Celery (task queue) adds infrastructure (Redis/RabbitMQ). For MVP with 1 test client, file upload is faster to validate.
3. **Data freshness tradeoff:** MVP assumes monthly batch uploads. Real-time polling would require alerting on data changes (edge case until customer requests it).
4. **Network/firewall complexity:** SAP OData requires VPN or SAP Cloud Connector. Utility APIs require IP whitelisting. Not portable across customers without custom setup.
5. **Testing nightmare:** Would need mock API servers for every integration. File upload tests are simpler.

### What We Do Instead

- **File upload endpoint:** Analyst uploads SAP CSV, Utility CSV, or Travel JSON
- **Manual scheduling:** Analyst runs upload job monthly (or we document how PM could add scheduler later)
- **Mocked API responses:** Travel data uses mocked Navan JSON structure (documents what real integration would look like)

### Cost of Not Having It

- **Manual overhead:** Analyst must download & upload files monthly (vs. automatic sync)
- **Lag:** Data ingested 1–2 days after source system generates it (vs. real-time)
- **No change detection:** Can't identify anomalies ("fuel spend jumped 20% vs. last month") in automated way

### When to Build It

- Customer scales to 100+ data imports per month (manual uploads become bottleneck)
- Real-time auditing requirement: "Alert if emissions spike"
- Navan/Concur contract includes API access (customer expects integration)
- Infrastructure budget approved (Celery, Redis, DevOps setup)

---

## Tradeoff 4: Row-Level Payload Storage vs. File-Level Ingestion Logging

### What We Didn't Build

Storing the full raw JSON payload of every individual row or travel segment directly inside the database on a per-record basis.

### Why We Didn't

1. **Database Efficiency:** Storing duplicate or stringified raw dictionaries for hundreds or thousands of rows would bloat the SQLite database.
2. **Simple Ingestion Path:** Reduces write times and query latency on local machines.
3. **Sufficient Provenance:** Storing the metadata (filename, size, etc.) in `RawIngestionLog` and linking all parsed `EmissionRecord` objects to it preserves file-level auditability. Detailed parsing issues are logged directly in the `AuditLog`.

### What We Do Instead

- Create a single `RawIngestionLog` per file upload event.
- Store file-level metadata (`filename`, `file_size`, etc.) in the log's `raw_payload`.
- Link all successfully parsed and flagged `EmissionRecord` objects back to this log.
- Record any row-specific parser issues in the initial `AuditLog` creation entry.

### Cost of Not Having It

- **Manual File Lookup:** Auditors looking to verify the exact raw text of a specific record must reference the original source file by matching the metadata in the `RawIngestionLog`, rather than fetching it from a database cell.

### When to Build It

- When migrating to a production database (e.g., PostgreSQL) where JSON column indexing and storage partitioning can handle heavy row-level tracking, and when users demand a side-by-side view of the raw row vs. parsed model in the dashboard.

---
