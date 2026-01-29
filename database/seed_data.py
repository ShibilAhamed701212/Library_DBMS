"""
seed_data.py
------------
Seeds initial data into the database using
application services (professional approach).

Run:
    python database/seed_data.py
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# ------------------------------------------------------
# IMPORT APPLICATION SERVICES
# ------------------------------------------------------
from backend.services.user_service import add_user
from backend.services.book_service import add_book
from backend.repository.db_access import fetch_one
from backend.config.db import get_connection

# ======================================================
# CLEAR EXISTING BOOKS
# ======================================================

def clear_books():
    """
    Deletes all existing book records from the database.
    """
    print("\n🗑️  Clearing existing books...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books")
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ All existing books deleted")
    except Exception as e:
        print(f"❌ Error clearing books: {e}")


# ======================================================
# USER SEEDING
# ======================================================

def seed_users():
    """
    Inserts admin and member users.
    - Uses add_user() service
    - Automatically hashes passwords
    - Enforces uniqueness on email
    """
    users = [
        ("Admin User", "admin@library.com", "admin", "Admin@123"),
        ("Rahul Verma", "rahul@gmail.com", "member", "Admin@123"),
        ("Aisha Khan", "aisha@gmail.com", "member", "Admin@123"),
        ("Neha Sharma", "neha@gmail.com", "member", "Admin@123"),
    ]

    for name, email, role, password in users:
        result = add_user(name, email, role, password)
        print(result)


# ======================================================
# BOOK SEEDING - 30 DIVERSE BOOKS
# ======================================================

def seed_books():
    """
    Inserts 30 diverse books across multiple categories.
    Format: (title, author, category, total_copies)
    """
    books = [
        # Programming & Technology (8 books)
        ("Clean Code", "Robert C. Martin", "Programming", 10),
        ("The Pragmatic Programmer", "Andrew Hunt", "Programming", 8),
        ("Python Crash Course", "Eric Matthes", "Programming", 12),
        ("JavaScript: The Good Parts", "Douglas Crockford", "Programming", 7),
        ("Design Patterns", "Gang of Four", "Programming", 6),
        ("Head First Java", "Kathy Sierra", "Programming", 9),
        ("You Don't Know JS", "Kyle Simpson", "Programming", 8),
        ("Eloquent JavaScript", "Marijn Haverbeke", "Programming", 10),
        
        # Fiction (7 books)
        ("The Alchemist", "Paulo Coelho", "Fiction", 15),
        ("1984", "George Orwell", "Fiction", 12),
        ("To Kill a Mockingbird", "Harper Lee", "Fiction", 10),
        ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 8),
        ("Pride and Prejudice", "Jane Austen", "Fiction", 9),
        ("The Catcher in the Rye", "J.D. Salinger", "Fiction", 7),
        ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fiction", 20),
        
        # Non-Fiction & Self-Help (8 books)
        ("Atomic Habits", "James Clear", "Self Help", 18),
        ("Sapiens", "Yuval Noah Harari", "History", 14),
        ("Educated", "Tara Westover", "Biography", 10),
        ("Thinking, Fast and Slow", "Daniel Kahneman", "Psychology", 9),
        ("The 7 Habits of Highly Effective People", "Stephen Covey", "Self Help", 12),
        ("How to Win Friends and Influence People", "Dale Carnegie", "Self Help", 11),
        ("Man's Search for Meaning", "Viktor Frankl", "Philosophy", 8),
        ("The Power of Now", "Eckhart Tolle", "Spirituality", 10),
        
        # Science & History (7 books)
        ("A Brief History of Time", "Stephen Hawking", "Science", 8),
        ("Cosmos", "Carl Sagan", "Science", 9),
        ("The Immortal Life of Henrietta Lacks", "Rebecca Skloot", "Science", 7),
        ("Guns, Germs, and Steel", "Jared Diamond", "History", 6),
        ("The Wright Brothers", "David McCullough", "History", 8),
        ("Steve Jobs", "Walter Isaacson", "Biography", 12),
        ("Becoming", "Michelle Obama", "Biography", 15),
    ]

    for title, author, category, copies in books:
        result = add_book(title, author, category, copies)
        print(result)


# ======================================================
# VERIFICATION STEP
# ======================================================

def verify_seed():
    """
    Verifies that seeding completed successfully.
    """
    admin = fetch_one("SELECT email FROM users WHERE role = 'admin'")
    book_count = fetch_one("SELECT COUNT(*) as count FROM books")
    
    if admin and book_count:
        print(f"✅ Seed verification successful")
        print(f"📚 Total books in database: {book_count['count']}")
    else:
        print("❌ Seed verification failed")


# ======================================================
# MAIN ENTRY POINT
# ======================================================

def main():
    """
    Main entry point for seeding.
    
    Execution order:
    1. Clear existing books
    2. Seed users
    3. Seed 30 new books
    4. Verify seed
    """
    print("\n" + "="*50)
    print("🌱 DATABASE SEEDING STARTED")
    print("="*50)
    
    clear_books()
    
    print("\n🌱 Seeding users...")
    seed_users()

    print("\n📚 Seeding 30 books...")
    seed_books()

    print("\n🔍 Verifying seed...")
    verify_seed()

    print("\n" + "="*50)
    print("✅ DATABASE SEEDING COMPLETED")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
