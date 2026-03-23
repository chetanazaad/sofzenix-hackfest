# Project Overview: Sofzenix HackFest 2026

## 🚀 Status: COMPLETE & STABLE 🏁
A high-end, futuristic hackathon management platform built for the 2026 National Edition.

---

## 🎨 Design & Branding
*   **Theme:** "Beyond Limits" — Pitch Black backgrounds with // Golden Yellow and // Neon Cyan accents.
*   **Visuals:** 
    *   Dynamic Digital Grid background animation.
    *   Neon glow hover effects on all interactive cards.
    *   Entrance "Fade Up" animations for a premium load experience.
*   **Cohesive Identity:** Unified styling across Home, Register, Login, and all Dashboard portals using `main.css`.

---

## 🔐 Advanced Authentication System
To ensure maximum stability across Render (Frontend) and Ngrok (Local Backend), we implemented a **Modern Token System**:
1.  **Triple-Tab Login:** Clean separation between // Participant, // Evaluator, and // Administrator on the same login page.
2.  **Session Persistence:** Instead of traditional cookies, we use `localStorage` for `auth_token`. This bypasses Chrome’s 3rd-party cookie restrictions entirely.
3.  **Cross-Origin Reliability:** Backend uses `Flask-CORS` with explicit `Allow-Header: Authorization`.
4.  **Google OAuth:** Fully functional "Sign-In with Google" that automatically registers and logs in participants.

---

## 📊 Feature-Rich Dashboards

### 👥 Participant Dashboard
*   **Overview Module:** Real-time account status and referral count.
*   **Submission Portal:** Team-specific project link and tech stack uploader.
*   **Referral Rewards:** Unique referral link generator with instant "Copy to Clipboard" functionality.
*   **Profile Settings:** Integrated module to view and update user credentials.

### ⚖️ Evaluator Portal
*   **Judging Queue:** Dedicated interface for judges to score Innovation and Design (0-50 scaling).
*   **Final Rankings:** Live leaderboard view reflecting the latest judge evaluations.
*   **Account Settings:** Specialized portal for judging credentials management.

### 🛡️ Administrator Panel
*   **Unified Control:** Centralized management of over 200+ participants with search/filter.
*   **Evaluation Results:** Real-time visibility into judge scoring and overall standings.
*   **Reward Distribution:** Scratch-card generation and link dispatch via the "Dispatch Cards" module.
*   **System Configuration:** Dynamic toggle for "Maintenance Mode" and "Dev/Live" payment settings.

---

## 🛠️ Deployment & Maintenance

### 🔗 Current Cloud Configuration
*   **Frontend:** Hosted on Render ([https://sofzenix-hackfest.onrender.com](https://sofzenix-hackfest.onrender.com)).
*   **Backend:** Local machine via Ngrok ([https://0a1e-2405-201-6040-b8df-815c-d3f2-590b-7f46.ngrok-free.app](https://0a1e-2405-201-6040-b8df-815c-d3f2-590b-7f46.ngrok-free.app)).
*   **Database:** Standard Local SQL DB.

### 🔄 How to restart the system:
1.  Launch Backend: `python app.py` (Ensure `.env` is populated).
2.  Launch Tunnel: `.\ngrok.exe http 5000`.
3.  Update URL: If the Ngrok URL changes, update `frontend/js/config.js` and push to Git.
4.  **Visit Site:** Always click the "Visit Site" button on the Ngrok warning page in Chrome before logging in.

---
**Report Generated: March 22, 2026** 🛡️✨
