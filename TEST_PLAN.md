# Testing Plan - Breadth ESG Dashboard

## Phase 3: Frontend + Backend Integration Testing

### Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5173` (Vite dev server)
- Database seeded with sample data (optional, can upload files during testing)
- Browser: Chrome, Firefox, Safari, or Edge (latest version)

---

## Unit Testing Checklist

### 1. File Upload Component ✅
**Objective:** Verify file upload functionality with all source types

- [ ] **Test 1.1:** Drag-and-drop CSV file
  - Drop a SAP CSV file onto the drop zone
  - Expected: File name appears, upload spinner shows, success notification

- [ ] **Test 1.2:** Browse and select file manually
  - Click "Browse Files" button
  - Select a utility CSV file
  - Expected: File upload completes successfully

- [ ] **Test 1.3:** Source type selection
  - Select each source type (SAP, UTILITY, TRAVEL)
  - Upload appropriate file for each
  - Expected: Correct parser processes each file type

- [ ] **Test 1.4:** Invalid file rejection
  - Try uploading unsupported file type (e.g., .txt)
  - Expected: Error notification shows, upload blocked

- [ ] **Test 1.5:** File size validation
  - Try uploading file > 10MB
  - Expected: Error message about file size limit

---

### 2. Dashboard Component ✅
**Objective:** Verify summary statistics display

- [ ] **Test 2.1:** Dashboard loads with correct stats
  - After uploading a file, dashboard updates
  - Expected: Total records, by-status counts match uploaded records

- [ ] **Test 2.2:** Stats update after new upload
  - Upload second file
  - Expected: Dashboard totals increase correctly

- [ ] **Test 2.3:** Scope breakdown displays
  - Check Scope 1/2/3 bars
  - Expected: Bars show correct distribution

- [ ] **Test 2.4:** Empty dashboard state
  - Clear database or start fresh
  - Expected: Dashboard shows 0 records, clear messaging

---

### 3. Records Table Component ✅
**Objective:** Verify table display, filtering, sorting

- [ ] **Test 3.1:** Table displays all uploaded records
  - Upload file with 10+ records
  - Expected: All records visible in table with correct data

- [ ] **Test 3.2:** Filter by Status
  - Select "FLAGGED" status filter
  - Expected: Table shows only flagged records

- [ ] **Test 3.3:** Filter by Scope
  - Select "Scope 2 (Electricity)"
  - Expected: Table shows only Scope 2 records

- [ ] **Test 3.4:** Filter by Category
  - Select "Fuel" category
  - Expected: Table shows only Fuel records

- [ ] **Test 3.5:** Sort by newest first
  - Upload multiple files
  - Sort by "Newest First"
  - Expected: Records ordered by ID descending

- [ ] **Test 3.6:** Sort by status
  - Use "By Status" sort
  - Expected: Records grouped by status

- [ ] **Test 3.7:** Combined filters
  - Apply Status + Scope + Category filters
  - Expected: Table shows intersection of all filters

---

### 4. Edit Record Modal ✅
**Objective:** Verify record editing and status transitions

- [ ] **Test 4.1:** Open edit modal for FLAGGED record
  - Click "Fix" button on flagged record
  - Expected: Modal opens showing record details

- [ ] **Test 4.2:** Edit emissions value
  - Change normalized_value to different number
  - Click "Save Changes"
  - Expected: Record updates, notification shows success

- [ ] **Test 4.3:** Approve a PENDING record
  - Find PENDING record
  - Click "Review" button
  - Change status to "APPROVED"
  - Save
  - Expected: Record locked, status updated

- [ ] **Test 4.4:** Cannot edit APPROVED record
  - Attempt to open edit modal for APPROVED record
  - Expected: Only "History" button available, no edit option

- [ ] **Test 4.5:** Add notes to record
  - Open edit modal
  - Add notes in Notes field
  - Save
  - Expected: Notes saved with record

- [ ] **Test 4.6:** Cancel edit without saving
  - Open edit modal
  - Change values
  - Click "Cancel"
  - Expected: Modal closes, original values unchanged

---

### 5. Audit Trail Component ✅
**Objective:** Verify audit log viewing

- [ ] **Test 5.1:** Open audit trail for record
  - Click "History" button on any record
  - Expected: Modal shows timeline of changes

- [ ] **Test 5.2:** View creation entry
  - Check first audit log entry
  - Expected: "Created" action with timestamp and system user

- [ ] **Test 5.3:** View update entry
  - Edit record and save
  - Open audit trail again
  - Expected: New "Updated" entry with timestamp

- [ ] **Test 5.4:** View state changes
  - Click "View Changes" on an update entry
  - Expected: Previous and new state JSON displayed

- [ ] **Test 5.5:** Multiple edits tracked
  - Edit same record 3 times
  - Open audit trail
  - Expected: All 3 edits shown in timeline

---

### 6. Notifications ✅
**Objective:** Verify user feedback messages

- [ ] **Test 6.1:** Success notification on upload
  - Upload file
  - Expected: Green success notification shows, auto-dismisses after 4s

- [ ] **Test 6.2:** Success notification on save
  - Edit and save record
  - Expected: Green notification "Record updated successfully!"

- [ ] **Test 6.3:** Error notification on failed upload
  - Upload invalid file
  - Expected: Red error notification with details

- [ ] **Test 6.4:** Error notification dismissal
  - Let notification auto-dismiss
  - Click X to dismiss
  - Expected: Notification disappears

---

## Integration Testing Checklist

### 7. API Integration ✅
**Objective:** Verify correct API endpoints and payloads

- [ ] **Test 7.1:** Upload endpoint uses correct path
  - Monitor network tab during upload
  - Expected: POST to `/api/emissions/upload/`

- [ ] **Test 7.2:** GET records endpoint
  - Table loads records
  - Expected: GET to `/api/emissions/` returns paginated results

- [ ] **Test 7.3:** Dashboard summary endpoint
  - Dashboard loads stats
  - Expected: GET to `/api/emissions/summary/` returns stats

- [ ] **Test 7.4:** PATCH record endpoint
  - Edit and save record
  - Expected: PATCH to `/api/emissions/{id}/` with updated fields

- [ ] **Test 7.5:** Audit history endpoint
  - Open audit trail
  - Expected: GET to `/api/emissions/{id}/audit_history/` returns logs

---

### 8. Data Consistency ✅
**Objective:** Verify data consistency between frontend and backend

- [ ] **Test 8.1:** Upload reflects in table
  - Upload 5-record file
  - Check table count matches
  - Expected: 5 new records in table

- [ ] **Test 8.2:** Edit persists to backend
  - Edit record value to 123.45
  - Refresh page
  - Expected: Record still shows 123.45

- [ ] **Test 8.3:** Status change locks record
  - Approve record (set APPROVED)
  - Try to edit again
  - Expected: Edit button unavailable

- [ ] **Test 8.4:** Multi-user consistency
  - Open same record in 2 browser windows
  - Edit in window 1, save
  - Refresh window 2
  - Expected: Updated data shows in window 2

---

### 9. Performance Testing ✅
**Objective:** Verify dashboard performance with moderate data

- [ ] **Test 9.1:** Table loads 100 records
  - Upload/create 100 records
  - Expected: Table loads in < 2 seconds

- [ ] **Test 9.2:** Filtering is responsive
  - Apply filters with 100+ records
  - Expected: Filter updates < 200ms

- [ ] **Test 9.3:** Sorting is fast
  - Sort 100 records by different fields
  - Expected: Sort < 500ms

---

## UI/UX Testing Checklist (Non-Technical Users)

### 10. Usability ✅
**Objective:** Verify dashboard is intuitive for analysts without technical background

- [ ] **Test 10.1:** First-time user flow
  - New user navigates to dashboard
  - Finds and uploads file without help
  - Expected: Intuitive icons, clear labels guide user

- [ ] **Test 10.2:** Record status obvious
  - Check color coding for statuses
  - Expected: Green = Approved, Orange = Flagged, Gray = Pending clear

- [ ] **Test 10.3:** Filter labels clear
  - User understands what each filter does
  - Expected: Dropdown labels and options are self-explanatory

- [ ] **Test 10.4:** Error messages helpful
  - Trigger error (e.g., invalid upload)
  - Expected: Message explains what went wrong and next steps

- [ ] **Test 10.5:** Action buttons obvious
  - User knows which buttons to click to edit/review/view history
  - Expected: Button labels and icons are clear

---

### 11. Responsiveness ✅
**Objective:** Verify dashboard works on different screen sizes

- [ ] **Test 11.1:** Mobile view (375px)
  - Open dashboard on mobile device or resize browser
  - Expected: All elements readable, no horizontal scroll

- [ ] **Test 11.2:** Tablet view (768px)
  - Expected: Table columns adapt, buttons stack appropriately

- [ ] **Test 11.3:** Desktop view (1200px+)
  - Expected: Full table visible with all columns

- [ ] **Test 11.4:** Touch interactions
  - On mobile/tablet, test touch-friendly buttons
  - Expected: Buttons are large enough, no accidental clicks

---

### 12. Accessibility ✅
**Objective:** Verify dashboard accessible to users with disabilities

- [ ] **Test 12.1:** Keyboard navigation
  - Navigate table with Tab key
  - Open modals, interact with forms
  - Expected: All interactive elements accessible

- [ ] **Test 12.2:** Color not only indicator
  - Status clearly shown with text, not just color
  - Expected: Status badge shows text (APPROVED, FLAGGED, etc.)

- [ ] **Test 12.3:** Form labels associated
  - Form inputs have associated labels
  - Screen reader announces labels
  - Expected: Semantic HTML for accessibility

---

## Browser Compatibility Testing

### 13. Cross-Browser ✅
- [ ] Chrome (latest) - Full testing
- [ ] Firefox (latest) - Critical features
- [ ] Safari (latest) - Critical features
- [ ] Edge (latest) - Critical features

---

## Test Execution Log

### Test Session 1: [Date]
- **Tester:** [Name]
- **Browser:** [Chrome 123 / Firefox 122 / Safari 17 / etc.]
- **Duration:** [Start - End time]
- **Status:** ✅ PASS / ❌ FAIL
- **Issues Found:**
  1. [Brief description of any bugs]
  2. [Brief description of any UX concerns]
  3. [Brief description of any performance issues]

### Test Session 2: [Date]
- **Tester:** [Name]
- **Status:** ✅ PASS / ❌ FAIL
- **Issues:** [Any remaining issues]

---

## Known Issues & Workarounds

### Before Testing Begins
- [ ] Ensure backend is running (`python manage.py runserver`)
- [ ] Ensure frontend dev server is running (`npm run dev`)
- [ ] Ensure sample data is available or ready to upload
- [ ] Clear browser cache if testing UI changes
- [ ] Check network tab in DevTools for API calls

### Debugging Tips
- Monitor network tab for failed API calls
- Check browser console for JavaScript errors
- Verify backend logs for 500 errors
- Test with mock data if API issues arise

---

## Test Results Summary

**Total Tests:** 50+
**Passed:** ___/50
**Failed:** ___/50
**Critical Issues:** ___
**Non-Critical Issues:** ___

**Overall Status:** [ ] Ready for Deployment / [ ] Needs Fixes

---

## Sign-Off

- **Testing Lead:** _________________ Date: _______
- **Developer:** _________________ Date: _______
- **Product Owner:** _________________ Date: _______

---

## Phase 4: Deployment Readiness

After all Phase 3 tests pass:
1. [ ] Lint all frontend code
2. [ ] Build for production (`npm run build`)
3. [ ] Verify Docker build
4. [ ] Test in Docker container
5. [ ] Deploy to staging environment
6. [ ] Smoke test in staging
7. [ ] Deploy to production
