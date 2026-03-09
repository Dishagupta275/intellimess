-- ================================================================
--  IntelliMess — FINAL MIGRATIONS (run on CleverCloud DB)
--  Connect: mysql -h boepijlcqxhibaudjeck-mysql.services.clever-cloud.com
--           -u ublerrfhpva5tzcq -p boepijlcqxhibaudjeck
-- ================================================================

USE boepijlcqxhibaudjeck;

-- 1. Attendance tracking
ALTER TABLE bookings
    ADD COLUMN IF NOT EXISTS attended TINYINT(1) DEFAULT NULL;

-- 2. Profile: email + notification preference
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email          VARCHAR(120) NULL DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS remind_booking TINYINT(1)   NOT NULL DEFAULT 1;

-- 3. Reminder log (prevents duplicate emails per meal per day)
CREATE TABLE IF NOT EXISTS reminder_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT         NOT NULL,
    meal          VARCHAR(20) NOT NULL,
    reminder_date DATE        NOT NULL,
    sent_at       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_reminder (user_id, meal, reminder_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ================================================================
-- Done! All 3 statements are safe to re-run (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).
-- ================================================================
