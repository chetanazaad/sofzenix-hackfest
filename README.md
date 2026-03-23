# ⚡ SkilStation Summer Hackathon 2026

Welcome to the **SkilStation Summer Hackathon** Registration & Management Platform! This project is a complete end-to-end event management platform designed for the 2026 National Level Online Summer Hackathon.

It allows users to register, form teams, and manage their participation, while an Admin Dashboard gives full control over verifying participants, coordinating via WhatsApp, and managing the event lifecycle.

---

## 🎯 Features & How It Works

### For Participants:
1. **Registration & Payment:** Users fill out a responsive registration form. Participation fees (₹99 for individuals, ₹349 for teams) are paid via provided payment links, and users upload transaction screenshots for verification.
2. **Team Formation:** Support for individual or team (up to 4 members) registrations.
3. **Automated Confirmation:** Once verified by an admin, users receive a personalized WhatsApp notification with their login credentials and event details.
4. **Referral Perks:** (Optional) Users can share their referral codes to earn incentives.

### For Admins:
1. **Participant Verification:** View registrations and verify/reject payment proof in real-time.
2. **WhatsApp Automation:** Integrated one-click WhatsApp API to send confirmation messages (Email/Login ID, Password note, and Referral links) directly to participants.
3. **Reward Management:** System for generating and dispatching digital scratch card rewards to winners or through referral milestones.
4. **Leaderboard & Evaluation:** Tools for judges to score teams based on Innovation and Design.

---

## 🛠 Tech Stack

*   **Frontend:** Pure HTML5, Modern CSS (Cyberpunk/Futuristic Theme), Vanilla JavaScript, GSAP (Animations), and tsParticles.
*   **Backend:** Python 3.14+ utilizing Flask and SQLAlchemy (ORM).
*   **Database:** MySQL-compatible (Local XAMPP or Cloud TiDB Serverless).

---

## 🚀 Installation & Deployment Options

### Option 1: All Local (Development Mode)
1. **Database:** Install XAMPP and start MySQL. Create a database named `sofzenix_hackfest`.
2. **Backend Config:** In `backend/.env`, set `DATABASE_URL` to your local MySQL connection.
3. **Start Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
4. **Start Frontend:** Use "Live Server" on the `frontend/` folder. Ensure `frontend/js/config.js` points to `http://127.0.0.1:5000`.

---

### Option 2: Full Production Deployment (Render + TiDB)
1. **Database:** Setup a free **TiDB Serverless** cluster.
2. **Backend Config:** In Render dash, set `DATABASE_URL` with your TiDB connection string and `ALLOWED_ORIGIN` to your domain. 
3. **Frontend Config:** Update `frontend/js/config.js` to point to your Render `onrender.com` URL.
4. **Deploy:** Push code to GitHub. Render will auto-build using `pip install` and start using `gunicorn`.

---

## 📅 Event Timeline (2026)
*   **Registration:** March 23 – April 27
*   **Prelims (Online):** May 6
*   **Grand Finale:** May 14 & 15

## 🔒 Security
*   **Data Integrity:** Passwords hashed with `Bcrypt`.
*   **Image Storage:** Screenshots stored as `MEDIUMTEXT` (Base64) to avoid external storage dependencies.
*   **CORS Protection:** API restricted to verified domains via `ALLOWED_ORIGIN`.

---
Copyright © 2026 **SkilStation / Sofzenix IT Solution LLP**
