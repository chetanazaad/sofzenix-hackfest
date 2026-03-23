from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ─── Hackathon User ────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'sfz_users'
    id                    = db.Column(db.Integer, primary_key=True)
    google_id             = db.Column(db.String(255), unique=True, nullable=True)
    name                  = db.Column(db.String(255), nullable=False)
    email                 = db.Column(db.String(255), unique=True, nullable=False)
    password_hash         = db.Column(db.String(255), nullable=True)
    phone                 = db.Column(db.String(100), nullable=True)
    college               = db.Column(db.String(255), nullable=True)
    branch                = db.Column(db.String(100), nullable=True)
    year_of_study         = db.Column(db.String(10), nullable=True)
    avatar_url            = db.Column(db.Text, nullable=True)
    role                  = db.Column(db.Enum('participant', 'evaluator', 'admin'), default='participant')
    is_verified           = db.Column(db.Boolean, default=False)
    referral_code         = db.Column(db.String(12), unique=True, nullable=True)
    referred_by           = db.Column(db.String(12), nullable=True)
    participation_type    = db.Column(db.Enum('INDIVIDUAL', 'TEAM'), default='INDIVIDUAL')
    team_name             = db.Column(db.String(255), nullable=True)
    payment_reference     = db.Column(db.String(255), nullable=True)
    payment_screenshot    = db.Column(db.Text, nullable=True)  # base64
    payer_name            = db.Column(db.String(255), nullable=True)  # name on payment app
    payment_date          = db.Column(db.String(20), nullable=True)   # date of payment
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)

    scratch_links = db.relationship('ScratchLink', backref='user', lazy=True)


# ─── Admin User ────────────────────────────────────────────────────────────────
class AdminUser(UserMixin, db.Model):
    __tablename__ = 'sfz_admin_users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Scratch Reward Link ──────────────────────────────────────────────────────
class ScratchLink(db.Model):
    __tablename__ = 'sfz_scratch_links'
    id               = db.Column(db.Integer, primary_key=True)
    token            = db.Column(db.String(20), unique=True, nullable=False, index=True)
    campaign_id      = db.Column(db.String(100), nullable=True)
    phone_number     = db.Column(db.String(100), nullable=True, index=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('sfz_users.id'), nullable=True)
    reward_amount    = db.Column(db.Float, nullable=False)
    is_used          = db.Column(db.Boolean, default=False, nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    used_at          = db.Column(db.DateTime, nullable=True)
    recipient_upi    = db.Column(db.String(100), nullable=True)
    submitted_phone  = db.Column(db.String(255), nullable=True)
    payment_status   = db.Column(db.String(30), default='pending')
    payment_ref      = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 'token': self.token, 'campaign_id': self.campaign_id,
            'phone_number': self.phone_number, 'user_id': self.user_id,
            'reward_amount': self.reward_amount, 'is_used': self.is_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'recipient_upi': self.recipient_upi, 'submitted_phone': self.submitted_phone,
            'payment_status': self.payment_status, 'payment_ref': self.payment_ref,
        }


# ─── Payment Log ──────────────────────────────────────────────────────────────
class PaymentLog(db.Model):
    __tablename__ = 'sfz_payment_logs'
    id            = db.Column(db.Integer, primary_key=True)
    token         = db.Column(db.String(20), db.ForeignKey('sfz_scratch_links.token'), nullable=False)
    upi_id        = db.Column(db.String(100), nullable=False)
    amount        = db.Column(db.Float, nullable=False)
    status        = db.Column(db.String(20), nullable=False)
    response_data = db.Column(db.Text, nullable=True)
    timestamp     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'token': self.token, 'upi_id': self.upi_id,
            'amount': self.amount, 'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


# ─── Reward Settings ─────────────────────────────────────────────────────────
class RewardSettings(db.Model):
    __tablename__ = 'sfz_reward_settings'
    id                       = db.Column(db.Integer, primary_key=True)
    min_amount               = db.Column(db.Float, default=50.0)
    max_amount               = db.Column(db.Float, default=350.0)
    primary_gateway          = db.Column(db.String(20), default='razorpay')
    dev_mode                 = db.Column(db.Boolean, default=True)
    phonepe_merchant_id      = db.Column(db.String(255), nullable=True)
    phonepe_api_key          = db.Column(db.String(255), nullable=True)
    razorpayx_key_id         = db.Column(db.String(255), nullable=True)
    razorpayx_key_secret     = db.Column(db.String(255), nullable=True)
    razorpayx_account_number = db.Column(db.String(255), nullable=True)
    updated_at               = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Team Member (manually added by team leader) ────────────────────────────
class TeamMember(db.Model):
    __tablename__ = 'sfz_team_members'
    id         = db.Column(db.Integer, primary_key=True)
    leader_id  = db.Column(db.Integer, db.ForeignKey('sfz_users.id'), nullable=False)
    name       = db.Column(db.String(255), nullable=False)
    email      = db.Column(db.String(255), nullable=False)
    phone      = db.Column(db.String(255), nullable=False)
    added_at   = db.Column(db.DateTime, default=datetime.utcnow)

    leader = db.relationship('User', backref=db.backref('team_extra_members', lazy=True))
