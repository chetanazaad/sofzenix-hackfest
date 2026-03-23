# ⚡ Sofzenix HackFest 2026

Welcome to the **Sofzenix HackFest** Registration & Reward Platform! This project is a complete end-to-end event management platform infused with a built-in gamified **Scratch Card Referral Engine**. 

It allows users to register, pay, and receive referral codes, while an Admin Dashboard gives full control over verifying participants, assigning scores, generating reward scratch cards, and approving prize disbursements.

---

## 🎯 Features & How It Works

### For Participants:
1. **Registration & Payment:** Users fill out a responsive registration form. Instead of instant payments, they click a Razorpay link, pay, and upload a screenshot of their transaction along with their Reference ID.
2. **Referral Program:** Upon registration, users get a unique Referral Code. If a friend registers using this code, the original user receives a digital Scratch Card.
3. **Scratch Cards:** Users log into their dashboard to view their earned cards. A realistic canvas-based scratch effect reveals a random monetary reward.
4. **Reward Claim:** Users claim their reward by submitting their UPI ID.

### For Admins:
1. **Participant Verification:** View all user details and approve/reject their submitted payment screenshots.
2. **WhatsApp Integration:** 1-click WhatsApp notification to inform verified users of their successful registration, login credentials, and referral code.
3. **Reward Management:** Generate new scratch cards manually or dispatch them in bulk to specific hackathon participants as prizes.
4. **Payment Processing:** View claimed rewards and process manual payouts to the users' provided UPI IDs.
5. **Database Controls:** Global settings for Dev Mode (mock payments), reward bounds (min/max values), and campaign wiping.

---

## 🛠 Tech Stack

*   **Frontend:** Pure HTML5, Vanilla JavaScript, and Custom CSS (Zero frameworks for maximum speed).
*   **Backend:** Python 3.14+ utilizing Flask and SQLAlchemy.
*   **Database:** MySQL (Local XAMPP or Cloud TiDB).

---

## 🚀 Installation & Deployment Options

You can deploy this application in several architectural setups depending on your needs. Below are the three main tracking methods:

### Option 1: All Local (Development Mode)
*Best for testing and building new features on your own machine.*

1. **Database:** Install XAMPP and start MySQL. Create a database named `sofzenix_hackfest`.
2. **Backend Config:** Go to `backend/.env` and ensure the `DATABASE_URL` is set to your local DB or the variables point to `root` with no password. Set `ALLOWED_ORIGIN=http://127.0.0.1:5500`.
3. **Start Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
   *The Flask API is now running on port 5000.*
4. **Start Frontend:** Use VS Code's "Live Server" extension to open the `frontend/` folder on port 5500.
5. **Connect:** Go to `frontend/js/config.js` and set `API_URL: 'http://127.0.0.1:5000'`.

---

### Option 2: Split Hosting (Backend/DB Local, Frontend Hosted)
*Best if you do not want to buy a web server, but want the frontend live for users (e.g., using GitHub Pages, Vercel, or Netlify), while running the database securely on your home network.*

1. **Expose Local Backend:** Run your backend locally (Port 5000) mapped to your local MySQL database.
2. **Setup Ngrok/Cloudflare:** Run a tunnel like `ngrok http 5000`. This gives you a public HTTPS URL mapped to your local machine.
3. **Update CORS:** Add the frontend hosting URL (e.g., `https://myhackathon.vercel.app`) to your `backend/.env` under `ALLOWED_ORIGIN`.
4. **Configure Frontend:** Go to `frontend/js/config.js` and set `API_URL: 'https://<your-ngrok-url>.ngrok-free.app'`. 
5. **Host Frontend:** Upload your `frontend` folder to Vercel, Netlify, or Hostinger. 
*Note: Your local computer must remain ON and running the ngrok tunnel for the website to communicate.*

---

### Option 3: Full Production Deployment (VPS or Render)
*Best for actual live events. The entire stack (Frontend + Backend) is served by a cloud provider like Render, communicating with a cloud database like TiDB.*

1. **Database:** Create a free MySQL-compatible cloud database using **TiDB Serverless**. Grab your connection string.
2. **Backend Config:** In your Render dashboard, set the following Environment Variables:
   *   `DATABASE_URL` = `mysql+pymysql://<user>:<password>@<host>:4000/test?ssl_ca=/etc/ssl/certs/ca-certificates.crt&ssl_verify_cert=true&ssl_verify_identity=true`
   *   `DEV_MODE` = `false`
   *   `ALLOWED_ORIGIN` = `https://<your-render-url>.onrender.com`
3. **Render Setup:**
   *   Build Command: `pip install -r backend/requirements.txt`
   *   Start Command: `cd backend && gunicorn app:app`
4. **Frontend Integration:** Because we serve the static frontend through Flask in production, no separate frontend hosting is required. Just ensure `frontend/js/config.js` points to your unified render domain or is an empty string `''` for relative paths.

---

## 🔒 Security Notes
*   **Session Cookies:** Configured for `SameSite=None` and `Secure=True` to allow seamless split-hosting authentication.
*   **Media Handling:** All payment screenshots are converted to `Base64` strings and stored natively inside the database as `MEDIUMTEXT`. No complex AWS S3 setup required for image hosting.
*   **Passwords:** Securely hashed using `Bcrypt`.

## 🧑‍💻 Contributing
Found a bug or want to enhance the UI? Pull requests are always welcome!
