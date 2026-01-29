# 📚 Library Management System

> A modern, full-stack Library Management System built with Flask, MySQL, and Python featuring a responsive golden-ratio UI, CLI interface, and comprehensive analytics.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Overview

A production-ready library management system with dual interfaces (Web + CLI), role-based access control, and advanced analytics. Built following clean architecture principles with separation of concerns and industry-grade design patterns.

### ✨ Key Highlights

- 🎨 **Modern UI**: Golden ratio design system with responsive layout
- 🔐 **Secure Authentication**: Bcrypt password hashing with session management
- 👥 **Role-Based Access**: Separate admin and member capabilities
- 📊 **Advanced Analytics**: Pandas-powered reports and insights
- 🖥️ **Dual Interface**: Web dashboard + CLI application
- 🏗️ **Clean Architecture**: Layered design with reusable services

## 🚀 Features

### 🔐 Authentication & Security
- Secure password hashing using **bcrypt**
- Forced password change on first login
- Session-based authentication
- Role-based access control (Admin/Member)

### 👑 Admin Capabilities
- **Dashboard**: Real-time statistics and metrics
- **User Management**: Add, view, and delete users
- **Book Management**: Add, view, and delete books
- **Circulation**: Issue and return books with fine calculation
- **Analytics**: Generate comprehensive reports
- **Export**: Download reports as CSV/Excel

### 👤 Member Capabilities
- View issued books and borrowing history
- Track return status and outstanding fines
- Browse available books catalog
- Request new books

### 📊 Analytics & Reports (Powered by Pandas)
- **Search & Filter**: By title, author, category, availability
- **Reports**:
  - Most issued books
  - Most active users
  - Monthly issue trends
  - Overdue books analysis
- **Export**: CSV and Excel formats

### 🖥️ CLI Application
- Secure terminal-based login
- Full admin and member functionality
- Pandas-powered analytics in terminal
- Cross-platform password input (Windows/Linux/Mac)

## 🏗️ Architecture

### Project Structure

```
pythonProject/
├── backend/
│   ├── app.py                      # Flask app factory
│   ├── config/
│   │   ├── db.py                   # Database connection
│   │   └── settings.py             # Central configuration
│   ├── repository/
│   │   └── db_access.py            # Raw DB operations (CRUD)
│   ├── services/
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── user_service.py         # User management
│   │   ├── book_service.py         # Book management
│   │   ├── issue_service.py        # Issue/return logic
│   │   ├── analytics_service.py    # Data analysis
│   │   └── report_service.py       # Report generation
│   ├── routes/
│   │   ├── auth_routes.py          # Auth endpoints
│   │   ├── admin_routes.py         # Admin endpoints
│   │   └── member_routes.py        # Member endpoints
│   └── utils/
│       ├── decorators.py           # Custom decorators
│       └── security.py             # Security utilities
├── templates/                      # Jinja2 HTML templates
├── static/
│   └── css/
│       └── style.css               # Golden ratio design system
├── database/
│   ├── schema.sql                  # Database schema
│   └── seed_data.py                # Initial data seeding
├── mainCLI.py                      # CLI application
├── run.py                          # Flask entry point
├── .env                            # Environment variables
└── requirements.txt                # Python dependencies
```

### Design Principles

- **Separation of Concerns**: Clear boundaries between layers
- **No SQL in Routes**: All database logic in repository layer
- **Reusable Services**: Shared business logic for Web & CLI
- **Transaction Safety**: ACID-compliant operations
- **Centralized Configuration**: Single source of truth

## 🗄️ Database Design

### Tables

| Table | Description |
|-------|-------------|
| `users` | User accounts and roles (admin/member) |
| `books` | Library inventory catalog |
| `issues` | Issue/return transaction history |

### Key Design Decisions

- **Immutable History**: Issue records are never deleted
- **Soft Returns**: Returning a book updates `return_date` field
- **Active Issues**: Identified by `WHERE return_date IS NULL`

**Benefits:**
- Complete audit trail
- Historical analytics
- Compliance and reporting

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### 1️⃣ Clone Repository

```bash
git clone <repository-url>
cd pythonProject
```

### 2️⃣ Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment

Create a `.env` file in the project root:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=library_db
DB_USER=app_user
DB_PASSWORD=App@123
FLASK_SECRET_KEY=your-super-secret-key-here
```

### 5️⃣ Setup Database

```bash
# Run schema in MySQL
mysql -u root -p < database/schema.sql

# Seed initial data
python database/seed_data.py
```

## ▶️ Running the Application

### 🌐 Web Application

```bash
python run.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

**Default Credentials:**
- Admin: `admin` / `admin123`
- Member: `member` / `member123`

### 🖥️ CLI Application

```bash
python mainCLI.py
```

Follow the interactive prompts to login and navigate menus.

## 🎨 UI Design System

The web interface follows **Golden Ratio (1.618:1)** design principles:

### Layout
- **Sidebar**: 38% of viewport (max 380px)
- **Content**: 62% with centered max-width of 1100px

### Spacing Scale (Golden Ratio)
- `8px` → Small gaps
- `13px` → Icon-to-text spacing
- `21px` → Card padding
- `34px` → Section spacing
- `55px` → Large gaps

### Typography Scale
- Body: 14-16px
- Headings: 23-26px
- Stats: 38-42px

### Responsive Breakpoints
- **Desktop**: 1000px+ (full golden ratio)
- **Tablet**: 768-999px (adjusted proportions)
- **Mobile**: <600px (hamburger menu, stacked layout)

## 🧪 Technologies Used

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.10+, Flask 3.0+ |
| **Database** | MySQL 8.0+, mysql-connector-python |
| **Security** | bcrypt, Flask sessions |
| **Analytics** | Pandas, openpyxl |
| **Frontend** | HTML5, CSS3, Jinja2 |
| **Design** | Golden Ratio UI System |

## 📊 Dashboard Metrics

| Metric | Description |
|--------|-------------|
| **Total Users** | Number of registered users in the system |
| **Total Books** | Number of books in the library catalog |
| **Active Issues** | Books currently issued (not yet returned) |

> **Note**: Returned books are not deleted, only marked with `return_date`. This maintains a complete transaction history.

## 🏆 Best Practices

✅ **Clean Architecture**: Layered design with clear separation  
✅ **No SQL in Routes**: Database logic isolated in repository  
✅ **Centralized Config**: Single source of truth for settings  
✅ **Reusable Services**: Shared logic between Web & CLI  
✅ **Transaction Safety**: ACID-compliant operations  
✅ **Security First**: Bcrypt hashing, session management  
✅ **Production Ready**: Error handling, logging, validation  

## 📝 API Endpoints

### Authentication
- `GET /` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - End session

### Admin Routes
- `GET /admin/dashboard` - Admin overview
- `GET /admin/books` - Book management
- `GET /admin/users` - User management
- `GET /admin/issues` - Issue/return interface
- `GET /reports` - Analytics dashboard

### Member Routes
- `GET /member/dashboard` - Member overview
- `GET /member/catalog` - Browse books

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Library Management System**  
Built as a DBMS + Backend Engineering project

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

Made with ❤️ using Flask, MySQL, and Python

</div>
