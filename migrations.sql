-- ============================================================
--  IntelliMess Database Migrations
--  Run these SQL statements on your existing `intellimess` DB
-- ============================================================

USE intellimess;

-- -----------------------------------------------
-- 1. GUEST BOOKING: Add columns to bookings table
-- -----------------------------------------------
ALTER TABLE bookings
    ADD COLUMN guest_count INT NOT NULL DEFAULT 0,
    ADD COLUMN guest_food_type VARCHAR(10) NULL;

-- -----------------------------------------------
-- 2. POLLING SYSTEM: New tables
-- -----------------------------------------------

-- polls: one row per poll
CREATE TABLE IF NOT EXISTS polls (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    question     VARCHAR(255) NOT NULL,
    meal         VARCHAR(20)  NOT NULL,
    poll_date    DATE         NOT NULL,
    closing_time TIME         NOT NULL,
    status       ENUM('open','closed') NOT NULL DEFAULT 'open',
    winner_dish  VARCHAR(150) NULL,        -- auto-filled when poll closes
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- poll_options: dish choices for each poll
CREATE TABLE IF NOT EXISTS poll_options (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    poll_id     INT          NOT NULL,
    option_text VARCHAR(150) NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

-- poll_votes: one vote per student per poll
CREATE TABLE IF NOT EXISTS poll_votes (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    poll_id   INT NOT NULL,
    option_id INT NOT NULL,
    user_id   INT NOT NULL,
    voted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_vote (poll_id, user_id),
    FOREIGN KEY (poll_id)   REFERENCES polls(id)        ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)   REFERENCES users(id)        ON DELETE CASCADE
);

-- ============================================================
-- Done! Your database is now ready for Guest Booking & Polls.
-- ============================================================

-- -----------------------------------------------
-- NOTE: If you already ran migrations.sql before,
-- run ONLY this line to add the winner_dish column:
-- -----------------------------------------------
-- ALTER TABLE polls ADD COLUMN winner_dish VARCHAR(150) NULL;

-- ── Dish Suggestions (student → admin) ──────────────────────────
CREATE TABLE IF NOT EXISTS dish_suggestions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    dish_name    VARCHAR(150) NOT NULL,
    meal         ENUM('Breakfast','Lunch','Snacks','Dinner') NOT NULL,
    reason       TEXT,
    votes        INT DEFAULT 0,
    status       ENUM('pending','noted','declined') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Upvotes table so each student can vote once per suggestion
CREATE TABLE IF NOT EXISTS suggestion_votes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    suggestion_id INT NOT NULL,
    user_id       INT NOT NULL,
    UNIQUE KEY uq_sugvote (suggestion_id, user_id),
    FOREIGN KEY (suggestion_id) REFERENCES dish_suggestions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
