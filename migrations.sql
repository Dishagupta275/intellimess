-- ============================================================
--  IntelliMess — Clean Database Migration (Fresh Install)
--  Run this on an empty `intellimess` database.
--  All tables derived from actual app.py queries.
-- ============================================================

CREATE DATABASE IF NOT EXISTS intellimess
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE intellimess;

-- -----------------------------------------------
-- 1. USERS
--    Used by: register, login, all foreign keys
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       VARCHAR(20)  NOT NULL DEFAULT 'student',  -- 'student' | 'admin'
    roll_no    VARCHAR(50)  NULL,
    phone_no   VARCHAR(20)  NULL
);

-- -----------------------------------------------
-- 2. DISHES
--    Master list of all dish names.
--    Used by: menu_items, feedback
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS dishes (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    dish_name  VARCHAR(150) NOT NULL UNIQUE
);

-- -----------------------------------------------
-- 3. WEEKLY MENU
--    One row per (day_of_week, meal) slot.
--    Used by: admin_menu, menu page, feedback
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS weekly_menu (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    day_of_week  VARCHAR(20) NOT NULL,   -- 'Monday' … 'Sunday'
    meal         VARCHAR(20) NOT NULL,   -- 'Breakfast' | 'Lunch' | 'Snacks' | 'Dinner'
    UNIQUE KEY uq_day_meal (day_of_week, meal)
);

-- -----------------------------------------------
-- 4. MENU ITEMS
--    Links dishes to weekly_menu slots (many-to-many).
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    weekly_menu_id  INT NOT NULL,
    dish_id         INT NOT NULL,
    UNIQUE KEY uq_menu_dish (weekly_menu_id, dish_id),
    FOREIGN KEY (weekly_menu_id) REFERENCES weekly_menu(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id)        REFERENCES dishes(id)       ON DELETE CASCADE
);

-- -----------------------------------------------
-- 5. BOOKINGS
--    Student meal bookings (includes guest support).
--    Used by: /book, /feedback, all admin views
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT          NOT NULL,
    meal             VARCHAR(20)  NOT NULL,
    food_type        VARCHAR(10)  NOT NULL,                 -- 'Veg' | 'Non-Veg'
    booking_date     DATE         NOT NULL,
    booking_time     TIME         NOT NULL,
    guest_count      INT          NOT NULL DEFAULT 0,
    guest_food_type  VARCHAR(10)  NULL,                     -- 'Veg' | 'Non-Veg'
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------
-- 6. FEEDBACK
--    Per-dish ratings from students after meals.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT  NOT NULL,
    booking_id     INT  NOT NULL,
    dish_id        INT  NOT NULL,
    rating         INT  NOT NULL CHECK (rating BETWEEN 1 AND 5),
    feedback_date  DATE NOT NULL,
    comment        TEXT NULL,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id)    REFERENCES dishes(id)   ON DELETE CASCADE
);

-- -----------------------------------------------
-- 7. POLLS
--    Admin-created dish polls for upcoming meals.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS polls (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    question      VARCHAR(255)          NOT NULL,
    meal          VARCHAR(20)           NOT NULL,
    poll_date     DATE                  NOT NULL,
    closing_time  TIME                  NOT NULL,
    status        ENUM('open','closed') NOT NULL DEFAULT 'open',
    winner_dish   VARCHAR(150)          NULL,       -- filled when poll closes
    created_at    TIMESTAMP             DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------
-- 8. POLL OPTIONS
--    Dish choices for each poll.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS poll_options (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    poll_id      INT          NOT NULL,
    option_text  VARCHAR(150) NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

-- -----------------------------------------------
-- 9. POLL VOTES
--    One vote per student per poll (enforced by UNIQUE).
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS poll_votes (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    poll_id   INT NOT NULL,
    option_id INT NOT NULL,
    user_id   INT NOT NULL,
    voted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_vote (poll_id, user_id),
    FOREIGN KEY (poll_id)   REFERENCES polls(id)        ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)   REFERENCES users(id)        ON DELETE CASCADE
);

-- -----------------------------------------------
-- 10. DISH SUGGESTIONS
--     Students suggest dishes they want to see.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS dish_suggestions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT          NOT NULL,
    dish_name     VARCHAR(150) NOT NULL,
    meal          ENUM('Breakfast','Lunch','Snacks','Dinner') NOT NULL,
    reason        TEXT         NULL,
    votes         INT          NOT NULL DEFAULT 0,
    status        ENUM('pending','noted','declined') NOT NULL DEFAULT 'pending',
    submitted_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------
-- 11. SUGGESTION VOTES
--     Prevents double-upvoting a suggestion.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS suggestion_votes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    suggestion_id  INT NOT NULL,
    user_id        INT NOT NULL,
    UNIQUE KEY uq_sugvote (suggestion_id, user_id),
    FOREIGN KEY (suggestion_id) REFERENCES dish_suggestions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)       REFERENCES users(id)             ON DELETE CASCADE
);

-- -----------------------------------------------
-- 12. USER STREAKS  (gamification)
--     One row per student; upserted after each feedback.
--     Columns match exact SELECT / INSERT in app.py.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS user_streaks (
    user_id             INT PRIMARY KEY,
    current_streak      INT   NOT NULL DEFAULT 0,
    longest_streak      INT   NOT NULL DEFAULT 0,
    last_feedback_date  DATE  NULL,
    total_feedbacks     INT   NOT NULL DEFAULT 0,
    total_ratings       INT   NOT NULL DEFAULT 0,
    avg_rating_given    FLOAT NOT NULL DEFAULT 0,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------
-- 13. USER BADGES  (gamification)
--     One row per (user, badge_key); awarded_at tracked.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS user_badges (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT         NOT NULL,
    badge_key   VARCHAR(50) NOT NULL,
    awarded_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_badge (user_id, badge_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- Seed: default admin account  (change password before deploy)
-- ============================================================
INSERT IGNORE INTO users (username, password, role)
VALUES ('admin', 'admin123', 'admin');

-- ============================================================
-- Done! All 13 tables created. Database is ready for IntelliMess.
-- ============================================================
