# 🍉 Career Learning Vault — Full-Stack Cloud Web Hub

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Abhishek-Gali/career-learning-vault-web)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Watermelon UI](https://img.shields.io/badge/Design-Watermelon%20UI-10B981?style=for-the-badge)
![Keep-Alive](https://img.shields.io/badge/Keep--Alive-24%2F7%20Zero%20Sleep-38BDF8?style=for-the-badge)
![Challenges](https://img.shields.io/badge/Challenges-312%20Fleet-F43F5E?style=for-the-badge)

A high-performance full-stack web application designed for developer interview readiness and algorithm mastery. Featuring **Refero Design** (`styles.refero.design`) combined with **Watermelon UI** glassmorphism, an **Activity-Gated Daily 2-Hour Focus Timer**, **312 curated coding challenges across 10 platforms**, and a **24/7 Zero-Cost Keep-Alive Architecture** via Render.com and cron-job.org.

---

## 🌟 Key Features

### 1. 🍉 Watermelon UI & Refero Design System
- **Obsidian Dark Canvas**: `#090d16` with ambient radial mesh glow.
- **Glassmorphic Elevations**: `backdrop-filter: blur(16px)` with delicate borders and emerald/coral neon accents.
- **Celebratory Confetti**: Interactive particle explosion triggered on 100% test suite completion.

### 2. ⏱️ Activity-Gated Focus Timer (Smart Auto-Pause)
- Tracks daily 2-hour study goals (`02:00:00`).
- Listens to active user interactions (keystrokes, mouse moves, clicks, scrolls).
- **Auto-Pauses (`⏸ IDLE`)** if no activity for 2 minutes to prevent fake study credit.
- Flushes active seconds to SQLite (`/api/timer/sync`) every 30 seconds and caches in `localStorage`.

### 3. 🚀 10-Platform Coding Sandbox (312 Challenges)
- Curated challenges categorized by difficulty (Easy, Medium, Hard) across 10 major platforms:
  - **Placement Preparation** (30 Qs)
  - **GUVI – CodeKata** (30 Qs)
  - **HackerRank** (30 Qs)
  - **LeetCode** (30 Qs)
  - **GeeksforGeeks** (30 Qs)
  - **Codewars** (30 Qs)
  - **HackerEarth** (30 Qs)
  - **CodeChef** (30 Qs)
  - **Programiz** (30 Qs)
  - **W3Schools** (30 Qs)
  - **Foundational DSA Core** (12 Qs)
- **3.0-Second Isolated Subprocess Runner** with detailed input/expected/got test diffs and execution telemetry.

### 4. 🎯 Level-Based Technical Interview Drills
- 14 Comprehensive question banks covering:
  - **Cyber Security**: ISC2 Certified in Cybersecurity (CC) Domains 1–5.
  - **Data Science**: Levels 1–3 (Foundations, Intermediate, Advanced).
  - **Machine Learning**: Levels 1–3 (Foundations, Intermediate, Advanced).
  - **Data Structures & Algorithms**: Levels 1–3.
- Option-by-option pedagogical rationales explaining why each answer is correct or incorrect.

### 5. 🗺️ NeetCode 150 / Blind 75 Roadmap & Big-O Cheat Sheet
- Topic-wise algorithmic breakdowns (Arrays, Two Pointers, Sliding Window, Trees, Graphs, DP).
- Python 3 complexity matrix (Lists, Dicts, Sets, Deques).

---

## ⚡ 24/7 Zero-Cost Keep-Alive Architecture

Render.com free tier services spin down after 15 minutes of inactivity. With **cron-job.org**:

```
[ cron-job.org ] ──────(GET /api/health every 10 min)─────► [ Render Web Service ]
                                                                   │
                                                    • Response time: <40ms
                                                    • 100% Free ($0)
                                                    • Zero Credit Card Required
                                                    • 24/7/365 Zero Sleep (Always Awake)
```

1. Pinging `/api/health` every 10 minutes keeps the server awake permanently.
2. Zero cold starts: every page load and sandbox test execution responds instantly.

---

## 🚀 1-Click Deployment to Render.com

1. Click the **Deploy to Render** button above or go to [render.com](https://render.com).
2. Create a **New Web Service** connected to `https://github.com/Abhishek-Gali/career-learning-vault-web`.
3. Configuration:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free ($0 / month — No credit card required)
4. Add a job on [cron-job.org](https://console.cron-job.org/jobs):
   - **URL**: `https://<your-render-app>.onrender.com/api/health`
   - **Interval**: Every 10 minutes (`*/10 * * * *`)

---

## 💻 Running Locally

```bash
# Clone the repository
git clone https://github.com/Abhishek-Gali/career-learning-vault-web.git
cd career-learning-vault-web

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
Or simply double-click `run_web_app.bat` on Windows!
