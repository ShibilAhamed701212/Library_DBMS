# 🛠️ LDBMS Technical Architecture & Documentation

This document provides a deep dive into the engineering choices, architectural patterns, and technology stack powering the Enterprise Library Database Management System.

---

## 1. 🏗️ High-Level Architecture

The system follows a **Layered Monolithic Architecture** with clear separation of concerns using the **Service-Repository Pattern**.

```mermaid
graph TD
    User[User / Client] -->|HTTP Requests| Nginx[Ngrok / Web Server]
    User -->|WebSocket| Socket[Socket.IO Server]
    
    Nginx --> Routes[Flask Blueprints (presentation)]
    Socket --> Events[Socket Event Handlers]
    
    Routes --> Services[Service Layer (Business Logic)]
    Events --> Services
    
    Services --> Repository[Repository Layer (Data Access)]
    Services --> AI[Gemini AI Client]
    
    Repository --> DB[(MySQL Database)]
```

### Core Design Principles
1.  **Separation of Concerns**: Routes only handle HTTP; Services handle logic; Repositories handle SQL.
2.  **Centralized Data Access**: All database interactions go through `backend/repository/db_access.py`.
3.  **Real-Time Hybrid**: Uses HTTP for standard actions and WebSockets for Chat/Notifications.

---

## 2. 💻 Integrated Technology Stack

### Backend Core
-   **Framework**: **Flask 3.0** (Python Microframework).
-   **Runtime**: **Python 3.10+**.
-   **Concurrency**: **Eventlet/Gevent** (via Flask-SocketIO) for async operations.
-   **Task Scheduling**: **APScheduler** for background jobs (PDF reports, fine calculation).

### Database & Storage
-   **RDBMS**: **MySQL 8.0** with ACID compliance.
-   **Connection Pooling**: Custom managed pool in `backend/config/db.py`.
-   **File Storage**: Local filesystem (`/storage`) for PDFs and user uploads.

### Real-Time Communication
-   **Protocol**: **Socket.IO** (WebSockets with polling fallback).
-   **Library**: `flask-socketio`.
-   **Features**: Bi-directional event emitting for Chat, Typing Indicators, and Live Notifications.

### Intelligence Layer (AI)
-   **Provider**: **Google Gemini 1.5 Flash**.
-   **Integration**: `google-generativeai` SDK.
-   **Use Cases**: Semantic book search ("Vibe" check), Chatbot assistance, Content generation.

### Frontend
-   **Templating**: **Jinja2** (Server-side rendering).
-   **Styling**: **Vanilla CSS3** with Custom Properties (Variables) for theming.
-   **Design System**: Glassmorphism UI with Golden Ratio typography.
-   **Interactivity**: **Vanilla JavaScript (ES6+)**. No heavy frameworks (React/Vue) to ensure lightweight performance.
-   **Visualization**: **Chart.js** for admin dashboards.

---

## 3. 📂 Project Structure & Key Files

The codebase is organized to support scalability and maintainability.

### Root Directory (`LDBMS/pythonProject`)
| File/Folder | Purpose |
| :--- | :--- |
| `run.py` | **Entry Point**. Initializes app, starts Ngrok, and runs SocketIO server. |
| `mainCLI.py` | **Admin CLI**. Terminal-based management tool for headless operations. |
| `requirements.txt` | Dependency manifest. |

### Backend (`backend/`)
| Directory | Description |
| :--- | :--- |
| **`app.py`** | **Application Factory**. Bootstraps Flask, registers Blueprints, initializes extensions. |
| **`routes/`** | **Presentation Layer**. Contains Blueprints (`auth_routes.py`, `chat_routes.py`). Handles request parsing and response formatting. |
| **`services/`** | **Business Layer**. The "Brain" of the app. Contains `chat_service.py` (logic), `ai_service.py` (Gemini), etc. |
| **`repository/`** | **Data Layer**. `db_access.py` is the **critical gateway** for all SQL execution. |
| **`config/`** | Configuration files (DB connection, logging, constants). |
| **`chat/`** | Specialized Socket.IO namespace handlers. |

---

## 4. 🧠 Code Flow & Patterns

### A. The Request Lifecycle (Standard HTTP)
Example: **User borrows a book**.

1.  **Route Layer** (`routes/issue_routes.py`):
    -   Receives `POST /issue/book/<id>`.
    -   Validates session (Is user logged in?).
    -   Calls `issue_service.issue_book(user_id, book_id)`.
2.  **Service Layer** (`services/issue_service.py`):
    -   Checks business rules: "Does user have unpaid fines?", "Is book available?".
    -   Calls `repository.execute()` to insert transaction record.
    -   Calls `repository.execute()` to update book stock.
3.  **Repository Layer** (`repository/db_access.py`):
    -   Gets a connection from the pool.
    -   Executes raw SQL: `INSERT INTO transactions ...`
    -   Commits transaction.
4.  **Database**:
    -   Persists data.

### B. The Real-Time Lifecycle (WebSocket)
Example: **User sends a chat message**.

1.  **Client**: Emits `send_message` event via JS.
2.  **Socket Handler** (`chat/socket_service.py`):
    -   Listens for `@socketio.on('send_message')`.
    -   Calls `chat_service.save_message()`.
3.  **Service Layer**:
    -   Sanitizes input.
    -   Saves to DB via Repository.
    -   Returns message object.
4.  **Socket Broadcaster**:
    -   `emit('receive_message', msg, room=room_id)` sends to all connected clients in that room.

---

## 5. 🔑 Key Component Deep Dive

### 🛡️ Repository Pattern (`db_access.py`)
Instead of using an ORM like SQLAlchemy, this project uses **Raw SQL** via a Repository pattern for maximum performance and control.
-   **`fetch_all(query, params)`**: Returns list of dicts.
-   **`fetch_one(query, params)`**: Returns single dict.
-   **`execute(query, params)`**: Handles INSERT/UPDATE/DELETE with auto-commit/rollback.

### 🤖 AI Service (`ai_service.py`)
Wraps the Google Gemini API.
-   **Function**: `get_book_recommendation(user_history)`.
-   **Logic**: Constructs a prompt with user's reading list -> Sends to Gemini -> Parses JSON response -> Returns book list.

### 💬 Chat Service (`chat_service.py`)
Handles complex social logic.
-   **Privacy**: Generates `anon_id` for anonymous mode.
-   **Room Management**: Logical grouping of users (Guilds vs DMs vs Public Channels).
-   **Security**: Verifies "Is user allowed in this room?" before every action.

---

## 6. 🌐 Frontend Architecture

The frontend is built on **Atomic Design Principles** using purely vanilla technologies.

-   **Templates**: Jinja2 inheritance (`layout.html` -> `base_dashboard.html` -> page).
-   **CSS**:
    -   Global Variables: Defined in `root` (colors, spacing).
    -   Glassmorphism: Extensive use of `backdrop-filter: blur()` and `rgba` alpha channels.
    -   Responsiveness: CSS Grid and Flexbox with `@media` breakpoints for mobile.
-   **JavaScript**:
    -   `socket.io.js` client logic.
    -   `fetch` API for async AJAX calls without page reloads.

---
*Generated by Agent Antigravity for User Documentation*
