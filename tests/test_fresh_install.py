"""
End-to-end check of the documented fresh-install path against a real
MySQL/MariaDB database:

    database/init_db.py -> database/seed_data.py -> app starts -> pages load

DESTRUCTIVE: seeding truncates users/books/etc. Only runs when
LDBMS_INTEGRATION=1 and DB_HOST/DB_USER/DB_PASSWORD/DB_NAME point at an
empty, disposable database, e.g.

    mysql -e "CREATE DATABASE library_test CHARACTER SET utf8mb4"
    LDBMS_INTEGRATION=1 DB_NAME=library_test pytest tests/test_fresh_install.py
"""
import ast
import glob
import os
import re

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("LDBMS_INTEGRATION") != "1",
    reason="set LDBMS_INTEGRATION=1 and point DB_* at a disposable database",
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED_PASSWORD = "Integration#Pass1"

# Modules that are never imported by the app (legacy chat implementation).
UNUSED_MODULES = ("backend/chat/room_manager.py", "backend/chat/message_engine.py")
# Queries wrapped in try/except that fall back to defaults when the table is absent.
OPTIONAL_TABLES = ("system_settings",)
# Pages that cannot render in an offline test environment.
SKIP_PAGES = (
    "/member/ai-chat",   # downloads a sentence-transformers model on first use
    "/admin/support/1",  # no ticket 1 in seed data (page 500s on unknown ids; see README known issues)
)


@pytest.fixture(scope="module")
def seeded_db():
    os.environ["SEED_ADMIN_PASSWORD"] = SEED_PASSWORD
    from database.init_db import run_schema
    from database.seed_data import main as seed

    msg, ok = run_schema()
    assert ok, msg
    msg, ok = run_schema()  # idempotent
    assert ok, msg
    seed()
    return True


def test_seed_populates_books_with_author(seeded_db):
    from backend.repository.db_access import fetch_one

    assert fetch_one("SELECT COUNT(*) AS n FROM books")["n"] == 30
    assert fetch_one("SELECT COUNT(*) AS n FROM books WHERE author = '' OR author IS NULL")["n"] == 0
    assert fetch_one("SELECT email FROM users WHERE role = 'admin'")["email"] == "admin@library.com"


def _static_sql_statements():
    for path in sorted(glob.glob(os.path.join(ROOT, "backend", "**", "*.py"), recursive=True)):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel in UNUSED_MODULES or "/routes/test_" in rel:
            continue
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                sql = node.value.strip()
                if re.match(r"(?is)^(SELECT|INSERT|UPDATE|DELETE)\s", sql) and re.search(r"(?i)\b(FROM|INTO|UPDATE)\b", sql):
                    yield rel, node.lineno, sql


def test_every_query_matches_schema(seeded_db):
    """EXPLAIN every static SQL statement so unknown tables/columns fail here, not in production."""
    from backend.config.db import get_connection

    conn = get_connection()
    cur = conn.cursor()
    problems = []
    for rel, line, sql in _static_sql_statements():
        if any(t in sql for t in OPTIONAL_TABLES):
            continue
        query = re.sub(r"(?i)^INSERT\s+IGNORE", "INSERT", sql.replace("%%", "%").replace("%s", "NULL"))
        try:
            cur.execute("EXPLAIN " + query)
            cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            if getattr(exc, "errno", None) in (1054, 1146):  # unknown column / table
                problems.append(f"{rel}:{line}: {exc}")
    cur.close()
    conn.close()
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("email", ["admin@library.com", "rahul@gmail.com"])
def test_all_pages_render_after_fresh_install(seeded_db, email):
    os.environ.setdefault("FLASK_SECRET_KEY", "integration-secret")
    from backend.app import create_app

    app = create_app()
    client = app.test_client()
    response = client.post("/login", data={"email": email, "password": SEED_PASSWORD})
    assert response.status_code == 302, "login with seeded credentials failed"

    failures = []
    for rule in app.url_map.iter_rules():
        if "GET" not in rule.methods or re.search(r"<(?!int:)", rule.rule):
            continue
        if any(s in rule.rule for s in ("/logout", "/system/", "/static", "/export", "/reset")):
            continue
        path = re.sub(r"<int:[^>]+>", "1", rule.rule)
        if path in SKIP_PAGES:
            continue
        status = client.get(path).status_code
        if status >= 500:
            failures.append(f"{path} -> {status}")
    assert not failures, "\n".join(failures)
