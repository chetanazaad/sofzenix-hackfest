import os, bcrypt
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models import db, AdminUser, RewardSettings


def create_app():
    frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=frontend_folder, static_url_path='')
    app.config.from_object(Config)

    # ── Proxy Fix (Ensures HTTPS is detected through tunnels) ───
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5000", "http://127.0.0.1:5000",
        "http://localhost:5500", "http://127.0.0.1:5500",
        "http://localhost:3000",
        "https://sofzenix-hackfest.onrender.com",
        Config.ALLOWED_ORIGIN,
    ], allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
       methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])

    # ── Session Cookie Fix for Cross-Site (Render <-> Local) ───
    app.config.update(
        SESSION_COOKIE_SAMESITE='None',
        SESSION_COOKIE_SECURE=True, # Required for SameSite=None
        SESSION_COOKIE_HTTPONLY=True
    )

    # Register blueprints
    from routes.auth    import auth_bp
    from routes.register import register_bp
    from routes.admin   import admin_bp
    from routes.scratch import scratch_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(scratch_bp)

    with app.app_context():
        # ─── FRESH DATABASE SETUP ───
        from sqlalchemy import text
        try:
            from sqlalchemy import create_engine
            # Connect to TiDB root to ensure the new DB exists
            # We must pass SSL args here as well
            base_uri = Config.SQLALCHEMY_DATABASE_URI.rsplit('/', 1)[0] + '/mysql'
            temp_engine = create_engine(base_uri, connect_args={"ssl": {"ca": "ca.pem"}})
            with temp_engine.connect() as conn:
                conn.execute(text("CREATE DATABASE IF NOT EXISTS sofzenix_hackfest_live;"))
                conn.commit()
            print("[Sofzenix Hackfest] Database 'sofzenix_hackfest_live' verified/created.")
        except Exception as e:
            print(f"[Sofzenix Hackfest] DB Creation info: {e}")

        # Final check if tables need to be created
        db.create_all()
        _seed_admin(app)
        _seed_settings()

    @app.route('/api/health')
    @app.route('/health')
    def health():
        from sqlalchemy import text
        try:
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)[:60]}'
        return {"status": "healthy", "service": "sofzenix-hackfest",
                "db": db_status, "dev_mode": Config.DEV_MODE}, 200

    @app.route('/')
    def index():
        idx = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(idx):
            return send_from_directory(app.static_folder, 'index.html')
        return '<h2 style="font-family:monospace;color:#00f5ff;background:#000;padding:40px">⚡ Sofzenix HackFest API is running.<br><br><a href="/api/health" style="color:#00f5ff">/api/health</a></h2>', 200

    @app.route('/<path:path>')
    def static_files(path):
        full = os.path.join(app.static_folder, path)
        if os.path.exists(full):
            return send_from_directory(app.static_folder, path)
        # SPA fallback — serve index.html or API message
        idx = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(idx):
            return send_from_directory(app.static_folder, 'index.html')
        return {'error': f'Not found: {path}'}, 404

    return app


def _seed_admin(app):
    if AdminUser.query.count() == 0:
        username = app.config['ADMIN_USERNAME']
        password = app.config['ADMIN_PASSWORD']
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.session.add(AdminUser(username=username, password_hash=hashed))
        db.session.commit()
        print(f"[Sofzenix HackFest] Default admin: {username} / {password}")


def _seed_settings():
    if RewardSettings.query.count() == 0:
        db.session.add(RewardSettings(min_amount=50.0, max_amount=350.0))
        db.session.commit()
        print("[Sofzenix HackFest] Default reward settings seeded: ₹50 – ₹350")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
