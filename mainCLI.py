"""
mainCLI.py — Command-Line Interface for LDBMS
Uses the same service layer as the Flask web app.
"""

import sys
import getpass

from backend.services.auth_service import authenticate_user
from backend.services.user_service import view_users, add_user, delete_user
from backend.services.book_service import view_books, add_book, delete_book
from backend.services.issue_service import issue_book, return_book
from backend.services.analytics_service import search_by_title, available_books, overdue_books
from backend.repository.db_access import fetch_one, execute


# ─── Formatting Helpers ───────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
RED    = "\033[31m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
WHITE  = "\033[97m"
BG_DARK = "\033[48;5;236m"

LINE = f"{DIM}{'─' * 62}{RESET}"
THICK_LINE = f"{DIM}{'═' * 62}{RESET}"


def banner(title: str, icon: str = "📚"):
    """Prints a styled section banner."""
    print(f"\n{THICK_LINE}")
    print(f"  {icon}  {BOLD}{title}{RESET}")
    print(THICK_LINE)


def success(msg: str):
    print(f"  {GREEN}✔ {msg}{RESET}")


def error(msg: str):
    print(f"  {RED}✘ {msg}{RESET}")


def warn(msg: str):
    print(f"  {YELLOW}⚠ {msg}{RESET}")


def pause():
    input(f"\n  {DIM}Press ENTER to continue...{RESET}")


def read_int(prompt: str):
    """Safely reads an integer from stdin."""
    try:
        return int(input(f"  {prompt}"))
    except ValueError:
        error("Please enter a valid number")
        return None


def print_table(rows: list, columns: list, col_widths: list = None):
    """
    Pretty-prints a list of dicts as an aligned table.

    Args:
        rows: list of dicts (each row)
        columns: list of (key, header_label) tuples
        col_widths: optional explicit widths per column
    """
    if not rows:
        warn("No data found")
        return

    keys    = [c[0] for c in columns]
    headers = [c[1] for c in columns]

    # Auto-calculate column widths if not provided
    if col_widths is None:
        col_widths = []
        for i, key in enumerate(keys):
            max_data = max((len(str(r.get(key, ""))) for r in rows), default=0)
            col_widths.append(max(len(headers[i]), max_data) + 2)

    # Header
    header_line = "  "
    sep_line    = "  "
    for i, h in enumerate(headers):
        header_line += f"{BOLD}{h:<{col_widths[i]}}{RESET}"
        sep_line    += f"{DIM}{'─' * col_widths[i]}{RESET}"

    print(sep_line)
    print(header_line)
    print(sep_line)

    # Rows
    for row in rows:
        line = "  "
        for i, key in enumerate(keys):
            val = row.get(key, "—")
            if val is None:
                val = "—"
            # Format datetime objects
            if hasattr(val, "strftime"):
                val = val.strftime("%Y-%m-%d %H:%M")
            line += f"{str(val):<{col_widths[i]}}"
        print(line)

    print(sep_line)
    print(f"  {DIM}{len(rows)} record(s){RESET}\n")


def print_df(df):
    """Pretty-prints a Pandas DataFrame."""
    if df is None or df.empty:
        warn("No data found")
    else:
        print(f"\n{df.to_string(index=False)}\n")


# ─── Login ────────────────────────────────────────────────────────

def cli_login():
    banner("LIBRARY MANAGEMENT SYSTEM — LOGIN", "📚")

    email = input("  Email: ").strip()
    if not email:
        error("Email cannot be empty")
        return None

    try:
        password = getpass.getpass("  Password: ")
    except (KeyboardInterrupt, EOFError):
        print()
        error("Login cancelled")
        return None

    if not password:
        error("Password cannot be empty")
        return None

    user = authenticate_user(email, password)
    if not user:
        error("Invalid email or password")
        return None

    success(f"Login successful  ·  Role: {BOLD}{user['role'].upper()}{RESET}")
    return user


# ─── Admin Menu ───────────────────────────────────────────────────

ADMIN_MENU = f"""
  {CYAN}USER MANAGEMENT{RESET}
   1 │ View Users
   2 │ Add User
   3 │ Delete User

  {CYAN}BOOK MANAGEMENT{RESET}
   4 │ View Books
   5 │ Add Book
   6 │ Delete Book

  {CYAN}CIRCULATION{RESET}
   7 │ Issue Book
   8 │ Return Book

  {CYAN}ANALYTICS{RESET}
   9 │ Search Book by Title
  10 │ Available Books
  11 │ Overdue Books

  {DIM} 0 │ Logout{RESET}
"""


def admin_menu(user):
    while True:
        banner(f"ADMIN DASHBOARD  —  {user['email']}", "👑")
        print(ADMIN_MENU)

        choice = input(f"  {BOLD}▸ Choice:{RESET} ").strip().lstrip("0") or "0"

        if choice == "0":
            success("Logged out. Goodbye!")
            break

        elif choice == "1":
            print(f"\n  {BOLD}All Users{RESET}")
            users = view_users()
            print_table(users, [
                ("user_id", "ID"),
                ("name",    "Name"),
                ("email",   "Email"),
                ("role",    "Role"),
                ("created_at", "Joined"),
            ])

        elif choice == "2":
            print(f"\n  {BOLD}Add New User{RESET}")
            print(LINE)
            name     = input("  Name: ").strip()
            email    = input("  Email: ").strip()
            role     = input("  Role (admin/member): ").strip().lower()
            password = getpass.getpass("  Password: ")
            result   = add_user(name, email, role, password)
            print(f"\n  {result}")

        elif choice == "3":
            uid = read_int("User ID to delete: ")
            if uid is not None:
                confirm = input(f"  {YELLOW}Confirm delete user #{uid}? (y/n):{RESET} ").strip().lower()
                if confirm == "y":
                    print(f"\n  {delete_user(uid)}")
                else:
                    warn("Cancelled")

        elif choice == "4":
            print(f"\n  {BOLD}All Books{RESET}")
            books = view_books()
            print_table(books, [
                ("book_id",   "ID"),
                ("title",     "Title"),
                ("author",    "Author"),
                ("category",  "Category"),
                ("available_copies", "Avail"),
                ("total_copies",     "Total"),
            ])

        elif choice == "5":
            print(f"\n  {BOLD}Add New Book{RESET}")
            print(LINE)
            title       = input("  Title: ").strip()
            author_name = input("  Author: ").strip()
            category    = input("  Category: ").strip()
            copies      = read_int("Total copies: ")
            if copies is not None:
                author = fetch_one("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                if not author:
                    execute("INSERT INTO authors (name) VALUES (%s)", (author_name,))
                    author = fetch_one("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                add_book(title, author['author_id'], category, copies)
                success("Book added successfully")

        elif choice == "6":
            bid = read_int("Book ID to delete: ")
            if bid is not None:
                confirm = input(f"  {YELLOW}Confirm delete book #{bid}? (y/n):{RESET} ").strip().lower()
                if confirm == "y":
                    print(f"\n  {delete_book(bid)}")
                else:
                    warn("Cancelled")

        elif choice == "7":
            print(f"\n  {BOLD}Issue Book{RESET}")
            print(LINE)
            uid = read_int("User ID: ")
            bid = read_int("Book ID: ")
            if uid and bid:
                print(f"\n  {issue_book(uid, bid)}")

        elif choice == "8":
            print(f"\n  {BOLD}Return Book{RESET}")
            print(LINE)
            uid = read_int("User ID: ")
            bid = read_int("Book ID: ")
            if uid and bid:
                print(f"\n  {return_book(uid, bid)}")

        elif choice == "9":
            key = input("  Search title: ").strip()
            print_df(search_by_title(key))

        elif choice == "10":
            print(f"\n  {BOLD}Available Books{RESET}")
            print_df(available_books())

        elif choice == "11":
            print(f"\n  {BOLD}Overdue Books{RESET}")
            print_df(overdue_books())

        else:
            error("Invalid choice — enter a number from the menu")

        pause()


# ─── Member Menu ──────────────────────────────────────────────────

MEMBER_MENU = f"""
  {CYAN}CATALOG{RESET}
   1 │ View Available Books
   2 │ Search Book by Title

  {DIM} 0 │ Logout{RESET}
"""


def member_menu(user):
    while True:
        banner(f"MEMBER DASHBOARD  —  {user['email']}", "👤")
        print(MEMBER_MENU)

        choice = input(f"  {BOLD}▸ Choice:{RESET} ").strip().lstrip("0") or "0"

        if choice == "0":
            success("Logged out. Goodbye!")
            break

        elif choice == "1":
            print(f"\n  {BOLD}Available Books{RESET}")
            print_df(available_books())

        elif choice == "2":
            key = input("  Search title: ").strip()
            print_df(search_by_title(key))

        else:
            error("Invalid choice — enter a number from the menu")

        pause()


# ─── Entry Point ──────────────────────────────────────────────────

def main():
    user = cli_login()
    if not user:
        return

    if user["role"] == "admin":
        admin_menu(user)
    else:
        member_menu(user)


if __name__ == "__main__":
    main()
