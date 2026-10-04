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
    - `FLASK_SECRET_KEY`: a long random value, e.g. the output of `python -c "import secrets; print(secrets.token_hex(32))"`. Required: without it every restart logs everyone out.
    - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`: needed for account-request OTP emails and reminders.
    - `DB_AUTH_PLUGIN`: set to `caching_sha2_password` if your MySQL user does not use `mysql_native_password`.

6.  Click **Create Web Service**.

## 5️⃣ Initialize the Database (One-time)

Once the app is live, open the **Shell** tab on Render and create the schema:
```bash
python database/init_db.py
```

Optionally load the demo data (30 books plus demo accounts). **This deletes existing users and books**, so only do it on an empty database:
```bash
SEED_ADMIN_PASSWORD='pick-a-password' python database/seed_data.py
```

If your host has no shell, set a long random `DB_INIT_TOKEN` environment variable, open
`https://<your-app>/system/initialize-db-cloud-sync?token=<DB_INIT_TOKEN>` once (it runs the schema **and** the destructive seed), then remove `DB_INIT_TOKEN`. The route returns 404 whenever `DB_INIT_TOKEN` is unset.

> Uploaded files (`static/uploads/`) are stored on the local disk, which is ephemeral on Render's free tier. Attach a persistent disk if avatars, chat files and e-books must survive redeploys.

---

**✅ Your app is now live at `https://library-system.onrender.com`!**
