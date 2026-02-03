-- Migration: Add Authors and Series Support
-- Date: 2026-01-31

CREATE TABLE IF NOT EXISTS authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    bio TEXT,
    image_url VARCHAR(255),
    nationality VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS series (
    series_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: ADD COLUMN IF NOT EXISTS is not standard MySQL < 8.0
-- I'll use a safer approach in my python script or just check if they exist.
-- For now, I'll assume they don't exist yet as this is a new feature.

ALTER TABLE books ADD COLUMN author_id INT AFTER author;
ALTER TABLE books ADD COLUMN series_id INT AFTER author_id;
ALTER TABLE books ADD COLUMN series_order INT AFTER series_id;

-- Add Constraints
ALTER TABLE books ADD CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE SET NULL;
ALTER TABLE books ADD CONSTRAINT fk_books_series FOREIGN KEY (series_id) REFERENCES series(series_id) ON DELETE SET NULL;
