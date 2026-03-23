import json, re
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import db, ScratchLink, PaymentLog, User

scratch_bp = Blueprint('scratch', __name__)


def is_valid_upi(upi_id: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$', upi_id.strip()))


@scratch_bp.route('/api/reward/<token>', methods=['GET'])
def get_scratch_card(token):
    link = ScratchLink.query.filter_by(token=token.upper()).first()
    if not link:
        return jsonify({'error': 'Invalid or expired link', 'valid': False}), 404
    if link.is_used:
        return jsonify({'valid': False, 'error': 'This scratch card has already been used.',
                        'used_at': link.used_at.isoformat() if link.used_at else None}), 410
    
    # Try to see if user is already logged in to pre-fill or skip some checks
    uid  = session.get('user_id')
    user = User.query.get(uid) if uid else None
    
    return jsonify({
        'valid': True, 
        'token': link.token, 
        'reward_amount': link.reward_amount,
        'phone_number': link.phone_number,
        'requires_phone_verification': bool(link.phone_number),
        'is_logged_in': bool(user),
        'user_phone': user.phone if user else None
    }), 200


@scratch_bp.route('/api/reward/<token>/claim', methods=['POST'])
def claim_reward(token):
    link = ScratchLink.query.filter_by(token=token.upper()).first()
    if not link: return jsonify({'success': False, 'error': 'Invalid token'}), 404
    if link.is_used: return jsonify({'success': False, 'error': 'Card already claimed.'}), 410

    data = request.get_json() or {}
    recipient_name = data.get('name', '').strip()
    upi_id = data.get('upi_id', '').strip()
    contact = data.get('contact_number', '').strip()
    submitted_phone = data.get('phone_number', '').strip() # Phone used for verification

    if not recipient_name: return jsonify({'success': False, 'error': 'Full name is required'}), 400
    if not upi_id: return jsonify({'success': False, 'error': 'UPI ID is required'}), 400
    if not is_valid_upi(upi_id): return jsonify({'success': False, 'error': 'Invalid UPI ID format. Use: name@bank'}), 400
    if not contact: return jsonify({'success': False, 'error': 'Contact number required for verification'}), 400

    # Strict Identity Verification
    if link.phone_number:
        # Normalize both for a clean comparison
        def clean(p): return re.sub(r'\D', '', str(p or ''))[-10:]
        
        target = clean(link.phone_number)
        input_phone = clean(submitted_phone)
        
        # If user is logged in, we can also check their session phone
        uid = session.get('user_id')
        user = User.query.get(uid) if uid else None
        session_phone = clean(user.phone) if user else None

        # Must match EITHER the input OR the session (if they are the same person)
        if input_phone != target and session_phone != target:
            return jsonify({'success': False, 'error': 'Identity verification failed. This card is linked to a different participant account.'}), 403

    link.is_used = True
    link.used_at = datetime.utcnow()
    link.recipient_upi = upi_id
    link.submitted_phone = f"{recipient_name} | {contact}" # Combine name and contact for admin
    link.payment_status = 'pending_verification'
    db.session.commit()

    return jsonify({'success': True,
                    'message': '🎉 Verification Request Submitted!',
                    'detail': 'Your reward will be sent to your UPI ID after we verify your details (24-48 hours).',
                    'amount': link.reward_amount}), 200


@scratch_bp.route('/api/reward/<token>/status', methods=['GET'])
def payment_status(token):
    link = ScratchLink.query.filter_by(token=token.upper()).first()
    if not link: return jsonify({'error': 'Token not found'}), 404
    return jsonify({'token': link.token, 'is_used': link.is_used,
                    'payment_status': link.payment_status, 'payment_ref': link.payment_ref,
                    'recipient_upi': link.recipient_upi, 'reward_amount': link.reward_amount,
                    'used_at': link.used_at.isoformat() if link.used_at else None}), 200
