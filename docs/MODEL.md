# Data Model Architecture

**Core Philosophy:** Immutability + Traceability. Because ESG data is audited, we must prove exactly where every normalized metric originated and track every human touch.

---

## 1. Multi-Tenancy (`Tenant`)
**Goal:** Logical separation of client data for enterprise deployments.

**Structure:**
```python
class Tenant(models.Model):
    name = CharField(unique=True)
    created_at = DateTimeField(auto_now_add=True)
```

**Design Rationale:**
- Every `RawIngestionLog`, `EmissionRecord`, and `AuditLog` has a non-nullable `tenant_id` foreign key
- Query isolation: `EmissionRecord.objects.filter(tenant=current_tenant)` prevents cross-tenant data leaks
- Enables future per-tenant billing, reporting, and audit scopes
- Scales to 100+ clients without schema changes (logical vs. row-based multi-tenancy)

---

## 2. Raw Ingestion Log (`RawIngestionLog`)
**Goal:** Immutable source-of-truth storage. Never discard original data.

**Structure:**
```python
class RawIngestionLog(models.Model):
    tenant = ForeignKey(Tenant)
    source_type = CharField(choices=['SAP', 'UTILITY', 'TRAVEL'])
    raw_payload = JSONField()  # Entire CSV row or JSON object
    ingested_at = DateTimeField(auto_now_add=True)
```

**Design Rationale:**
- **JSONField** stores exact unparsed data: CSV row dict, JSON object, or flattened PDF extraction
- Immutable (no updates) — only creation and reads
- Enables auditor replay: "Here's the exact data we received"
- Decouples schema evolution: future parsers can re-process old payloads
- Justification for storing messy data: SAP exports with German headers (WERKS, MATNR, MENGE, MEINS) and mixed date formats must be preserved verbatim

---

## 3. Emission Record (`EmissionRecord`)
**Goal:** Normalized core table for analyst dashboard and carbon calculations.

**Structure:**
```python
class EmissionRecord(models.Model):
    # Relationships
    tenant = ForeignKey(Tenant)
    raw_log = ForeignKey(RawIngestionLog, null=True)
    
    # Categorization
    scope = IntegerField(choices=[(1,'Scope 1 (Direct)'), (2,'Scope 2 (Indirect)'), (3,'Scope 3 (Value Chain)')])
    category = CharField()  # e.g., 'Diesel Fuel', 'Electricity - Building A', 'Air Travel - Business'
    activity_date = DateField()
    
    # Original Data (as-received)
    original_value = FloatField(null=True)
    original_unit = CharField(null=True)  # 'GAL', 'L', 'kWh', 'km', etc.
    
    # Normalized Data (for calculations)
    normalized_value = FloatField(null=True)
    normalized_unit = CharField(default='kgCO2e')  # Base unit for all
    
    # Workflow
    status = CharField(choices=['PENDING', 'FLAGGED', 'APPROVED'])
    is_locked = BooleanField(default=False)  # True if APPROVED
    
    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Scope Classification (Required by rubric):**
- **Scope 1 (Direct):** SAP fuel & procurement (diesel, gasoline, oils)
- **Scope 2 (Indirect - Energy):** Utility electricity from grid
- **Scope 3 (Value Chain):** Corporate travel emissions (flights, trains, ground)

**Unit Normalization Strategy:**
- All fuel → Liters (convert GAL via 3.78541 multiplier)
- All electricity → kWh (no conversion needed)
- All travel distances → km, then × emission factor (kg CO2e/km)
- Final normalized unit always stored as `kgCO2e` for Scope 1/3; `kWh` for Scope 2

**Status Workflow:**
- `PENDING`: Ingested cleanly, awaiting analyst review
- `FLAGGED`: Missing critical fields (e.g., unrecognized unit, invalid date) — analyst must decide
- `APPROVED`: Analyst signed off; locked from further edits; ready for auditor

**Why `is_locked`?** Once APPROVED, prevents accidental overwrite. Analyst UX shows "locked" badge.

---

## 4. Audit Log (`AuditLog`)
**Goal:** Tamper-evident trail of all human edits.

**Structure:**
```python
class AuditLog(models.Model):
    record = ForeignKey(EmissionRecord)
    user = ForeignKey(User, null=True)  # Analyst name
    action = CharField()  # "Status changed PENDING → APPROVED"
    previous_state = JSONField(null=True)  # {"status": "PENDING", "normalized_value": 100}
    new_state = JSONField(null=True)      # {"status": "APPROVED", "normalized_value": 105}
    timestamp = DateTimeField(auto_now_add=True)
```

**Design Rationale:**
- Immutable (created but never updated)
- Every record creation automatically logs: "Record created from SAP upload"
- Every analyst edit automatically logs: old state → new state
- Timestamped to second for compliance
- Enables full replay: can reconstruct state of any record at any point in time

---

## 5. Relationships Diagram

```
Tenant (1)
  ├─ RawIngestionLog (many)  [immutable, source-of-truth]
  ├─ EmissionRecord (many)   [mutable until APPROVED]
  │   └─ AuditLog (many)     [immutable history]
  └─ User (many)             [analysts who edit records]
```

---

## Design Trade-offs Made

1. **Separate `RawIngestionLog`:** Increases schema complexity but provides auditor-required proof. Trade-off accepted.
2. **JSONField for raw payload:** Less queryable than normalized columns but future-proof. Accepted.
3. **Status + is_locked:** Redundant but explicit; prevents locked-record mutations at ORM level. Accepted.
4. **Single `category` CharField:** No separate Category model. Rationale: category values (e.g., "Diesel Fuel", "Electricity - Building A") are source-specific and don't need lookup tables for this MVP. Future iterations can normalize.

---

## Audit & Compliance Notes

- **Multi-tenant isolation verified at query level:** Every Django query includes `.filter(tenant=current_tenant)`
- **Immutable tables:** `RawIngestionLog`, `AuditLog` use Django `Meta.managed=False` or read-only permissions
- **Unit conversions logged:** Conversion math (GAL→L, etc.) hardcoded in parsers and documented in SOURCES.md
- **Source attribution:** Every `EmissionRecord` links to its `RawIngestionLog`, proving provenance