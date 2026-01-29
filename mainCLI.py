"""
mainCLI.py
----------
Advanced CLI for Library DBMS

This file provides a command-line interface (CLI) for the Library Management System.

Key features:
- Secure login using the same authentication logic as Flask
- Role-based menus (Admin / Member)
- Reuses service layer (no duplicate logic)
- Uses Pandas-powered analytics for search/filter
- Safe password input (Windows / IDE compatible)
"""

# ===================== STANDARD LIBRARIES =====================

import sys              # Used for system-level operations (future-safe, exits, etc.)
import getpass          # Secure password input (does not echo characters)


# ===================== SERVICE LAYER IMPORTS =====================
# These are the SAME services used by the Flask web app
# This ensures consistency between CLI and Web UI

from backend.services.auth_service import authenticate_user
from backend.services.user_service import view_users, add_user, delete_user
from backend.services.book_service import view_books, add_book, delete_book
from backend.services.issue_service import issue_book, return_book
from backend.services.analytics_service import (
    search_by_title,
    available_books,
    overdue_books
)


# ===================== CLI UTILITY FUNCTIONS =====================

def divider():
    """
    Prints a visual divider line for better CLI readability.
    """
    print("\n" + "=" * 60)


def pause():
    """
    Pauses execution until user presses ENTER.
    Prevents menu from instantly refreshing.
    """
    input("\nPress ENTER to continue...")


def read_int(prompt: str):
    """
    Safely reads integer input from the user.

    Prevents ValueError crashes when user enters invalid input.
    Returns:
        int   -> if valid
        None  -> if invalid
    """
    try:
        return int(input(prompt))
    except ValueError:
        print("❌ Please enter a valid number")
        return None


def print_df(df):
    """
    Pretty-prints a Pandas DataFrame safely.

    - Avoids ugly index numbering
    - Handles empty or None DataFrames gracefully
    """
    if df is None or df.empty:
        print("⚠ No data found")
    else:
        print(df.to_string(index=False))


# ===================== LOGIN HANDLER =====================

def cli_login():
    """
    Handles CLI login flow.

    Steps:
    1. Ask for email
    2. Securely ask for password
    3. Authenticate using auth_service
    4. Return user object if valid
    """

    divider()
    print("📚 LIBRARY MANAGEMENT SYSTEM — CLI LOGIN")
    divider()

    # Read email input
    email = input("Email: ").strip()

    # Basic validation
    if not email:
        print("❌ Email cannot be empty")
        return None

    # ---- SAFE PASSWORD INPUT ----
    # getpass hides input and works in Windows / IDE terminals
    try:
        password = getpass.getpass("Password: ")
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or broken input stream
        print("\n❌ Login cancelled")
        return None

    # Validate password
    if not password:
        print("❌ Password cannot be empty")
        return None

    # Authenticate using service layer (DB-backed)
    user = authenticate_user(email, password)

    # Authentication failure
    if not user:
        print("❌ Invalid email or password")
        return None

    # Success
    print(f"\n✅ Login successful | Role: {user['role'].upper()}")
    return user


# ===================== ADMIN MENU =====================

def admin_menu(user):
    """
    Displays and handles Admin menu operations.

    Admin capabilities:
    - User management
    - Book management
    - Issue / return books
    - Analytics (Pandas-powered)
    """

    while True:
        divider()
        print(f"👑 ADMIN DASHBOARD — {user['email']}")
        divider()

        # Menu options
        print("""
01. View Users
02. Add User
03. Delete User
04. View Books
05. Add Book
06. Delete Book
07. Issue Book
08. Return Book
09. Search Book by Title
10. Available Books
11. Overdue Books
00. Logout
""")

        # Read menu choice
        choice = input("👉 Enter choice: ").strip()

        # Logout
        if choice == "00":
            print("👋 Logged out")
            break

        # View all users
        elif choice == "01":
            for u in view_users():
                print(u)

        # Add a new user
        elif choice == "02":
            name = input("Name: ").strip()
            email = input("Email: ").strip()
            role = input("Role (admin/member): ").strip().lower()
            password = getpass.getpass("Password: ")
            print(add_user(name, email, role, password))

        # Delete a user
        elif choice == "03":
            uid = read_int("User ID to delete: ")
            if uid is not None:
                print(delete_user(uid))

        # View all books
        elif choice == "04":
            for b in view_books():
                print(b)

        # Add a new book
        elif choice == "05":
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            category = input("Category: ").strip()
            copies = read_int("Total copies: ")
            if copies is not None:
                add_book(title, author, category, copies)
                print("✅ Book added")

        # Delete a book
        elif choice == "06":
            bid = read_int("Book ID to delete: ")
            if bid is not None:
                print(delete_book(bid))

        # Issue a book
        elif choice == "07":
            uid = read_int("User ID: ")
            bid = read_int("Book ID: ")
            if uid is not None and bid is not None:
                print(issue_book(uid, bid))

        # Return a book
        elif choice == "08":
            uid = read_int("User ID: ")
            bid = read_int("Book ID: ")
            if uid is not None and bid is not None:
                print(return_book(uid, bid))

        # Search books (Pandas)
        elif choice == "09":
            key = input("Search title: ")
            print_df(search_by_title(key))

        # View available books (Pandas filter)
        elif choice == "10":
            print_df(available_books())

        # View overdue books (Pandas analytics)
        elif choice == "11":
            print_df(overdue_books())

        # Invalid menu option
        else:
            print("❌ Invalid choice")

        pause()


# ===================== MEMBER MENU =====================

def member_menu(user):
    """
    Displays and handles Member menu operations.

    Member capabilities:
    - View available books
    - Search books
    """

    while True:
        divider()
        print(f"👤 MEMBER DASHBOARD — {user['email']}")
        divider()

        print("""
01. View Available Books
02. Search Book by Title
00. Logout
""")

        choice = input("👉 Enter choice: ").strip()

        # Logout
        if choice == "00":
            print("👋 Logged out")
            break

        # View available books
        elif choice == "01":
            print_df(available_books())

        # Search books
        elif choice == "02":
            key = input("Search title: ")
            print_df(search_by_title(key))

        else:
            print("❌ Invalid choice")

        pause()


# ===================== PROGRAM ENTRY POINT =====================

def main():
    """
    Entry point for CLI application.

    Flow:
    1. Login
    2. Route user based on role
    """

    user = cli_login()

    # Exit if login failed
    if not user:
        return

    # Role-based menu routing
    if user["role"] == "admin":
        admin_menu(user)
    else:
        member_menu(user)


# Run CLI only if executed directly
if __name__ == "__main__":
    main()
