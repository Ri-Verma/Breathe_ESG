# Frontend Setup & Integration Guide

## Quick Start: Run Frontend + Backend Together

### Prerequisites
- Node.js 18+ and npm installed
- Python 3.11+ and Django 4.2+ running
- Backend server on `http://localhost:8000`

---

## Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

**Expected output:**
```
added XXX packages in Xs
```

**Packages installed:**
- react@18
- react-dom@18
- axios (for API calls)
- vite (dev server)

---

## Step 2: Configure API Proxy (Vite)

The frontend needs to communicate with the Django backend. Vite's dev server includes a proxy.

**File:** `frontend/vite.config.js`

Should already be configured. If not, ensure it has:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
```

This routes all `/api/*` requests to the Django backend.

---

## Step 3: Start Frontend Dev Server

```bash
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

Frontend is now accessible at `http://localhost:5173`

---

## Step 4: Verify Backend is Running

In a separate terminal:

```bash
cd backend
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Starting development server at http://127.0.0.1:8000/
```

Backend is now accessible at `http://localhost:8000`

---

## Step 5: Test Integration

### In your browser, open: `http://localhost:5173`

You should see:
1. ✅ Header: "🌍 Breadth ESG Dashboard"
2. ✅ File upload section with drag-drop zone
3. ✅ Dashboard with summary cards (may be empty initially)
4. ✅ Records table (empty initially)

### Upload Test File

1. Download one of these sample files:
   - SAP data: `data_samples/sap_export.csv`
   - Utility data: `data_samples/utility_bill.csv`
   - Travel data: `data_samples/travel_api_response.json`

2. Drag file onto the drop zone (or click "Browse Files")

3. Select appropriate source type (SAP/UTILITY/TRAVEL)

4. Click "Browse Files" or drop the file

5. Watch the upload spinner

6. After ~2-3 seconds, you should see:
   - ✅ Green success notification: "Successfully uploaded..."
   - ✅ Dashboard stats update
   - ✅ Records appear in the table

---

## Debugging: Monitor Network & Console

### Browser DevTools (F12)

**Network Tab:**
1. Open DevTools → Network tab
2. Perform an action (upload file, filter records, etc.)
3. Look for these API calls:

```
POST /api/emissions/upload/        ← File upload
GET /api/emissions/                ← Fetch records
GET /api/emissions/summary/        ← Dashboard stats
PATCH /api/emissions/123/          ← Record update
GET /api/emissions/123/audit_history/  ← Audit trail
```

**Expected Status Codes:**
- ✅ 200 OK — Successful GET
- ✅ 201 Created — Successful POST
- ✅ 204 No Content — Successful PATCH
- ❌ 400 Bad Request — Invalid data
- ❌ 404 Not Found — Endpoint doesn't exist
- ❌ 500 Server Error — Backend error

**Console Tab:**
- Check for JavaScript errors (red messages)
- Check for CORS errors (usually blue warnings)

---

## Common Issues & Fixes

### Issue 1: "Cannot POST /api/emissions/upload/"

**Problem:** Frontend can't reach backend API

**Solution:**
```bash
# Check backend is running
cd backend
python manage.py runserver

# Check Vite proxy config in vite.config.js
# Verify localhost:8000 is accessible
curl http://localhost:8000/api/emissions/
```

**Expected Response:**
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

---

### Issue 2: CORS Error in Console

**Problem:** "Access to XMLHttpRequest blocked by CORS policy"

**Solution:**
Backend needs CORS headers. In `backend/core/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this first
    'django.middleware.common.CommonMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://127.0.0.1:5173',
]
```

Then restart Django:
```bash
python manage.py runserver
```

---

### Issue 3: File Upload Returns 415 (Unsupported Media Type)

**Problem:** Backend doesn't recognize file format

**Solution:**
- Ensure you selected the correct source type (SAP → CSV, TRAVEL → JSON, etc.)
- Check file format matches backend parser expectations
- Verify file headers (SAP should have German headers, etc.)

---

### Issue 4: Dashboard Shows 0 Records After Upload

**Problem:** Records uploaded but don't appear in table

**Likely Causes:**
1. API not returning records
2. Frontend not refetching after upload
3. Filters hiding records

**Debug Steps:**
1. Check browser Network tab: GET /api/emissions/ should return records
2. Check backend logs for parsing errors
3. In browser console, type: `fetch('/api/emissions/').then(r => r.json()).then(console.log)`
4. Remove filters to show all records

---

### Issue 5: Modal Doesn't Close

**Problem:** After saving record, edit/audit modal stays open

**Solution:**
- Hard refresh browser: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- Clear browser cache
- Check console for JavaScript errors

---

### Issue 6: Notification Doesn't Show

**Problem:** No success/error message after action

**Solution:**
- Check console for errors
- Verify API call succeeded (Network tab should show 200/201)
- In console: `document.querySelector('.notification')` should exist

---

## File Structure Reference

```
frontend/
├── src/
│   ├── App.jsx                    ← Main component with state
│   ├── App.css                    ← App-specific styles
│   ├── index.css                  ← Global styles (700+ lines)
│   ├── main.jsx                   ← React entry point
│   ├── components/
│   │   ├── FileUpload.jsx         ← Upload interface
│   │   ├── Dashboard.jsx          ← Summary cards
│   │   ├── MetricsDisplay.jsx     ← Records table (RecordsTable)
│   │   ├── EditRecord.jsx         ← Edit modal
│   │   └── AuditTrail.jsx         ← Audit log viewer
│   └── index.html                 ← HTML template
├── package.json                   ← Dependencies
├── vite.config.js                 ← Vite configuration (includes proxy)
└── .gitignore
```

---

## API Endpoints Reference

### 1. Upload File
```
POST /api/emissions/upload/
Content-Type: multipart/form-data

Body:
- file: <binary file data>
- source_type: "SAP" | "UTILITY" | "TRAVEL"

Response (201):
{
  "status": "success",
  "filename": "sap_export.csv",
  "source_type": "SAP",
  "raw_log_id": 1,
  "statistics": {
    "total_rows": 10,
    "successful": 8,
    "flagged": 2
  },
  "records_created": 8
}
```

### 2. Get All Records
```
GET /api/emissions/?status=FLAGGED&scope=1&category=Fuel

Response (200):
{
  "count": 50,
  "next": "http://localhost:8000/api/emissions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tenant_id": 1,
      "scope": "1",
      "category": "Fuel",
      "original_value": 100,
      "original_unit": "GAL",
      "normalized_value": 378.541,
      "normalized_unit": "L",
      "status": "FLAGGED",
      "is_locked": false,
      "notes": "",
      "created_at": "2024-05-27T10:00:00Z"
    }
  ]
}
```

### 3. Get Dashboard Summary
```
GET /api/emissions/summary/

Response (200):
{
  "total_records": 50,
  "by_status": {
    "PENDING": 15,
    "FLAGGED": 10,
    "APPROVED": 25
  },
  "by_scope": {
    "1": 20,
    "2": 15,
    "3": 15
  },
  "by_category": {
    "Fuel": 20,
    "Electricity": 15,
    "Travel": 15
  }
}
```

### 4. Update Record
```
PATCH /api/emissions/1/
Content-Type: application/json

Body:
{
  "normalized_value": 500.0,
  "status": "APPROVED",
  "notes": "Verified against supplier invoice"
}

Response (200):
{
  "id": 1,
  "status": "APPROVED",
  "normalized_value": 500.0,
  "is_locked": true,
  "notes": "Verified against supplier invoice",
  "updated_at": "2024-05-27T11:00:00Z"
}
```

### 5. Get Audit Trail
```
GET /api/emissions/1/audit_history/

Response (200):
{
  "results": [
    {
      "id": 1,
      "action": "CREATE",
      "timestamp": "2024-05-27T10:00:00Z",
      "user_name": "System",
      "previous_state": null,
      "new_state": {
        "scope": "1",
        "original_value": 100,
        "status": "PENDING"
      }
    },
    {
      "id": 2,
      "action": "UPDATE",
      "timestamp": "2024-05-27T11:00:00Z",
      "user_name": "analyst@company.com",
      "previous_state": {
        "status": "PENDING",
        "normalized_value": 378.541
      },
      "new_state": {
        "status": "APPROVED",
        "normalized_value": 500.0
      }
    }
  ]
}
```

---

## Performance Tips

### For Large Datasets (100+ records)

1. **Use filtering:** Always filter by status/scope to reduce table size
2. **Implement pagination:** Backend supports `?page=2` parameter
3. **Enable table virtualization:** For extremely large tables (optional Phase 2 improvement)

### Optimize Build

```bash
npm run build
```

Produces optimized bundle in `frontend/dist/`

---

## Useful Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Lint code (if ESLint configured)
npm run lint

# Run tests (if Jest configured)
npm test
```

---

## Testing Checklist (Before Each Deploy)

- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:5173
- [ ] Can upload SAP CSV
- [ ] Can upload Utility CSV
- [ ] Can upload Travel JSON
- [ ] Can filter records by status
- [ ] Can edit flagged record
- [ ] Can approve pending record
- [ ] Can view audit trail
- [ ] Notifications appear correctly
- [ ] No console errors
- [ ] No CORS errors

---

## Support

**If frontend doesn't work:**

1. Clear browser cache: `Ctrl+Shift+Delete`
2. Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. Stop dev server: `Ctrl+C`
4. Restart: `npm run dev`
5. Check browser console for errors: `F12` → Console tab
6. Check Network tab for failed API calls

**If API calls fail:**

1. Verify backend is running: `python manage.py runserver`
2. Test API directly: `curl http://localhost:8000/api/emissions/`
3. Check Django logs in terminal for errors
4. Verify CORS configuration in `settings.py`
