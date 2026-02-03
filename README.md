# 📚 Enterprise Library Database Management System (LDBMS)

> **The Ultimate "Mega Project" Evolution** - A high-performance, AI-augmented, and gamified Library Management Ecosystem. Built with a "Golden Ratio" design philosophy and powered by Google Gemini 1.5.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini_1.5_Flash-purple.svg)](https://deepmind.google/technologies/gemini/)
[![Gamified](https://img.shields.io/badge/Gamification-Active-gold.svg)](#-gamification-system)

---

## 🌟 The "Mega Project" Milestone

The LDBMS has evolved from a standard management tool into an enterprise-grade platform. Featuring **33 modular features**, it now combines traditional library science with cutting-edge AI and behavioral design.

### ✨ Enterprise Core Highlights
- 🧠 **AI-First Discovery**: Semantic search and "Vibe" matching powered by Gemini 1.5.
- 🎮 **Gamified Retention**: XP systems, level-ups, and badges for active readers.
- 💎 **Dynamic Tiering**: Silver, Gold, and Platinum membership with intelligent privilege enforcement.
- 📊 **Real-time Analytics**: Interactive Chart.js dashboards and automated PDF reporting.
- 🏗️ **Smart Inventory**: ISBN Auto-Hydration for zero-effort catalog expansion.

---

## 🚀 Feature Set (33 Core Capabilities)

### 🧠 Artificial Intelligence & Search
- **AI Librarian Chatbot**: Conversational assistant for citations and general help.
- **"Vibe" & Mood Discovery**: Find books by describing a mood (e.g., "dark and rainy").
- **Smart Recommendations**: Personalized "Recommended for You" engine based on user history.
- **ISBN Auto-Hydrator**: Fetch metadata (Title, Author, Cover) via global APIs (OpenLibrary/Google Books).

### 🎮 Gamification & Community
- **XP & Leveling System**: Earn experience for borrowing and returning on time.
- **Achievement Gallery**: Unlock badges like "First Bloom" or "Scholar" for library milestones.
- **Personal Activity Feed**: A visual timeline of your literary journey.
- **Social Discovery**: Public profiles (optional) to see what fellow "Platinum" members are reading.

### 👑 Enterprise Administration
- **Automated Reporting**: Weekly PDF performance audits sent via scheduled email (APscheduler).
- **Advanced Analytics Dashboard**: Interactive trends, genre popularity, and usage heatmaps.
- **System Health Monitor**: Live diagnostics for DB latency, CPU load, and resource vitals.
- **Maintenance Mode**: One-click system lockdown for updates (Admin-exclusive access).
- **Bulk Data Management**: Import/Export capabilities for massive library catalogs.

### 📖 Classic Library Management
- **Circulation 2.0**: Atomic transactions for issuing/returning with tiered limits.
- **Waitlist & Reservations**: In-app and email notifications when high-demand books return.
- **Dynamic Fine Engine**: Category-specific fine rates and automated overdue reminders.
- **Waitlist Management**: First-come-first-served automated reservation clearing.
- **Rating & Reviews**: Social proofing and feedback for every book in the catalog.

---

## 🏗️ Technical Architecture

### 📁 Project Structure (Evolution)
```
LDBMS/
├── backend/
│   ├── app.py                      # Application Factory
│   ├── scheduler.py                # Background job engine (PDFs/Reminders)
│   ├── config/                     # Multi-environment configuration
│   ├── repository/                 # Atomic Data Access Layer (ACID)
│   ├── services/                   # Modular Business Logic (AI, Game, Issue, etc.)
│   │   ├── ai_service.py           # Gemini Integration
│   │   ├── discovery_service.py    # Mood-based Semantic Search
│   │   ├── health_service.py       # Diagnostic Vitals
│   │   └── report_service.py       # PDF/CSV Generation
│   └── routes/                     # Domain-driven blueprints (Admin, Member, System)
├── templates/                      # Responsive Glassmorphism UI (Jinja2)
├── static/                         # Assets & High-performance CSS
├── storage/                        # PDF E-books & Metadata Covers
├── mainCLI.py                      # Advanced Terminal Interface
└── run.py                          # Unified Entry Point
```

### 🧪 Tech Stack
- **Backend**: Flask 3.0, Apscheduler, FPDF2 (Reporting)
- **Database**: MySQL 8.0 (Optimized Connection Pooling)
- **AI Layer**: Google Generative AI (Gemini 1.5 Flash)
- **Frontend**: Vanilla CSS (Golden Ratio Design), JavaScript (ES6+), Chart.js
- **Tools**: Pandas (Data Processing), Requests (Metadata API)

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL 8.x
- Google Gemini API Key (Optional, for AI features)

### 1️⃣ Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Configuration
Create a `.env` file:
```env
DB_HOST=127.0.0.1
DB_NAME=library_db
DB_USER=root
DB_PASSWORD=your_password
GEMINI_API_KEY=your_key_here
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=app_password
```

### 3️⃣ Initialize Database
```bash
mysql -u root -p < database/schema_evolution.sql
python database/seed_mega.py
```

### 4️⃣ Execution
```bash
python run.py
```

---

## 👨‍💻 Author & Credits

**Shibil Ahamed**  
Built with the goal of redefining the "Library System" as a high-tech literary social hub.

Special thanks to the **Google Gemini Team** for providing the intelligence layer that powers our discovery engine.

---

<div align="center">

**⭐ Star the LDBMS if you want to revolutionize reading!**

Made with ❤️ using Flask, MySQL, and Artificial Intelligence

</div>
