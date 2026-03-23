import json, re, bcrypt, io
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from functools import wraps
from models import db, AdminUser, User, ScratchLink, PaymentLog, RewardSettings, Evaluator, Evaluation
from utils.link_generator import generate_unique_token
from utils.reward_engine import generate_reward

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def normalize_phone(raw):
    digits = re.sub(r'\D', '', str(raw).strip())
    if digits.startswith('91') and len(digits) == 12: digits = digits[2:]
    if digits.startswith('0') and len(digits) == 11: digits = digits[1:]
    return digits if len(digits) == 10 else None


# ── Auth ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    user = AdminUser.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({'success': True, 'message': f'Welcome, {username}!'}), 200
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@admin_bp.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'success': True}), 200


@admin_bp.route('/api/admin/check-auth', methods=['GET'])
def check_auth():
    return jsonify({'logged_in': bool(session.get('admin_logged_in'))}), 200


# ── Hackathon Participant Management ─────────────────────────────────────────

@admin_bp.route('/api/admin/participants', methods=['GET'])
@admin_required
def get_participants():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    query = User.query.filter(User.role == 'participant')
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f'%{search}%'), User.email.ilike(f'%{search}%'),
                   User.college.ilike(f'%{search}%'))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'participants': [{
            'id': u.id, 'name': u.name, 'email': u.email, 'phone': u.phone,
            'college': u.college, 'branch': u.branch, 'year_of_study': u.year_of_study,
            'participation_type': u.participation_type, 'team_name': u.team_name,
            'payment_reference': u.payment_reference,
            'payer_name': u.payer_name,
            'payment_date': u.payment_date,
            'is_verified': u.is_verified,
            'referral_code': u.referral_code, 'referred_by': u.referred_by,
            'created_at': u.created_at.isoformat() if u.created_at else None,
        } for u in pagination.items],
        'total': pagination.total, 'page': page, 'pages': pagination.pages
    }), 200


@admin_bp.route('/api/admin/participants/<int:uid>/verify', methods=['POST'])
@admin_required
def verify_participant(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user.is_verified = True
    db.session.commit()
    return jsonify({'success': True, 'message': f'{user.name} verified successfully'}), 200


@admin_bp.route('/api/admin/participants/<int:uid>', methods=['DELETE'])
@admin_required
def delete_participant(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    # Detach scratch links from this user but keep them
    ScratchLink.query.filter_by(user_id=uid).update({'user_id': None})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True}), 200


# ── Delete Campaign ───────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/campaigns/<campaign_id>', methods=['DELETE'])
@admin_required
def delete_campaign(campaign_id):
    if not campaign_id:
        return jsonify({'success': False, 'error': 'Campaign ID required'}), 400
    links = ScratchLink.query.filter_by(campaign_id=campaign_id).all()
    if not links:
        return jsonify({'success': False, 'error': f'No campaign found with ID "{campaign_id}"'}), 404
    count = len(links)
    for link in links:
        # Remove payment logs linked to these tokens
        PaymentLog.query.filter_by(token=link.token).delete()
        db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Deleted {count} links from campaign "{campaign_id}"'}), 200


# ── Wipe All Scratch Data ────────────────────────────────────────────────────

@admin_bp.route('/api/admin/wipe', methods=['DELETE'])
@admin_required
def wipe_database():
    PaymentLog.query.delete()
    ScratchLink.query.delete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'All scratch data wiped successfully'}), 200


# ── Change Admin Credentials ─────────────────────────────────────────────────

@admin_bp.route('/api/admin/change-credentials', methods=['POST'])
@admin_required
def change_credentials():
    data = request.get_json() or {}
    current_password = data.get('current_password', '').strip()
    new_username     = data.get('new_username', '').strip()
    new_password     = data.get('new_password', '').strip()

    if not current_password:
        return jsonify({'success': False, 'error': 'Current password is required'}), 400

    username = session.get('admin_username', '')
    admin = AdminUser.query.filter_by(username=username).first()
    if not admin or not bcrypt.checkpw(current_password.encode(), admin.password_hash.encode()):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401

    if not new_username and not new_password:
        return jsonify({'success': False, 'error': 'Provide at least a new username or password'}), 400
    if new_password and len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400

    if new_username:
        existing = AdminUser.query.filter_by(username=new_username).first()
        if existing and existing.id != admin.id:
            return jsonify({'success': False, 'error': 'Username already taken'}), 409
        admin.username = new_username
        session['admin_username'] = new_username

    if new_password:
        admin.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    db.session.commit()
    return jsonify({'success': True, 'message': 'Credentials updated successfully'}), 200


@admin_bp.route('/api/admin/participants/<int:uid>/screenshot', methods=['GET'])
@admin_required
def get_screenshot(uid):
    user = User.query.get(uid)
    if not user or not user.payment_screenshot:
        return jsonify({'error': 'No screenshot'}), 404
    return jsonify({'screenshot': user.payment_screenshot}), 200


# ── Reward Stats ─────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/reward-stats', methods=['GET'])
@admin_required
def reward_stats():
    campaign_id = request.args.get('campaign_id', 'all')
    query = ScratchLink.query
    if campaign_id and campaign_id != 'all':
        query = query.filter_by(campaign_id=campaign_id)
    total = query.count()
    used  = query.filter(ScratchLink.is_used == True).count()
    disbursed = db.session.query(db.func.sum(PaymentLog.amount)).filter(
        PaymentLog.status == 'success').scalar() or 0.0
    settings = RewardSettings.query.first()
    return jsonify({
        'total_links': total, 'used_links': used, 'unused_links': total - used,
        'total_disbursed': round(disbursed, 2),
        'reward_settings': {
            'min_amount': settings.min_amount if settings else 50,
            'max_amount': settings.max_amount if settings else 350,
            'primary_gateway': settings.primary_gateway if settings else 'razorpay',
            'dev_mode': settings.dev_mode if settings else True
        }
    }), 200


# ── Generate Scratch Links ───────────────────────────────────────────────────

@admin_bp.route('/api/admin/generate', methods=['POST'])
@admin_required
def generate_links():
    data = request.get_json() or {}
    settings = RewardSettings.query.first()
    min_amt = float(data.get('min_amount', settings.min_amount if settings else 50.0))
    max_amt = float(data.get('max_amount', settings.max_amount if settings else 350.0))
    campaign_name = data.get('campaign_id', '').strip() or f"Campaign-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
    if min_amt < 1 or max_amt < min_amt:
        return jsonify({'success': False, 'error': 'Invalid reward range'}), 400

    raw_phones = data.get('phone_numbers', [])
    user_ids = data.get('user_ids', [])  # Dispatch by hackathon user IDs
    phones = []
    if raw_phones:
        seen = set()
        for p in raw_phones:
            n = normalize_phone(p)
            if n and n not in seen:
                seen.add(n); phones.append(n)
        count = len(phones)
    else:
        count = int(data.get('count', 1))
        count = max(1, min(count, 500))

    all_tokens = {r.token for r in ScratchLink.query.with_entities(ScratchLink.token).all()}
    new_links = []
    for i in range(count):
        phone = phones[i] if phones else None
        user_id = user_ids[i] if user_ids and i < len(user_ids) else None
        # If dispatching by user_id, fetch phone from user
        if user_id and not phone:
            u = User.query.get(user_id)
            if u: phone = u.phone
        token = generate_unique_token(all_tokens)
        all_tokens.add(token)
        reward = generate_reward(min_amt, max_amt)
        link = ScratchLink(token=token, reward_amount=reward, campaign_id=campaign_name,
                           phone_number=phone, user_id=user_id)
        db.session.add(link)
        new_links.append({'token': token, 'reward_amount': reward, 'phone_number': phone})
    db.session.commit()
    return jsonify({'success': True, 'generated': len(new_links), 'links': new_links,
                    'message': f'{len(new_links)} scratch card(s) generated for "{campaign_name}"'}), 201


@admin_bp.route('/api/admin/upload-phones', methods=['POST'])
@admin_required
def upload_phones():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    file = request.files['file']
    fname = file.filename.lower()
    phones = []
    try:
        if fname.endswith('.csv'):
            import csv
            text = file.read().decode('utf-8', errors='ignore')
            reader = csv.DictReader(io.StringIO(text))
            phone_col = next((c for c in (reader.fieldnames or [])
                              if any(k in c.lower() for k in ['phone','mobile','contact','number'])), None)
            if not phone_col and reader.fieldnames:
                phone_col = reader.fieldnames[0]
            if phone_col:
                for row in reader:
                    n = normalize_phone(row.get(phone_col, ''))
                    if n: phones.append(n)
        elif fname.endswith(('.xlsx', '.xls')):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file.read()), read_only=True)
            rows = list(wb.active.iter_rows(values_only=True))
            if not rows: return jsonify({'success': False, 'error': 'Empty spreadsheet'}), 400
            header = [str(c).lower() if c else '' for c in rows[0]]
            idx = next((i for i, h in enumerate(header)
                        if any(k in h for k in ['phone','mobile','contact','number'])), 0)
            for row in rows[1:]:
                if idx < len(row) and row[idx]:
                    n = normalize_phone(row[idx])
                    if n: phones.append(n)
        else:
            return jsonify({'success': False, 'error': 'Use .csv or .xlsx'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'File error: {str(e)}'}), 400
    seen = set(); unique = []
    for p in phones:
        if p not in seen: seen.add(p); unique.append(p)
    return jsonify({'success': True, 'phones': unique, 'count': len(unique),
                    'duplicates_removed': len(phones) - len(unique)}), 200


# ── Scratch Links Table ──────────────────────────────────────────────────────

@admin_bp.route('/api/admin/links', methods=['GET'])
@admin_required
def get_links():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', 'all')
    campaign = request.args.get('campaign_id', 'all')
    query = ScratchLink.query
    if status == 'used':   query = query.filter_by(is_used=True)
    elif status == 'unused': query = query.filter_by(is_used=False)
    if campaign and campaign != 'all': query = query.filter_by(campaign_id=campaign)
    pagination = query.order_by(ScratchLink.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'links': [l.to_dict() for l in pagination.items],
                    'total': pagination.total, 'page': page, 'pages': pagination.pages}), 200


# ── Payment Logs ─────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/payments', methods=['GET'])
@admin_required
def get_payments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', 'all')
    query = PaymentLog.query
    if status == 'success': query = query.filter_by(status='success')
    elif status == 'failed': query = query.filter_by(status='failed')
    pagination = query.order_by(PaymentLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'logs': [l.to_dict() for l in pagination.items],
                    'total': pagination.total, 'page': page, 'pages': pagination.pages}), 200


@admin_bp.route('/api/admin/payments/<token>/retry', methods=['POST'])
@admin_required
def retry_payment(token):
    from utils.payment_engine import initiate_upi_payout
    link = ScratchLink.query.filter_by(token=token.upper()).first()
    if not link: return jsonify({'success': False, 'error': 'Token not found'}), 404
    if not link.is_used or not link.recipient_upi:
        return jsonify({'success': False, 'error': 'Card not claimed yet'}), 400
    if link.payment_status == 'success':
        return jsonify({'success': False, 'error': 'Payment already succeeded — retry blocked'}), 409
    link.payment_status = 'processing'
    db.session.commit()
    result = initiate_upi_payout(link.recipient_upi, link.reward_amount, link.token + '-RETRY')
    log = PaymentLog(token=link.token, upi_id=link.recipient_upi, amount=link.reward_amount,
                     status='success' if result['success'] else 'failed',
                     response_data=json.dumps(result.get('raw', result.get('message', ''))))
    db.session.add(log)
    link.payment_status = 'success' if result['success'] else 'failed'
    link.payment_ref = result.get('transaction_id', '')
    db.session.commit()
    if result['success']:
        return jsonify({'success': True,
                        'message': f"₹{link.reward_amount} sent to {link.recipient_upi}",
                        'transaction_id': result['transaction_id']}), 200
    return jsonify({'success': False, 'error': f"Retry failed: {result.get('message')}"}), 500


# ── Campaigns ────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/campaigns', methods=['GET'])
@admin_required
def get_campaigns():
    campaigns = db.session.query(ScratchLink.campaign_id).filter(
        ScratchLink.campaign_id.isnot(None)).distinct().all()
    return jsonify({'campaigns': [c[0] for c in campaigns if c[0]]}), 200


# ── Settings ──────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/settings', methods=['POST'])
@admin_required
def update_settings():
    data = request.get_json() or {}
    settings = RewardSettings.query.first()
    if not settings:
        settings = RewardSettings()
        db.session.add(settings)
    settings.min_amount = float(data.get('min_amount', 50))
    settings.max_amount = float(data.get('max_amount', 350))
    settings.primary_gateway = data.get('primary_gateway', 'razorpay')
    settings.dev_mode = data.get('dev_mode', True)
    if data.get('phonepe_merchant_id'): settings.phonepe_merchant_id = data['phonepe_merchant_id']
    if data.get('phonepe_api_key') and data['phonepe_api_key'] != '********':
        settings.phonepe_api_key = data['phonepe_api_key']
    if data.get('razorpayx_key_id'): settings.razorpayx_key_id = data['razorpayx_key_id']
    if data.get('razorpayx_key_secret') and data['razorpayx_key_secret'] != '********':
        settings.razorpayx_key_secret = data['razorpayx_key_secret']
    if data.get('razorpayx_account_number'):
        settings.razorpayx_account_number = data['razorpayx_account_number']
    db.session.commit()
    return jsonify({'success': True}), 200


# ── Evaluator Management ──────────────────────────────────────────────────────

@admin_bp.route('/api/admin/evaluators', methods=['GET'])
@admin_required
def list_evaluators():
    evaluators = Evaluator.query.order_by(Evaluator.created_at.desc()).all()
    result = []
    for ev in evaluators:
        d = ev.to_dict()
        d['evaluation_count'] = Evaluation.query.filter_by(evaluator_id=ev.id).count()
        d['completed_count']  = Evaluation.query.filter_by(evaluator_id=ev.id, status='COMPLETED').count()
        result.append(d)
    return jsonify({'evaluators': result, 'total': len(result)}), 200


@admin_bp.route('/api/admin/evaluators', methods=['POST'])
@admin_required
def create_evaluator():
    data = request.get_json() or {}
    name     = data.get('name', '').strip()
    login_id = data.get('login_id', '').strip()
    password = data.get('password', '').strip()

    if not name or not login_id or not password:
        return jsonify({'success': False, 'error': 'Name, login_id, and password are required'}), 400
    if len(password) < 4:
        return jsonify({'success': False, 'error': 'Password must be at least 4 characters'}), 400
    if Evaluator.query.filter_by(login_id=login_id).first():
        return jsonify({'success': False, 'error': f'Login ID "{login_id}" already exists'}), 409

    ev = Evaluator(name=name, login_id=login_id, password=password)
    db.session.add(ev)
    db.session.commit()
    return jsonify({'success': True, 'evaluator': ev.to_dict()}), 201


@admin_bp.route('/api/admin/evaluators/<int:eid>', methods=['DELETE'])
@admin_required
def delete_evaluator(eid):
    ev = Evaluator.query.get(eid)
    if not ev:
        return jsonify({'success': False, 'error': 'Evaluator not found'}), 404
    # Cascading: remove evaluations done by this evaluator
    Evaluation.query.filter_by(evaluator_id=eid).delete()
    db.session.delete(ev)
    db.session.commit()
    return jsonify({'success': True}), 200


@admin_bp.route('/api/admin/evaluators/<int:eid>/evaluations', methods=['GET'])
@admin_required
def evaluator_evaluations(eid):
    ev = Evaluator.query.get(eid)
    if not ev:
        return jsonify({'success': False, 'error': 'Evaluator not found'}), 404
    evals = Evaluation.query.filter_by(evaluator_id=eid).order_by(Evaluation.chosen_at.desc()).all()
    result = []
    for e in evals:
        d = e.to_dict()
        u = User.query.get(e.participant_id)
        d['participant_name'] = u.name if u else 'Unknown'
        d['participant_email'] = u.email if u else ''
        result.append(d)
    return jsonify({'evaluator': ev.to_dict(), 'evaluations': result}), 200


@admin_bp.route('/api/admin/evaluations/leaderboard', methods=['GET'])
@admin_required
def admin_leaderboard():
    evals = (Evaluation.query
             .filter_by(status='COMPLETED')
             .order_by(Evaluation.total_score.desc())
             .all())
    result = []
    for rank, e in enumerate(evals, 1):
        u   = User.query.get(e.participant_id)
        ev  = Evaluator.query.get(e.evaluator_id)
        result.append({
            'rank': rank,
            'participant_name': u.name if u else 'Unknown',
            'participant_email': u.email if u else '',
            'college': u.college if u else '',
            'team_name': u.team_name if u else '',
            'participation_type': u.participation_type if u else '',
            'evaluator_name': ev.name if ev else 'Unknown',
            'total_score': e.total_score,
            'innovation_score': e.innovation_score,
            'technical_score': e.technical_score,
            'impact_score': e.impact_score,
            'presentation_score': e.presentation_score,
            'scalability_score': e.scalability_score,
            'comments': e.comments,
            'completed_at': e.completed_at.isoformat() if e.completed_at else None,
        })
    return jsonify({'leaderboard': result, 'total': len(result)}), 200


@admin_bp.route('/api/admin/evaluations', methods=['GET'])
@admin_required
def all_evaluations():
    """All evaluations with participant + evaluator info."""
    evals = Evaluation.query.order_by(Evaluation.chosen_at.desc()).all()
    result = []
    for e in evals:
        u  = User.query.get(e.participant_id)
        ev = Evaluator.query.get(e.evaluator_id)
        d  = e.to_dict()
        d['participant_name']  = u.name  if u  else 'Unknown'
        d['participant_email'] = u.email if u  else ''
        d['evaluator_name']    = ev.name if ev else 'Unknown'
        result.append(d)
    return jsonify({'evaluations': result, 'total': len(result)}), 200
