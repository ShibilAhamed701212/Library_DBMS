# 🚀 Deployment Guide: Render + GitHub

This guide walks you through deploying your Library Management System to **Render**.

## 1️⃣ Prepare your Code for GitHub

1.  **Initialize Git** (if not already done):
    Open your terminal in the `pythonProject` folder and run:
    ```bash
    git init
    ```
2.  **Add your files**:
    ```bash
    git add .
    ```
3.  **Commit your changes**:
    ```bash
    git commit -m "Prepare for deployment"
    ```

## 2️⃣ Create a GitHub Repository

1.  Go to [github.com/new](https://github.com/new).
2.  Name it `library-management-system`.
3.  Keep it **Public** (or Private if you have GitHub Pro).
4.  **Do NOT** initialize with README, .gitignore, or License.
5.  Follow the instructions on GitHub to **"push an existing repository from the command line"**:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/library-management-system.git
    git branch -M main
    git push -u origin main
    ```

## 3️⃣ Set up an External MySQL Database (Recommended)

Render's built-in database is PostgreSQL. Your app uses MySQL.
The easiest way is to use **Aiven** (Free tier available):

1.  Go to [aiven.io](https://aiven.io/) and create a free MySQL service.
2.  Get your Connection URI or separate Host, Port, User, Password details.

## 4️⃣ Deploy to Render

1.  Go to [dashboard.render.com](https://dashboard.render.com/).
2.  Click **New +** > **Web Service**.
3.  Connect your GitHub repository.
4.  **Configuration**:
    - **Name**: `library-system`
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `gunicorn run:app`
5.  **Add Environment Variables**:
    Click **Advanced** > **Add Environment Variable**:
    - `DB_HOST`: (From Aiven)
    - `DB_PORT`: `3306`
    - `DB_NAME`: `defaultdb`
    - `DB_USER`: `avnadmin`
    - `DB_PASSWORD`: (From Aiven)
    - `FLASK_SECRET_KEY`: (Something random like `super-secret-123`)

6.  Click **Create Web Service**.

## 5️⃣ Initialize Data (One-time)

Once the app is live, you need to run the seed script *once* to create your 30 books.
On Render, go to the **Shell** tab and run:
```bash
python database/seed_data.py
```

---

**✅ Your app is now live at `https://library-system.onrender.com`!**
