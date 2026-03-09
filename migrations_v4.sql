-- ================================================================
--  IntelliMess — Migration v4 (New Features)
--  Run on your existing `intellimess` / CleverCloud database
-- ================================================================

-- -----------------------------------------------
-- 1. ATTENDANCE: Add attended column to bookings
-- -----------------------------------------------
ALTER TABLE bookings
    ADD COLUMN attended TINYINT(1) DEFAULT NULL;
-- NULL = not marked yet, 1 = attended, 0 = absent

-- ================================================================
-- Done! No other schema changes needed.
--
-- Summary of all new features and what changed:
-- ─────────────────────────────────────────────
-- ✅ Cancel Booking     → New routes /my-bookings + /cancel-booking/<id>
--                          New template: my_bookings.html
--                          (no DB change needed — just DELETE from bookings)
--
-- ✅ Meal Calendar      → New route /calendar
--                          New template: calendar.html
--                          (reads existing weekly_menu + polls tables)
--
-- ✅ Low-Rated Alerts   → New route /admin/alerts
--                          New template: admin_alerts.html
--                          (reads existing feedback table)
--
-- ✅ Attendance %       → New routes /admin/attendance + /admin/attendance/mark
--                          New template: admin_attendance.html
--                          Requires: bookings.attended column (added above ↑)
--
-- ✅ Export CSV         → New route /admin/export/csv
--                          (no template — streams CSV file download)
--
-- ✅ Input Validation   → Updated /register route in app.py
--                          Updated register.html with error display + hints
--
-- ================================================================
