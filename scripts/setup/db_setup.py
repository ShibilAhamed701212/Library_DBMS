"""
db_setup.py
-----------
This script initializes the database by creating necessary tables and adding an admin user.
Run this script once to set up your database.
"""

import os
import sys
from getpass import getpass
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# FIX 1: Removed 'get_db_connection' from import because it does not exist in db_access.py
from backend.repository.db_access import execute_query, fetch_one

def create_tables():
    """Create necessary database tables if they don't exist."""
    print("🛠  Creating database tables...")

    try:
        # 1. Create users table
        # FIX 2: Changed 'id' to 'user_id' to match your users.html template
        execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            role ENUM('admin', 'member') NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            must_change_password BOOLEAN DEFAULT TRUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("   - 'users' table checked/created.")

        # 2. Create books table (Added this because it was missing)
        execute_query("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) UNIQUE,
            category VARCHAR(100),
            quantity INT DEFAULT 1,
            available_quantity INT DEFAULT 1,
            cover_image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("   - 'books' table checked/created.")

        # 3. Create book_suggestions table
        # FIX 3: Updated Foreign Key to reference 'user_id' instead of 'id'
        execute_query("""
        CREATE TABLE IF NOT EXISTS book_suggestions (
            suggestion_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255),
            isbn VARCHAR(20),
            notes TEXT,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("   - 'book_suggestions' table checked/created.")

        # 4. Create issues table (Used by the application)
        execute_query("""
        CREATE TABLE IF NOT EXISTS issues (
            issue_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            book_id INT NOT NULL,
            issue_date DATE NOT NULL,
            return_date DATE DEFAULT NULL,
            fine INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            UNIQUE KEY uq_user_book_active (user_id, book_id, return_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("   - 'issues' table checked/created.")

        print("✅ All database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

def create_admin_user():
    """Create an admin user if one doesn't exist."""
    try:
        # Check if admin user already exists
        # FIX 4: Changed 'id' to 'user_id' in query
        admin = fetch_one("SELECT user_id FROM users WHERE email = 'admin@example.com'")

        if admin:
            print("ℹ️  Admin user already exists.")
            return True

        # Get admin details
        print("\n👤 Create Admin User")
        print("--------------------")
        name = input("Admin name [Admin]: ").strip() or "Admin"
        email = input("Admin email [admin@example.com]: ").strip() or "admin@example.com"

        while True:
            password = getpass("Admin password (min 8 characters): ")
            if len(password) >= 8:
                break
            print("Password must be at least 8 characters long. Please try again.")

        # Hash the password
        password_hash = generate_password_hash(password)

        # Insert admin user
        execute_query(
            """
            INSERT INTO users (name, email, password_hash, role, must_change_password)
            VALUES (%s, %s, %s, 'admin', FALSE)
            """,
            (name, email, password_hash)
        )

        print("\n✅ Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Password: {'*' * len(password)}")
        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up the database...\n")

    # Create tables
    if not create_tables():
        print("\n❌ Failed to create tables. Please check the error message above.")
        sys.exit(1)

    # Create admin user
    if not create_admin_user():
        print("\n❌ Failed to create admin user. Please check the error message above.")
        sys.exit(1)

    print("\n✨ Database setup completed successfully!")
    print("You can now log in with the admin credentials you provided.")