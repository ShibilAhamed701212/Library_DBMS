# 📚 Library Database Management System (LDBMS)

A Flask + MySQL library management web application with separate admin and member portals, real-time community chat (Socket.IO), gamification, membership tiers, and optional AI-assisted book discovery.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/MySQL%20%2F%20MariaDB-utf8mb4-orange.svg)](https://www.mysql.com/)
[![Real-Time](https://img.shields.io/badge/Real--Time-Socket.IO-black.svg)](https://socket.io/)

---

## Contents

- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running](#-running)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Interfaces and screens](#-interfaces-and-screens)
- [HTTP API](#-http-api)
- [Security notes](#-security-notes)
- [Known limitations](#-known-limitations)
- [Further documentation](#-further-documentation)

---

## ✨ Features

**Members** (`/member/...`)
- Browse and search the catalog, view authors and series, and read attached e-books (PDF).
- Request books, reserve titles, keep a wishlist and suggest new books for purchase.
- Dashboard with current loans, fines and notifications.
- Reading goals, XP/levels, achievement badges and a leaderboard.
- Membership tiers (Silver / Gold / Platinum) that set loan limits and loan days.
- Public or private reading profile, friend requests and privacy settings.
- Support tickets and personal API keys for the read-only catalog API.

**Admins** (`/dashboard`, `/admin/...`)
- Book, author and series management, including PDF e-book upload and CSV import/export.
- Issue/return workflow, request and suggestion queues, purchase list.
- User management and approval of public account requests.
- Analytics dashboard (Chart.js), reports and CSV exports.
- System health page (DB latency, CPU/memory via `psutil`), audit logs, maintenance mode and library settings.
- Community hub moderation (channels, chat audit log).

**Community chat** (`/chat/...`, Socket.IO)
- Admin-only "Global Community" announcement channel, public channels, private groups, guilds and direct messages.
- Anonymous posting mode, replies, edits and deletes, file/image attachments, channel rules and per-channel audit log.

**Public**
- Landing page with the catalog preview (`/`).
- Account requests with email OTP verification (`/request-account`, `/verify-email`); an admin approves them.

**Background jobs** (APScheduler, started by `run.py`)
- Daily overdue-reminder emails (10:00) and a weekly report (Mondays 09:00).

**Optional AI features**
- "Vibe" discovery via Google Gemini (`GEMINI_API_KEY`).
- AI librarian chat (`/member/ai-chat`) using a local ChromaDB vector store, `sentence-transformers` embeddings and the Hugging Face Inference API (`HF_TOKEN`), with a local TinyLlama fallback.

---

## 🧰 Tech stack

| Layer | Technology (pinned in `requirements.txt`) |
|---|---|
| Web framework | Flask 2.3.3, Werkzeug 2.3.7, Jinja2 3.1.3 |
| Real-time | Flask-SocketIO 5.3.6 (threading async mode) |
| Database | MySQL / MariaDB via `mysql-connector-python` 8.3.0 (connection pool, raw SQL) |
| Auth | Server-side sessions in signed cookies, `bcrypt` password hashing |
| Scheduling | APScheduler 3.11.2 |
| Reports | `fpdf2` (PDF), `pandas` (analytics/CSV) |
| AI (optional) | `google-generativeai`, `chromadb`, `sentence-transformers`, `transformers`, `huggingface_hub` |
| Frontend | Jinja2 templates, Tailwind CSS (CDN), vanilla JavaScript, Chart.js |
| Serving | `run.py` (Socket.IO dev server, optional ngrok tunnel) or `gunicorn run:app` |

---

## 🏗️ Architecture

```
Browser ──HTTP──▶ Flask blueprints (backend/routes) ──▶ services (backend/services) ──▶ db_access ──▶ MySQL
   └──Socket.IO──▶ backend/chat/socket_service.py ──────┘
APScheduler (backend/scheduler.py) ──▶ email / report services
```

```
Library_DBMS/
├── backend/
│   ├── app.py               # App factory: blueprints, Socket.IO, maintenance hook, security headers
│   ├── routes/              # auth, public, admin, member, chat, analytics, system, common
│   ├── services/            # business logic (books, issues, chat, gamification, email, AI, ...)
│   ├── chat/socket_service.py  # Socket.IO events (join/send/edit/delete/typing)
│   ├── repository/db_access.py # thin SQL helpers over the connection pool
│   ├── config/db.py         # pooled MySQL connection from environment variables
│   ├── brain/               # AI librarian (RAG + LLM orchestration)
│   └── scheduler.py         # background jobs
├── database/
│   ├── schema.sql           # complete, idempotent schema + reference data (source of truth)
│   ├── init_db.py           # loads schema.sql
│   └── seed_data.py         # demo users + 30 books (destructive, see below)
├── templates/               # admin/, member/ and shared pages
├── static/                  # CSS, JS; uploads/ is runtime data (git-ignored)
├── tests/                   # pytest suite (unit + optional fresh-install integration test)
├── scripts/                 # historical setup/migration/debug scripts (not needed for a fresh install)
├── docs/                    # design notes, deployment guide, audit report
├── run.py                   # development entry point / WSGI `app`
├── pythonanywhere_wsgi.py   # PythonAnywhere WSGI entry point
└── Procfile                 # `web: gunicorn run:app`
```

---

## ⚙️ Installation

Prerequisites: **Python 3.11** (the version the suite was verified with), a **MySQL 8 or MariaDB 10.6+** server, and roughly 3 GB of disk for the AI dependencies (`sentence-transformers` pulls in PyTorch).

### 1. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the database and a user

The application user needs DDL rights on its own database: `init_db.py` creates the tables, and a few routes run `CREATE TABLE IF NOT EXISTS` at runtime.

```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON library_db.* TO 'app_user'@'localhost';
```

The connector requests the `mysql_native_password` plugin by default (`DB_AUTH_PLUGIN`). On MySQL 8.0 either create the user `IDENTIFIED WITH mysql_native_password BY '...'`, or set `DB_AUTH_PLUGIN=caching_sha2_password`. MySQL 8.4+ disables `mysql_native_password` by default, so use `caching_sha2_password` there.

### 3. Configure `.env`

Create `.env` in the project root (see [Configuration](#-configuration)):

```env
FLASK_SECRET_KEY=generate-a-long-random-value
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=library_db
DB_USER=app_user
DB_PASSWORD=choose-a-strong-password
```

Generate a secret with `python -c "import secrets; print(secrets.token_hex(32))"`.

### 4. Create the schema

```bash
python database/init_db.py
```

This loads `database/schema.sql`. It is idempotent (it only creates missing tables and inserts missing reference rows), and exits non-zero if any statement fails.

### 5. (Optional) Load demo data

> ⚠️ `seed_data.py` **deletes** all users, books, authors, series, issues, requests and suggestions first. Only run it on a new or demo database.

```bash
SEED_ADMIN_PASSWORD='pick-a-password' python database/seed_data.py
```

It creates `admin@library.com` (admin) and three members (`rahul@gmail.com`, `aisha@gmail.com`, `neha@gmail.com`), all with `SEED_ADMIN_PASSWORD`, plus 30 books. If `SEED_ADMIN_PASSWORD` is not set, a random password is generated and printed once.

Without demo data, create the first admin account with the user service (you will be asked to change the password at first login):

```bash
python -c "from backend.services.user_service import add_user; print(add_user('Site Admin', 'you@example.com', 'admin', 'a-temporary-password'))"
```

### 6. (Optional) Build the AI vector store

The AI librarian reads book embeddings from `backend/brain/data/` (git-ignored). To index the current catalog (this downloads the `all-MiniLM-L6-v2` model on first run):

```bash
PYTHONPATH=. python scripts/migrations/ingest_books.py
```

---

## 🔧 Configuration

All settings are environment variables (loaded from `.env` by `python-dotenv`).

| Variable | Required | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | **Yes** | Signs session cookies. `SECRET_KEY` is accepted as an alias. If neither is set, a random key is generated per process: everyone is logged out on restart, and sessions break with more than one worker. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Yes | MySQL connection (defaults: `127.0.0.1`, `3306`, `library_db`, `app_user`, empty password). |
| `DB_AUTH_PLUGIN` | No | Default `mysql_native_password`; see installation step 2. |
| `DB_POOL_SIZE` | No | Connection pool size (default `5`). |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | For email | Account-request OTPs, credential emails, reminders. Defaults: `smtp.gmail.com`, `587`. Without them, emails are skipped and OTP sign-up cannot complete. |
| `SEED_ADMIN_PASSWORD` | No | Password for accounts created by `seed_data.py`. |
| `DB_INIT_TOKEN` | No | Enables `/system/initialize-db-cloud-sync` (see [Deployment](#-deployment)). The route returns 404 when this is unset. |
| `GEMINI_API_KEY` | No | Gemini-powered vibe discovery. |
| `HF_TOKEN` | No | Hugging Face Inference API for the AI librarian. |
| `NGROK_AUTHTOKEN` | No | `run.py` opens a public ngrok tunnel when this is set. |
| `LOG_LEVEL`, `FLASK_ENV` | No | Logging level and config profile used by `backend/config/config.py`. |

---

## ▶️ Running

**Development** (Socket.IO server with auto-reload, background scheduler, optional ngrok):

```bash
python run.py
# → http://127.0.0.1:5000
```

**Production-style** (as in `Procfile`):

```bash
gunicorn run:app
```

Under gunicorn the APScheduler jobs are not started (they start only in `run.py` and `pythonanywhere_wsgi.py`). Socket.IO falls back to HTTP long-polling with the default sync worker.

---

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest
```

- `tests/test_security.py`: regression tests for the security fixes (secret key, reset endpoint, debug route, OTP storage, chat authorization, upload validation, invites). No database needed.
- `tests/test_books.py`: book creation and update, and the admin add-book route.
- `tests/test_fresh_install.py`: end-to-end fresh-install check. It runs `init_db` twice and then `seed_data`, EXPLAINs every SQL statement in `backend/` against the schema, and loads every page as an admin and as a member. It is **destructive** and skipped by default:

  ```bash
  mysql -e "CREATE DATABASE library_test CHARACTER SET utf8mb4"
  LDBMS_INTEGRATION=1 DB_NAME=library_test pytest tests/test_fresh_install.py
  ```

---

## 🚀 Deployment

See [docs/02_Deployment_Guide.md](docs/02_Deployment_Guide.md) for Render + an external MySQL, and `pythonanywhere_wsgi.py` for PythonAnywhere. In short:

1. Set `FLASK_SECRET_KEY` and the `DB_*` variables (plus `SMTP_*` for email).
2. Run `python database/init_db.py` once from a shell.
3. If the host has no shell, set a long random `DB_INIT_TOKEN` temporarily and open `/system/initialize-db-cloud-sync?token=<DB_INIT_TOKEN>`. **This runs the schema and the destructive seed**, so use it only on an empty database. Remove `DB_INIT_TOKEN` afterwards.
4. Persist `static/uploads/` (avatars, chat files, channel icons, e-books) on durable storage. It is not part of the repository.

---

## 🖥️ Interfaces and screens

| Area | Main pages (templates) |
|---|---|
| Public | Landing page `/` (`public_landing.html`), login `/login`, email verification `/verify-email`, maintenance page |
| Member | Dashboard, catalog, author/series pages, e-book reader, discovery, wishlist, goals, achievements, leaderboard, community chat, AI chat, plans, profile/public profile, suggestions, support tickets, API keys (`templates/member/`) |
| Admin | Overview dashboard, books, authors, series, issues, requests, suggestions, purchase list, users, account requests, analytics, reports, health, audit logs, settings, community hub, support tickets, ISBN scanner (`templates/admin/`) |

Screenshots are not included yet. The UI loads Tailwind CSS, fonts and Chart.js from public CDNs, which were unreachable in the environment where this documentation was verified, so screenshots taken there would not have shown the real styling.

---

## 🔌 HTTP API

Most endpoints serve the bundled UI and require a logged-in session. The JSON endpoints most useful for integrations are:

| Method & path | Auth | Description |
|---|---|---|
| `GET /api/external/catalog` | `X-API-Key` header (member API key) | Full book catalog as JSON |
| `GET /api/book/get/<book_id>` | Session | Book details |
| `GET /api/notifications/unread` | Session | Unread notifications |
| `GET /chat/conversations` | Member session | DMs, public channels and groups for the current user |
| `GET /chat/channels/<id>/messages` | Member session with access to the channel | Latest 50 messages |
| `POST /chat/invites/send`, `POST /chat/invites/handle` | Member session | Send / answer DM or group invites |
| `GET /admin/analytics/data` | Admin session | Analytics data used by the dashboard |

Socket.IO events (`backend/chat/socket_service.py`): `join_channel`, `send_message`, `edit_message`, `delete_message`, `typing`, `stop_typing`. The server emits `message_history`, `receive_message`, `message_updated`, `message_deleted` and `error`.

---

## 🔐 Security notes

- Passwords are hashed with bcrypt. New accounts must change their temporary password on first login.
- Session cookies are signed with `FLASK_SECRET_KEY`; there is no hard-coded fallback key.
- The email OTP is never stored in the client-readable session cookie (only an HMAC). It expires after 10 minutes and allows 5 attempts.
- Chat history and posting are limited to channel participants (DMs, private groups) or guild members. Renaming a channel, changing its settings or rules, and answering invites are limited to the right users.
- Uploaded channel icons must be images, and e-books must be PDFs. All responses send `X-Content-Type-Options: nosniff`.
- The database reset endpoint is disabled unless `DB_INIT_TOKEN` is set, and the user-listing debug endpoint is no longer registered.

The fixes and their verification are listed in [docs/05_Audit_and_Fixes.md](docs/05_Audit_and_Fixes.md).

---

## ⚠️ Known limitations

- **No CSRF protection** on form and JSON POSTs. The session cookie sets no `SameSite` attribute, so it relies on the browser default (`Lax` in current Chromium and Firefox), which is not a complete defense.
- Joining a non-DM group by channel ID (`POST /chat/join/<id>`) is open to any member by design, so "private" groups depend on the ID not being known.
- OTP attempt counting is in-process memory: it resets on restart and is not shared between workers.
- `/admin/support/<id>` and the member ticket page return HTTP 500 for a ticket ID that doesn't exist.
- The AI features were not exercised end to end here. Gemini discovery uses the `gemini-1.5-flash` model ID, and the AI librarian downloads Hugging Face models on first use and needs network access.
- Verified on MariaDB 10.11 with Python 3.11. MySQL 8 should work with the same schema (see the authentication note above) but was not tested.
- `scripts/setup` and `scripts/migrations` are historical one-off scripts kept for reference. Some are destructive (`reset_*`), and none are needed for a fresh install.
- `backend/chat/room_manager.py` and `backend/chat/message_engine.py` are unused legacy modules that reference tables not in the schema.

---

## 📖 Further documentation

- [docs/05_Audit_and_Fixes.md](docs/05_Audit_and_Fixes.md): audit findings, fixes and validation
- [docs/02_Deployment_Guide.md](docs/02_Deployment_Guide.md): deploying to Render with an external MySQL
- [docs/03_Chat_System_Design.md](docs/03_Chat_System_Design.md): chat internals
- [docs/01_LDBMS_Architectural_Analysis.md](docs/01_LDBMS_Architectural_Analysis.md), [docs/04_Deep_Component_Analysis.md](docs/04_Deep_Component_Analysis.md): longer design write-ups (partly outdated; this README is authoritative for setup)

---

## 👨‍💻 Author

**Shibil Ahamed**. Licensed under the terms in [LICENSE](LICENSE).
