import bcrypt
from flask import Blueprint, request, jsonify
from models import db, User, ScratchLink
from utils.link_generator import generate_referral_code, generate_unique_token
from utils.reward_engine import generate_reward

register_bp = Blueprint('register', __name__)


@register_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    phone    = data.get('phone', '').strip()
    college  = data.get('college', '').strip()
    branch   = data.get('branch', '').strip()
    year     = data.get('year_of_study', '').strip()
    password = data.get('password', '').strip()
    part     = data.get('participation_type', 'INDIVIDUAL').upper()
    team_name = data.get('team_name', '').strip()
    payment_ref = data.get('payment_reference', '').strip()
    payment_ss  = data.get('payment_screenshot_base64', '')
    payer_name  = data.get('payer_name', '').strip()
    payment_date = data.get('payment_date', '').strip()
    referred_by = data.get('referred_by', '').strip().upper()

    # Basic validation
    if not name or not email or not phone or not college or not password:
        return jsonify({'success': False, 'error': 'Please fill in all required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'This email is already registered'}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Generate unique referral code
    existing_codes = {r.referral_code for r in User.query.with_entities(User.referral_code).all() if r.referral_code}
    ref_code = generate_referral_code()
    while ref_code in existing_codes:
        ref_code = generate_referral_code()

    user = User(
        name=name, email=email, phone=phone, college=college, branch=branch,
        year_of_study=year, password_hash=hashed, participation_type=part,
        team_name=team_name if part == 'TEAM' else None,
        payment_reference=payment_ref, payment_screenshot=payment_ss,
        payer_name=payer_name, payment_date=payment_date,
        referral_code=ref_code,
        referred_by=referred_by if referred_by else None
    )
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    # If referred, generate a scratch card for the referrer
    if referred_by:
        referrer = User.query.filter_by(referral_code=referred_by).first()
        if referrer:
            # Check if this referrer already has a reward for this specific email to prevent abuse
            existing_ref = ScratchLink.query.filter_by(user_id=referrer.id, campaign_id=f"REF:{email}").first()
            if not existing_ref:
                existing_tokens = {r.token for r in ScratchLink.query.with_entities(ScratchLink.token).all()}
                token = generate_unique_token(existing_tokens)
                reward = generate_reward()
                link = ScratchLink(
                    token=token, campaign_id=f"REF:{email}", reward_amount=reward,
                    phone_number=referrer.phone, user_id=referrer.id
                )
                db.session.add(link)

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Registration successful! Please wait for admin verification.',
        'referral_code': ref_code
    }), 201
