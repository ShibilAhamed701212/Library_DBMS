# Audit and fixes (October 2026)

This records what the engineering audit found in the code before any change was made (the baseline), what was changed, and how each fix was verified. Each finding was reproduced against a running copy of the app on MariaDB 10.11 before it was fixed.

## Baseline findings

| # | Finding | Evidence (before) |
|---|---|---|
| 1 | Session cookies could be forged. `app.py` read `FLASK_SECRET_KEY` with a public fallback, `"dev-secret"`, while the README told users to set `SECRET_KEY`. | A cookie signed with `dev-secret` opened `/admin/users` as an admin. |
| 2 | Unauthenticated database reset. `GET /system/initialize-db-cloud-sync` accepted the public default token `default-dev-token`, truncated users/books and re-created `admin@library.com` / `Admin@123`. | Code review of `system_routes.py` and `seed_data.py`. |
| 3 | `/test/test/auth/check-users` (debug blueprint registered in production) returned every user's email and role without login. | HTTP 200 with the user list. |
| 4 | The email-verification OTP was stored in the Flask session cookie, which is signed but not encrypted. | Decoded the cookie, read the OTP and submitted it successfully. |
| 5 | Chat authorization gaps: any member could rename any channel; channel icons accepted any file type (e.g. `.html`, so stored XSS under `/static`). | Code review of `chat_routes.py`. |
| 5b | Found while fixing #5: any client (even one not logged in) could join any channel's Socket.IO room, including other people's DMs, and read its history and new messages. Any member could also invite themselves into any group or DM and accept their own invite, or answer other people's invites. | Code review of `socket_service.py` and the invite routes; covered by regression tests. |
| 6 | Clean install impossible. `requirements.txt` pinned a non-existent `scikit-learn==1.4.1.1`. `fpdf2`, `psutil`, `email-validator`, `chromadb`, `huggingface_hub`, `transformers` and `pyngrok` were imported but not declared, and the app would not start without `fpdf`. | `pip install -r requirements.txt` failed; `create_app()` raised `ModuleNotFoundError: fpdf`. |
| 7 | No deterministic schema. The base SQL created 5 of about 38 tables, the rest were spread over about 50 setup/migration scripts with conflicting definitions, and `dm_participants` / `chat_invitations` were created nowhere. | Fresh DB plus every setup script: `channels` table missing, chat unusable. |
| 8 | Seeding failed: `add_book` never set the NOT NULL `books.author` column. The same bug broke adding a book on a fresh database. | `seed_data.py` raised `1364 Field 'author' doesn't have a default value`. |
| 9 | Several queries referenced columns the schema did not have (`series.name`, `reading_goals.goal_books/current_books`, `books.created_at`, `authors.nationality`, `badges.rule_type`, `book_suggestions.reason`, `books.copies`, `users.join_date`). | 7 member/admin pages returned HTTP 500 on a fresh install; EXPLAIN of every query reported 22 unknown tables or columns. |
| 10 | Admin "add book" without a PDF raised `NameError` (`pdf_src` undefined), and the e-book upload directory was never created. | Code review; covered by a regression test. |
| 11 | The README referenced files that do not exist (`schema_evolution.sql`, `seed_mega.py`), the wrong secret and email variables (`SECRET_KEY`, `MAIL_*` instead of `FLASK_SECRET_KEY`, `SMTP_*`), and Flask 3.0 (actual pin: 2.3.3). | Repository tree, `app.py`, `email_service.py`. |
| 12 | Committed runtime artifacts: 66 MB of user uploads (avatars, chat images, a PDF), generated CSV exports containing user names, the ChromaDB vector store (rewritten on every start), and a stray `null` file containing PowerShell error output. | `git ls-files`. |

## Fixes

| # | Change | Files |
|---|---|---|
| 1 | Use `FLASK_SECRET_KEY` (or `SECRET_KEY`). Without either, generate a random per-process key and log a warning. | `backend/app.py` |
| 2 | Reset route returns 404 unless a dedicated `DB_INIT_TOKEN` is set, and compares tokens in constant time. The Flask secret is no longer accepted. Seeded accounts use `SEED_ADMIN_PASSWORD` or a random printed password. The hard-coded `App@123` DB password fallback was removed. | `backend/routes/system_routes.py`, `database/seed_data.py`, `backend/config/db.py` |
| 3 | Debug user-listing blueprint is no longer registered. | `backend/app.py` |
| 4 | Session stores only an HMAC of the OTP, keyed with the app secret. OTP comes from `secrets`, expires after 10 minutes, and allows 5 failed attempts per email, counted server-side so replaying an old cookie does not reset the count; a code cannot be reused after it succeeds. | `backend/routes/public_routes.py` |
| 5, 5b | Added `can_access_channel()` (public, participant, guild member, or site admin for non-DM channels) and enforced it on Socket.IO join/send and on the REST message history. Channel rename uses the same rule as channel settings/rules. Channel icons must be png/jpg/gif/webp. Group invites require access to the channel. Only the invitee (or the guild owner) can answer a pending invite. | `backend/services/channel_service.py`, `backend/chat/socket_service.py`, `backend/routes/chat_routes.py` |
| 6 | Fixed the scikit-learn pin; declared every imported runtime package with the versions that resolved together; added `requirements-dev.txt` (pytest). | `requirements.txt`, `requirements-dev.txt` |
| 7, 9 | New `database/schema.sql`: one complete, idempotent schema plus reference data (settings, membership tiers, category fines, badges, Global Community channel). It was built from the setup/migration scripts and reconciled with every query in `backend/`. `init_db.py` loads it and now fails loudly. Where a query was clearly wrong against the original schema, the query was fixed instead (`book_suggestions.notes`, `books.total_copies`, `users.created_at`). | `database/schema.sql`, `database/init_db.py`, `backend/routes/admin_routes.py`, `backend/services/bulk_service.py`, `backend/services/gamification_service.py` |
| 8 | `add_book` / `update_book` fill `books.author` from the selected author. | `backend/services/book_service.py` |
| 10 | Initialise `pdf_src`, require `.pdf`, and create the e-books directory. Added the `X-Content-Type-Options: nosniff` header. | `backend/routes/admin_routes.py`, `backend/app.py` |
| 11 | README rewritten against the code; deployment guide updated; outdated design docs flagged. | `README.md`, `docs/02_Deployment_Guide.md`, `docs/01_*.md`, `docs/04_*.md` |
| 12 | Untracked `static/uploads/`, `exports/` and `backend/brain/data/` (now git-ignored, with `.gitkeep` placeholders for the upload folders); deleted `null`. | `.gitignore` |

## Validation

- **Regression tests** (`tests/test_security.py`, `tests/test_books.py`): 47 tests. Run against the pre-fix code, every test that targets a fixed issue fails (the remaining few check behaviour that was already correct); against the fixed code, all pass.
- **Fresh install** (`tests/test_fresh_install.py`, against an empty MariaDB 10.11 database, using a virtualenv built only from `requirements.txt`):
  - `init_db` succeeds twice in a row (idempotent).
  - `seed_data` creates 4 users and 30 books, all with an author.
  - All 301 static SQL statements in `backend/` pass `EXPLAIN` against the schema, apart from two unused legacy modules and one try/except-guarded optional table.
  - Every parameterless GET page loads without a 5xx error, as admin and as member.
- **Smoke test**: `gunicorn run:app` and `python run.py` both serve `/` and `/login`. The seeded admin can log in and open `/dashboard`. The Socket.IO handshake answers. `/system/initialize-db-cloud-sync?token=default-dev-token` and `/test/test/auth/check-users` both return 404.

## Remaining known issues (not changed)

- No CSRF protection; the session cookie relies on the browser's default `SameSite` behaviour.
- Any member can join a non-DM group by channel ID (`POST /chat/join/<id>`); the code documents this as intended.
- `/admin/support/<id>` and the member ticket page return 500 for an unknown ticket ID.
- A second `POST /chat/upload` handler in `chat_routes.py` is shadowed by the first and never runs.
- AI features (Gemini `gemini-1.5-flash`, Hugging Face inference, local model download) could not be exercised offline.
- The schema was verified on MariaDB 10.11 only.
- Screenshots were not captured: the UI's CSS, fonts and charts load from public CDNs that were unreachable in the verification environment.

## Manual steps for existing deployments

1. **Back up `static/uploads/`, `exports/` and `backend/brain/data/` before pulling.** They are no longer tracked, so pulling this change removes the previously committed copies from a git-based checkout.
2. Set `FLASK_SECRET_KEY` explicitly if it is not set already (sessions are invalidated once).
3. Existing databases: `python database/init_db.py` only creates missing tables. It does **not** alter existing ones. If an existing database was built from the old scripts, compare it with `database/schema.sql`, especially `series.name`, `reading_goals.goal_books/current_books`, `books.created_at`, `authors.nationality`, `badges.rule_type/rule_value`, `chat_messages`, `dm_participants`, `chat_invitations` and `audit_logs`.
4. `/system/initialize-db-cloud-sync` now needs `DB_INIT_TOKEN`. Leave it unset except for a one-time bootstrap.
5. Seeded demo accounts no longer use `Admin@123`. Change the password of any production account that still uses it.
