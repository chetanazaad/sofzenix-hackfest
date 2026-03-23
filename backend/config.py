import os
from dotenv import load_dotenv

load_dotenv()


def _build_db_uri() -> str:
    """
    Priority:
    1. DATABASE_URL env var (Render PostgreSQL, Railway, etc.)
       - Render sets postgres:// but SQLAlchemy needs postgresql://
    2. Individual DB_* vars  → MySQL via PyMySQL
    3. Fallback              → SQLite (local dev / unit testing)
    """
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        # Render provides postgres:// — fix the scheme for SQLAlchemy
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url

    host     = os.environ.get('DB_HOST', '')
    port     = os.environ.get('DB_PORT', '3306')
    user     = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '')
    name     = os.environ.get('DB_NAME', 'sofzenix_hackfest')

    if host:
        # TiDB Cloud requires SSL
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?ssl_ca=ca.pem"

    # Absolute fallback — SQLite (good enough for Render testing without a DB)
    return 'sqlite:///sofzenix_hackfest.db'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sofzenix-hackfest-change-this-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _build_db_uri()

    # Keep connections alive on PostgreSQL / MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 2,
    }

    # ── Google OAuth ──────────────────────────────────────────────
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI  = os.environ.get(
        'GOOGLE_REDIRECT_URI',
        'http://localhost:5000/auth/google/callback'
    )

    # ── Payment Gateways ──────────────────────────────────────────
    PHONEPE_API_KEY          = os.environ.get('PHONEPE_API_KEY', '')
    PHONEPE_MERCHANT_ID      = os.environ.get('PHONEPE_MERCHANT_ID', '')
    RAZORPAYX_KEY_ID         = os.environ.get('RAZORPAYX_KEY_ID', '')
    RAZORPAYX_KEY_SECRET     = os.environ.get('RAZORPAYX_KEY_SECRET', '')
    RAZORPAYX_ACCOUNT_NUMBER = os.environ.get('RAZORPAYX_ACCOUNT_NUMBER', '')

    DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'

    # ── Admin ─────────────────────────────────────────────────────
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@2026')

    # ── CORS — set to Hostinger domain in production ──────────────
    ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')

