# 📚 Enterprise Library Database Management System (LDBMS)

> **The Ultimate "Mega Project" Evolution** - A high-performance, AI-augmented, and gamified Library Management Ecosystem. Built with a "Golden Ratio" design philosophy and powered by Google Gemini 1.5.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini_1.5_Flash-purple.svg)](https://deepmind.google/technologies/gemini/)
[![Gamified](https://img.shields.io/badge/Gamification-Active-gold.svg)](#-gamification-system)
[![Real-Time](https://img.shields.io/badge/Real--Time-Socket.IO-orange.svg)](https://socket.io/)

---

## 🌟 The "Mega Project" Milestone

The LDBMS has evolved from a standard management tool into an enterprise-grade platform. Featuring **over 35 modular features**, it now combines traditional library science with cutting-edge AI, behavioral design, and real-time social interaction.

### ✨ Enterprise Core Highlights
- 🧠 **AI-First Discovery**: Semantic search and "Vibe" matching powered by Gemini 1.5.
- 💬 **Social Hub**: Real-time chat, guilds, and community interaction.
- 🎮 **Gamified Retention**: XP systems, level-ups, and badges for active readers.
- 📱 **Mobile-First Premium UI**: Fully responsive, touch-optimized design with glassmorphism aesthetics.
- 💎 **Dynamic Tiering**: Silver, Gold, and Platinum membership with intelligent privilege enforcement.
- 📊 **Real-time Analytics**: Interactive Chart.js dashboards and automated PDF reporting.
- 🏗️ **Smart Inventory**: ISBN Auto-Hydration for zero-effort catalog expansion.

---

## 🚀 Feature Set

### 💬 Real-Time Collaboration & Social Hub [NEW]
- **Channels & DMs**: Seamless real-time messaging with individual users or topic-based channels.
- **Guilds & Communities**: Join interest-based guilds (e.g., "Sci-Fi Lovers") with role-based access (Admin/Moderator).
- **Rich Media Support**: Share files and images with instant previews; typing indicators and read receipts.
- **Privacy First**: Anonymous chat mode for discreet discussions and granular profile privacy toggles.
- **Connections Hub**: Manage friend requests and view pending invitations in a centralized dashboard.

### 🧠 Artificial Intelligence & Search
- **AI Librarian Chatbot**: Conversational assistant for citations and general help.
- **"Vibe" & Mood Discovery**: Find books by describing a mood (e.g., "dark and rainy").
- **Smart Recommendations**: Personalized "Recommended for You" engine based on user history.
- **ISBN Auto-Hydrator**: Fetch metadata (Title, Author, Cover) via global APIs (OpenLibrary/Google Books).

### 📱 User Experience & Interface
- **Premium Glassmorphism Design**: Modern, translucent UI with vibrant gradients and golden-ratio typography.
- **Mobile-Adaptive Layouts**: Collapsible sidebars, touch-friendly tables, and optimized headers for phones/tablets.
- **Interactive Visuals**: Smooth transitions, hover effects, and micro-animations for a "living" interface feeling.

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

### 📁 Project Structure
```
LDBMS/
├── backend/
│   ├── app.py                      # Application Factory & SocketIO Init
│   ├── scheduler.py                # Background job engine
│   ├── socket_events.py            # Real-time Event Handlers
│   ├── config/                     # Environment & Logging Config
│   ├── repository/                 # Data Access Layer (DAL)
│   ├── services/                   # Business Logic (AI, Chat, Guilds, etc.)
│   │   ├── ai_service.py           # Gemini Integration
│   │   ├── chat_service.py         # Real-time Messaging Logic
│   │   ├── guild_service.py        # Community Management
│   │   └── ... (30+ services)
│   └── routes/                     # Blueprints (Admin, Chat, Member, System)
├── templates/                      # Jinja2 Layouts (Responsive/Glassmorphism)
│   ├── chat/                       # Chat & Guild Interfaces
│   ├── admin/                      # Management Dashboards
│   └── ...
├── static/                         # Compiled CSS, JS Bundles, Assets
├── storage/                        # Uploaded Files & Generated Reports
├── mainCLI.py                      # Admin Terminal Interface
├── run.py                          # Entry Point (Flask + SocketIO + Ngrok)
└── requirements.txt                # Project Dependencies
```

### 🧪 Tech Stack
- **Backend**: Flask 3.0, Flask-SocketIO (Real-time), Apscheduler
- **Database**: MySQL 8.0 (Pooled Connections)
- **AI Layer**: Google Generative AI (Gemini 1.5 Flash)
- **Frontend**: Vanilla CSS (Modern Variables), JavaScript (ES6+), Chart.js
- **Tools**: Pandas, FPDF2, PyNgrok (Tunneling)

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL 8.x
- Google Gemini API Key (Optional)

### 1️⃣ Environment Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2️⃣ Configuration
Create a `.env` file in the root directory:
```env
DB_HOST=127.0.0.1
DB_NAME=library_db
DB_USER=root
DB_PASSWORD=your_password
GEMINI_API_KEY=your_key_here
SECRET_KEY=your_secret_key
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
*The application will launch with a local URL and an optional public Ngrok URL.*

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
