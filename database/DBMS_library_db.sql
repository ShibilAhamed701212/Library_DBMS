-- ======================================================
-- DATABASE SETUP
-- ======================================================
-- This script initializes the Library Management System
-- database, users, tables, constraints, and indexes.
--
-- SAFE TO RUN MULTIPLE TIMES:
-- - Uses IF NOT EXISTS
-- - Drops users before recreation
-- ======================================================

-- ------------------------------------------------------
-- Create main application database if it does not exist (disabled for cloud compliance)
-- ------------------------------------------------------
-- CREATE DATABASE IF NOT EXISTS library_db;

-- Switch context to library_db (handeled by connection string in cloud)
-- USE library_db;


-- ======================================================
-- USERS (MYSQL DATABASE-LEVEL USERS)
-- ======================================================
-- These are NOT application users.
-- These are MySQL accounts used by the app and reports.
-- ======================================================

-- ------------------------------------------------------
-- Cleanup old database users to avoid conflicts
-- ------------------------------------------------------
DROP USER IF EXISTS 'app_user'@'localhost';
DROP USER IF EXISTS 'app_user'@'%';
DROP USER IF EXISTS 'report_user'@'localhost';


-- ======================================================
-- APP USER (CRUD ACCESS)
-- ======================================================
-- This user is used by:
-- - Flask backend
-- - CLI application
--
-- Permissions:
-- - Full CRUD on library_db
-- - NO admin privileges
-- ======================================================

CREATE USER 'app_user'@'localhost'
IDENTIFIED WITH mysql_native_password
BY 'App@123';

-- Grant CRUD permissions on entire database
GRANT SELECT, INSERT, UPDATE, DELETE
ON library_db.*
TO 'app_user'@'localhost';


-- ======================================================
-- REPORT USER (READ-ONLY ACCESS)
-- ======================================================
-- This user is used for:
-- - Analytics
-- - Reports
-- - Data exports
--
-- Security principle:
-- - Least privilege
-- ======================================================

CREATE USER 'report_user'@'localhost'
IDENTIFIED WITH mysql_native_password
BY 'Report@123';

-- Grant read-only access
GRANT SELECT
ON library_db.*
TO 'report_user'@'localhost';

-- Apply privilege changes immediately
FLUSH PRIVILEGES;


-- ======================================================
-- TABLE DEFINITIONS
-- ======================================================
-- Defines core entities of the system:
-- - users
-- - books
-- - issues
-- ======================================================


-- ------------------------------------------------------
-- USERS TABLE
-- ------------------------------------------------------
-- Stores application users (admin / member)
-- Password is stored as HASH (bcrypt from app)
-- ------------------------------------------------------

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,     -- Unique user identifier
    name VARCHAR(100) NOT NULL,                  -- User full name
    email VARCHAR(100) NOT NULL UNIQUE,          -- Login email (unique)
    password_hash VARCHAR(255) NOT NULL,              -- Hashed password
    role ENUM('admin', 'member') NOT NULL,       -- Authorization role
    must_change_password BOOLEAN DEFAULT TRUE,   -- Force password change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Account creation time
);


-- ------------------------------------------------------
-- BOOKS TABLE
-- ------------------------------------------------------
-- Stores book inventory and stock tracking
-- available_copies changes with issue/return
-- ------------------------------------------------------

CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,      -- Unique book identifier
    title VARCHAR(200) NOT NULL,                  -- Book title
    author VARCHAR(100) NOT NULL,                 -- Author name
    category VARCHAR(50),                         -- Optional category
    total_copies INT NOT NULL CHECK (total_copies >= 0),       -- Total stock
    available_copies INT NOT NULL CHECK (available_copies >= 0), -- Available stock
    cover_image_url VARCHAR(255) DEFAULT NULL     -- Cover image URL
);


-- ------------------------------------------------------
-- ISSUES TABLE (HARDENED)
-- ------------------------------------------------------
-- Tracks book issue & return history
-- Enforces data integrity using constraints
-- ------------------------------------------------------

CREATE TABLE issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,     -- Unique issue record
    user_id INT NOT NULL,                         -- User who issued the book
    book_id INT NOT NULL,                         -- Issued book
    issue_date DATE NOT NULL,                     -- Issue date
    return_date DATE DEFAULT NULL,                -- Return date (NULL = active)
    fine INT DEFAULT 0,                            -- Fine amount

    -- -----------------------------------------------
    -- FOREIGN KEY: issues → users
    -- Cascade delete ensures cleanup on user removal
    -- -----------------------------------------------
    CONSTRAINT fk_issues_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    -- -----------------------------------------------
    -- FOREIGN KEY: issues → books
    -- Cascade delete ensures cleanup on book removal
    -- -----------------------------------------------
    CONSTRAINT fk_issues_book
        FOREIGN KEY (book_id)
        REFERENCES books(book_id)
        ON DELETE CASCADE,

    -- -----------------------------------------------
    -- UNIQUE CONSTRAINT
    -- Prevents multiple ACTIVE issues for same book
    -- return_date NULL means active issue
    -- -----------------------------------------------
    CONSTRAINT uq_user_book_active
        UNIQUE (user_id, book_id, return_date)
);


-- ------------------------------------------------------
-- BOOK REQUESTS TABLE
-- ------------------------------------------------------
-- Tracks books requested by members
-- ------------------------------------------------------

CREATE TABLE IF NOT EXISTS book_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    request_date DATE NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',

    -- Foreign Keys
    CONSTRAINT fk_requests_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_requests_book
        FOREIGN KEY (book_id)
        REFERENCES books(book_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------
-- BOOK SUGGESTIONS TABLE (for member suggestions)
-- ------------------------------------------------------
-- Tracks suggested books from members for admin review
-- ------------------------------------------------------

CREATE TABLE IF NOT EXISTS book_suggestions (
    suggestion_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    isbn VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','approved','rejected') DEFAULT 'pending',

    CONSTRAINT fk_suggestions_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- ======================================================
-- INDEXES (PERFORMANCE OPTIMIZATION)
-- ======================================================
-- Indexes improve query performance for:
-- - Dashboards
-- - Issue checks
-- - Analytics
-- ======================================================

-- Speed up member dashboard issue lookup
CREATE INDEX idx_issues_user
ON issues(user_id);

-- Speed up book-based queries
CREATE INDEX idx_issues_book
ON issues(book_id);

-- Speed up active issue checks (critical path)
CREATE INDEX idx_issues_user_book_active
ON issues(user_id, book_id, return_date);


-- ======================================================
-- VERIFY STRUCTURE
-- ======================================================
-- Sanity checks to verify schema correctness
-- ======================================================

SHOW TABLES;
DESCRIBE users;
DESCRIBE books;
DESCRIBE issues;
SHOW INDEX FROM issues;


-- ======================================================
-- FINAL PRIVILEGE FLUSH
-- ======================================================
-- Ensures all permission changes are active
-- ======================================================
FLUSH PRIVILEGES;
