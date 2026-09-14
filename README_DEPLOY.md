# 🍉 Career Learning Vault — Render.com 24/7 Free Deployment Guide

This guide walks you through deploying the **Career Learning Vault** web app to **Render.com** for **$0 (Zero Credit Card Required)** and keeping it active **24/7/365** with **cron-job.org**.

---

## ⚡ Architecture Summary

```
   [ cron-job.org ] 
          │  (Pings /api/health every 10 min)
          ▼
   [ Render.com Free Web Service ] ──────► [ FastAPI + Python 3.13 Subprocess Sandbox ]
          │                                  ├── 312 Coding Challenges (10 Platforms)
          │                                  ├── Activity-Gated Focus Timer (2h Daily Goal)
          │                                  └── Technical Interview Engine (14 Sets)
          ▼
   [ User Browser (Refero & Watermelon UI) ]
```

- **Render Free Tier**: Spins down after 15 minutes of inactivity.
- **Your Cron Job (`cron-job.org`)**: Sends an HTTP `GET` to `/api/health` every **10 minutes**.
- **Outcome**: The instance **NEVER** sleeps! Response time is `<80ms` around the clock, with **zero credit card** and **zero subscription fees**.

---

## 🚀 Step 1: Push Web App to GitHub (2 Minutes)

1. Open your terminal in `D:\Career_Learning_Vault\web_app`:
   ```bash
   cd D:\Career_Learning_Vault\web_app
   git init
   git add .
   git commit -m "Initial commit: Career Learning Vault Web App"
   ```
2. Create a new repository on [GitHub](https://github.com/new) named `career-learning-vault-web`.
3. Push your code:
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/career-learning-vault-web.git
   git branch -M main
   git push -u origin main
   ```

---

## 🌐 Step 2: Deploy on Render.com (100% Free, No Credit Card)

1. Go to [https://render.com](https://render.com) and sign in with your GitHub account.
2. Click **New +** in the top right and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and click **Next**.
4. Select your `career-learning-vault-web` repository.
5. Fill in the deployment settings:
   - **Name**: `career-learning-vault` (or any custom name)
   - **Region**: Closest to you (e.g., Singapore, Frankfurt, Ohio)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free** ($0 / month — No credit card required!)
6. Click **Deploy Web Service**!
7. Within 90 seconds, your site will be live at:
   `https://career-learning-vault.onrender.com`

---

## ⏰ Step 3: Set Up 24/7 Keep-Alive on cron-job.org

1. Open your [cron-job.org Console](https://console.cron-job.org/jobs) (as configured in your dashboard).
2. Click **CREATE CRONJOB**.
3. Enter the configuration:
   - **Title**: `Career Vault 24/7 Keep-Alive`
   - **URL**: `https://<YOUR-RENDER-SUBDOMAIN>.onrender.com/api/health`
   - **Execution Schedule**: **Every 10 minutes** (`*/10 * * * *`)
   - **Request Method**: `GET`
4. Click **CREATE**.

---

## 🧪 Local Testing Before Deploying

You can also run the web app locally on your computer at any time:
1. Double-click `D:\Career_Learning_Vault\web_app\run_web_app.bat`.
2. Open your browser to `http://127.0.0.1:8000`.
