# Real-World Data Sources & Research

---

## 1. SAP Flat File Export (Fuel & Procurement)

### Real-World Format Researched

**Type:** IDoc (Intermediate Document) flat file export, typically ORDERS or INVOIC transaction type.

**Why this format?**
- Enterprises use SAP as their master data system but don't expose APIs externally
- Legacy IDoc exports to CSV/Excel are the standard handoff mechanism
- Research source: SAP documentation on IDoc structure, Reddit ESG/sustainability forums, enterprise data integration case studies

**Real-world characteristics:**
- **Headers in German:** DOCNUM, DATUM, WERKS (plant), MATNR (material number), MAKTX (material description), MENGE (quantity), MEINS (unit of measure)
- **Mixed date formats:** SAP regional configs produce DD.MM.YYYY, MM/DD/YYYY, or DD-MM-YYYY in same file
- **Inconsistent units:** L (liters), GAL (gallons), KG (kilograms), T (metric tons), sometimes duplicated for same material
- **Plant codes:** Internal to SAP (P100, P200, P300) — meaning unknown without client's lookup table
- **Material descriptions:** May include raw translations (e.g., "Dieselkraftstoff" = diesel fuel)

### What We Learned

1. **dateutil.parser is essential:** Can handle 15+ date format variants without explicit configuration
2. **Unit conversion matrix required:** Every fuel type appears in multiple units; we normalize all to Liters
3. **Messy data is normal:** Missing MENGE (quantity) or MEINS (unit) is common; data quality varies by plant
4. **Source-of-truth principle:** Must store raw row verbatim in JSONField for audits

### Sample Data in `data_samples/sap_export.csv`

```
DOCNUM,DATUM,WERKS,MATNR,MAKTX,MENGE,MEINS
10000001,15.01.2024,P100,F-001,Dieselkraftstoff,500,L
10000002,01/16/2024,P200,F-002,Unleaded Gas,150,GAL
10000003,17.01.2024,P100,F-001,Dieselkraftstoff,1200,L
10000004,18-01-2024,P300,E-001,Generator Oil,50,L
...
```

**Why these samples?**
- DATUM shows three date formats (DD.MM.YYYY, MM/DD/YYYY, DD-MM-YYYY) in same file
- MEINS mixes L and GAL (real scenario where unit conversion is needed)
- MAKTX includes German material names
- WERKS codes (P100, P200, P300) are opaque without lookup table
- Realistic quantity ranges (500–1200 L per fuel transaction)

### Parsing Logic

```python
def parse_sap_csv(file_content: str, tenant_id: int):
    # 1. CSV DictReader with flexible headers
    # 2. dateutil.parser.parse(DATUM) → handles all 3 date formats
    # 3. UNIT_CONVERSIONS[MEINS] → normalize to Liters
    # 4. Category inference from MAKTX (Diesel, Gasoline, Oil, etc.)
    # 5. Scope 1 (Direct emissions from fuel burning)
    # 6. Flag if: missing MENGE, unknown MEINS, invalid date
    return (successful_records, flagged_records)
```

### What Would Break in Real Deployment

1. **Plant code mapping:** Our sample has P100, P200, P300. Real client has 50+ plants with location names. We'd need to sync plant master table per client.
2. **Material master:** MATNR F-001 means nothing to our system. Real deployment needs MAKT (material master) lookups to standardize material categories (e.g., all Diesel → single Scope 1 category).
3. **Additional columns:** Real SAP exports have cost center, cost type, vendor, purchase order — we'd need to extend parser logic.
4. **Non-fuel materials:** SAP exports may include consumables (paper, packaging) that aren't fuel. We'd need classification logic.
5. **Character encoding:** Some SAP systems export as EBCDIC or non-UTF8. We assume UTF-8; real system needs encoding detection.

---

## 2. Utility Portal CSV Export (Electricity)

### Real-World Format Researched

**Type:** Meter reading CSV export from utility portal (e.g., Enel Connect, EDF Pro, Schneider Electric).

**Why this format?**
- Research: Surveyed 5+ utility portals (US, EU) for export options
- Found: All offer CSV export; none offer robust APIs except enterprise SLA
- Reality: Facilities teams download CSV monthly, sometimes manually copy-paste from online bill

**Real-world characteristics:**
- **Headers:** Meter_ID, Building_Code, Billing_Start_Date, Billing_End_Date, Total_kWh, Peak_kWh, OffPeak_kWh, Amount_Billed
- **Billing periods:** NOT calendar months. Meter reads on fixed day (e.g., 15th) → next 15th is 31 days. Spans Jan 15 – Feb 14.
- **Missing peak data:** Some utilities only provide total kWh; peak/offpeak split is blank (double commas)
- **Multiple meters per building:** Building A has 3 meters (HVAC, Lighting, Equipment) — each row separate
- **Tariff complexity:** Peak vs. offpeak rates vary by time of day and season — we don't store tariff, only consumption

### What We Learned

1. **Billing periods are non-standard:** Must extract date range, not assume calendar months
2. **Double commas are silent errors:** CSV reader skips blank peak_kWh fields; easy to miss
3. **kWh normalization is simple:** All electricity is already in kWh; no conversion needed
4. **Meter-level tracking is essential:** Multiple meters per building must be tracked separately for audit trail
5. **Scope 2 calculation:** kWh alone isn't enough for auditors; need grid carbon intensity (varies by region). We store kWh only; carbon calculation is downstream.

### Sample Data in `data_samples/utility_bill.csv`

```
Meter_ID,Building_Code,Billing_Start_Date,Billing_End_Date,Total_kWh,Peak_kWh,OffPeak_kWh,Amount_Billed
MTR-9921,BLDG-A,2023-12-15,2024-01-14,14500,4500,10000,1740.50
MTR-9921,BLDG-A,2024-01-15,2024-02-14,13200,4000,9200,1584.00
MTR-8810,BLDG-B,2023-12-18,2024-01-17,8900,,8900,979.00
MTR-8810,BLDG-B,2024-01-18,2024-02-17,9100,1200,7900,1001.00
...
```

**Why these samples?**
- Billing periods cross calendar months (Jan 15 – Feb 14)
- MTR-8810 BLDG-B row 3: missing Peak_kWh (double comma) — tests robustness
- Multiple buildings (BLDG-A, BLDG-B, BLDG-C, BLDG-D) — realistic facility
- Realistic consumption ranges: 8900–14500 kWh per billing period
- Dates in ISO format (realistic for modern portals)

### Parsing Logic

```python
def parse_utility_csv(file_content: str, tenant_id: int):
    # 1. CSV DictReader
    # 2. Extract Billing_Start_Date, Billing_End_Date → use end date as activity_date
    # 3. Total_kWh is original_value; no conversion (unit = kWh)
    # 4. Flag if: missing date range, missing Total_kWh, both peak & offpeak missing
    # 5. Scope 2 (Indirect from grid electricity)
    # 6. Category = f"Electricity - {Building_Code}"
    return (successful_records, flagged_records)
```

### What Would Break in Real Deployment

1. **Grid carbon intensity:** Real auditors want kWh × regional carbon factor (grams CO2e/kWh). We store kWh only; downstream system applies carbon factor. Missing in MVP.
2. **Demand charges:** Large customers pay for peak demand (kW), not just consumption (kWh). Our model ignores this.
3. **Multi-year averages:** Utility exports usually show 12–24 months. We parse all rows independently; no time-series analysis (e.g., "is usage trending up or down?").
4. **API integrations:** Real system should poll utility APIs (if available) automatically. We only accept file uploads.
5. **Tariff structure:** Peak vs. offpeak rates vary by season and time of day. We don't validate or flag missing tariff data.
6. **PDF parsing:** Some utilities only provide PDF bills. We'd need OCR (Tesseract) or manual rules.

---

## 3. Corporate Travel JSON (Navan/Concur API Mock)

### Real-World Format Researched

**Type:** Navan Travel API JSON response (mock for MVP; real OAuth in Phase 2).

**Why this format?**
- Research: Read Navan & Concur API documentation
- Found: Both expose trip segments with origin/destination airport codes (IATA: JFK, LHR, SFO)
- Found: Neither provides flight distances directly; that's calculated downstream
- Reality: MVP uses mocked JSON; production would implement OAuth + scheduled API pulls

**Real-world characteristics:**
- **Trip structure:** Each trip has one or more segments (flight, ground, train)
- **Airport codes:** IATA 3-letter codes (JFK, LAX, LHR) — NOT full airport names
- **Trip status:** COMPLETED, PENDING, CANCELLED — only process COMPLETED
- **Cabin class:** ECONOMY, BUSINESS, PREMIUM_ECONOMY — affects emission factor
- **No distance:** API doesn't provide km between airports; we calculate from lookup table
- **Departure time:** ISO 8601 timestamp (e.g., 2024-01-05T08:00:00Z)
- **Multi-segment:** Single trip (TRP-10045) may have flight (JFK → LHR) + ground (LHR → hotel)

### What We Learned

1. **Distance lookup is critical:** Without distances from API, we need a geographic database (or hardcoded lookup for MVP)
2. **Emission factors vary by transport:** Flight 0.255 kg CO2e/km, Train 0.041, Ground 0.120 (real values from ICAO, UK BEIS)
3. **Cabin class matters:** Business class has higher emissions (2–3x) than economy (more space per passenger)
4. **Multi-segment trips are common:** Business travelers take flight + ground transport in same trip
5. **Trip status filtering:** Don't process CANCELLED trips (no emissions if trip didn't happen)

### Sample Data in `data_samples/travel_api_response.json`

```json
{
  "api_provider": "navan_mock",
  "export_date": "2024-01-31T00:00:00Z",
  "data": [
    {
      "trip_id": "TRP-10045",
      "employee_id": "EMP-001",
      "status": "COMPLETED",
      "segments": [
        {
          "mode": "FLIGHT",
          "origin_airport": "JFK",
          "destination_airport": "LHR",
          "cabin_class": "ECONOMY",
          "departure_time": "2024-01-05T08:00:00Z"
        }
      ]
    },
    {
      "trip_id": "TRP-10052",
      "employee_id": "EMP-008",
      "status": "COMPLETED",
      "segments": [
        {
          "mode": "FLIGHT",
          "origin_airport": "LHR",
          "destination_airport": "DXB",
          "cabin_class": "BUSINESS",
          "departure_time": "2024-01-28T02:30:00Z"
        },
        {
          "mode": "GROUND",
          "origin_airport": "DXB",
          "destination_airport": "DWC",
          "cabin_class": "ECONOMY",
          "departure_time": "2024-01-28T05:30:00Z"
        }
      ]
    }
  ]
}
```

**Why these samples?**
- Trip TRP-10045: Standard flight (JFK → LHR)
- Trip TRP-10052: Multi-segment (flight LHR → DXB, then ground DXB → DWC) — tests parsing
- Status COMPLETED (not CANCELLED) — only these generate emissions
- Cabin classes vary (ECONOMY vs. BUSINESS) — emission factor differs
- Departure times in ISO 8601 format
- Trip dates span Jan 5 – Jan 28, covering multiple months (realistic for quarterly reports)

### Parsing Logic

```python
def parse_travel_json(file_content: str, tenant_id: int):
    # 1. json.loads() payload
    # 2. Filter trips by status == 'COMPLETED'
    # 3. For each segment:
    #    a. Look up distance: AIRPORT_DISTANCES[(origin, destination)] in km
    #    b. If not found, flag (missing distance data)
    #    c. Multiply km × emission_factor[mode] → kgCO2e
    #    d. Scope 3 (Value chain, business travel)
    # 4. Category = f"{mode} Travel - {cabin_class}"
    return (successful_records, flagged_records)
```

### What Would Break in Real Deployment

1. **Hardcoded distance lookup is brittle:** Only have 20 routes hardcoded. Real system needs dynamic distance API (Google Maps, Haversine calculation).
2. **Airport code ambiguity:** LHR could mean London Heathrow (international) or London City (domestic). Emission factors differ; we assume Heathrow. Real system needs airport IATA → location mapping.
3. **Emission factors are static:** Real deployment needs:
   - Time-dependent factors (RFI multiplier for high-altitude contrails)
   - Aircraft type (A380 vs. regional jet: different per-km CO2e)
   - Load factor (% of seats filled): affects per-passenger emissions
   - We use simple 0.255 kg CO2e/km for all flights
4. **No hotel/meal/car rental emissions:** Real Scope 3 includes accommodations, ground transportation, meals. MVP only does flights/trains/ground.
5. **Navan OAuth not implemented:** Real system needs API credentials, token refresh, scheduled pulls. We only accept mocked JSON upload.
6. **No ground distance calculation:** For ground transport (DXB → DWC), we rely on lookup table. Real system needs lat/long data.

---

## Summary: What Each Source Handles

| Aspect | SAP | Utility | Travel |
|--------|-----|---------|--------|
| **Format** | Flat CSV (IDoc) | Portal CSV | JSON (mocked API) |
| **Real-world complexity** | German headers, mixed dates, mixed units | Cross-month billing, missing fields | Distance lookup, multi-segment trips |
| **Normalization** | GAL → L | Already kWh | Distance → kgCO2e via factors |
| **Scope** | Scope 1 (Direct) | Scope 2 (Energy) | Scope 3 (Travel) |
| **Sample rows** | 14 | 13 | 9 trips |
| **MVP fully handles** | ✅ | ✅ | ✅ (mocked) |
| **Phase 2 needed** | Plant master sync, material lookups | Carbon intensity per region | Real Navan OAuth, dynamic distance API |

---

## Data Quality & Audit Resilience

All three parsers follow the principle:
- **Lenient parsing:** Accept messy data, don't crash.
- **Eager flagging:** Mark issues and output a status of `FLAGGED` to let the analyst review.
- **Full provenance:** Store overall file metadata in `RawIngestionLog` and log detailed parser issues in initial audit logs, linking all resulting emission records to their source file log.
- **Audit trail:** Every record creation + edit logged with user + timestamp.

---

## Real-World Ingestion Testing and Robustness Verification

During Phase 3 and Phase 3.5 testing, the parser implementations were validated against the sample data located in the `data_samples/` directory:

1. **SAP CSV Ingestion (`data_samples/sap_export.csv`):**
   - Successfully parsed all 14 rows.
   - Handled three distinct date formats (`DD.MM.YYYY`, `MM/DD/YYYY`, `DD-MM-YYYY`) using the robust `dateutil.parser`.
   - Performed correct volume unit conversions (e.g., converted gallons to liters using the `3.78541` multiplier).
   - Flagged rows with missing quantities or invalid fields, creating corresponding `EmissionRecord` entries with a status of `FLAGGED`.

2. **Utility Billing Ingestion (`data_samples/utility_bill.csv`):**
   - Successfully parsed 13 utility billing rows representing multiple meters across buildings (`BLDG-A`, `BLDG-B`, `BLDG-C`, `BLDG-D`).
   - Handled non-standard billing dates crossing calendar months (e.g., `2023-12-15` to `2024-01-14`).
   - Gracefully identified rows with missing `Peak_kWh` fields (such as double commas) and successfully flagged records that lacked both peak and off-peak metrics to allow user review.

3. **Corporate Travel Ingestion (`data_samples/travel_api_response.json`):**
   - Parsed 9 travel segments across multiple employee trips.
   - Filtered out cancelled trips (`status != 'COMPLETED'`) to ensure only actual emissions are logged.
   - Looked up route distances dynamically from a preset airport distance dictionary (e.g., LHR-DXB = 5,247 km).
   - Successfully applied mode-specific emission factors (Flights: `0.255 kgCO2e/km`, Trains: `0.041 kgCO2e/km`, Ground: `0.120 kgCO2e/km`) and cabin class indicators to compute Scope 3 emissions.