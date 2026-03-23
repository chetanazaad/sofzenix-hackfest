from flask import Blueprint, request, jsonify, session, redirect, url_for
from models import db, User, TeamMember
from config import Config
from utils.link_generator import generate_referral_code
from requests_oauthlib import OAuth2Session
import os, bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash:
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    session['user_id'] = user.id
    session['user_email'] = user.email
    session.permanent = True
    return jsonify({
        'success': True,
        'token': str(user.id), # Fallback token for cross-site stability
        'user': {'id': user.id, 'name': user.name, 'email': user.email,
                 'role': user.role, 'is_verified': user.is_verified}
    }), 200


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True}), 200


@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    # Try getting UID from session OR Authorization header (for cross-site)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    uid = session.get('user_id') or (int(token) if token and token.isdigit() else None)

    if not uid:
        return jsonify({'logged_in': False}), 200
    user = User.query.get(uid)
    if not user:
        return jsonify({'logged_in': False}), 200
    # Fetch unused scratch links
    scratch_links = [{'token': s.token, 'amount': s.reward_amount} 
                     for s in user.scratch_links if not s.is_used]
    
    # Referral count
    referral_count = User.query.filter_by(referred_by=user.referral_code).count()

    # Team members: leader + manually added extra members
    team_members = []
    if user.participation_type == 'TEAM':
        # Leader themselves (always first)
        team_members.append({
            'id': None, 'name': user.name, 'email': user.email,
            'phone': user.phone or '', 'is_leader': True
        })
        # Extra members added via dashboard
        for m in user.team_extra_members:
            team_members.append({
                'id': m.id, 'name': m.name, 'email': m.email,
                'phone': m.phone, 'is_leader': False
            })

    return jsonify({
        'logged_in': True,
        'user': {
            'id': user.id, 'name': user.name, 'email': user.email,
            'phone': user.phone or '',
            'college': user.college or '',
            'role': user.role, 'is_verified': user.is_verified,
            'referral_code': user.referral_code,
            'participation_type': user.participation_type or 'INDIVIDUAL',
            'team_name': user.team_name or '',
            'referral_count': referral_count,
            'scratch_cards': scratch_links,
            'team_members': team_members
        }
    }), 200


@auth_bp.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    """Returns verified participants ordered by creation time (placeholder until real scoring)."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    uid = session.get('user_id') or (int(token) if token and token.isdigit() else None)
    if not uid:
        return jsonify({'logged_in': False}), 401

    # Only show verified participants
    participants = User.query.filter_by(is_verified=True).order_by(User.created_at.asc()).all()

    # Deduplicate by team_name for TEAM registrations
    seen_teams = set()
    board = []
    rank = 1
    for p in participants:
        if p.participation_type == 'TEAM' and p.team_name:
            if p.team_name in seen_teams:
                continue
            seen_teams.add(p.team_name)
            display_name = p.team_name
        else:
            display_name = p.name
        board.append({
            'rank': rank,
            'name': display_name,
            'type': p.participation_type or 'INDIVIDUAL',
            'score': None,   # No scoring yet
            'is_me': p.id == uid
        })
        rank += 1

    return jsonify({'success': True, 'leaderboard': board}), 200


# ── Team Member Management ──────────────────────────────────────────────────

def _get_auth_user():
    """Helper to get the currently authenticated user."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    uid = session.get('user_id') or (int(token) if token and token.isdigit() else None)
    if not uid:
        return None
    return User.query.get(uid)


@auth_bp.route('/api/team/members', methods=['GET'])
def get_team_members():
    user = _get_auth_user()
    if not user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    if user.participation_type != 'TEAM':
        return jsonify({'success': False, 'error': 'Only TEAM participants can manage members'}), 403
    members = [{
        'id': m.id, 'name': m.name, 'email': m.email, 'phone': m.phone
    } for m in user.team_extra_members]
    return jsonify({'success': True, 'members': members, 'leader': {
        'name': user.name, 'email': user.email, 'phone': user.phone or ''
    }, 'total': len(members) + 1}), 200


@auth_bp.route('/api/team/members', methods=['POST'])
def add_team_member():
    user = _get_auth_user()
    if not user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    if user.participation_type != 'TEAM':
        return jsonify({'success': False, 'error': 'Only TEAM participants can add members'}), 403
    if len(user.team_extra_members) >= 3:  # leader + 3 = max 4
        return jsonify({'success': False, 'error': 'Team is full (max 4 members including leader)'}), 400

    data = request.get_json() or {}
    name  = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()

    if not name or not email or not phone:
        return jsonify({'success': False, 'error': 'Name, email and phone are required'}), 400
    if '@' not in email:
        return jsonify({'success': False, 'error': 'Enter a valid email address'}), 400
    if len(phone) < 10:
        return jsonify({'success': False, 'error': 'Enter a valid phone number'}), 400

    member = TeamMember(leader_id=user.id, name=name, email=email, phone=phone)
    db.session.add(member)
    db.session.commit()
    return jsonify({'success': True, 'message': f'{name} added to your team!',
                    'member': {'id': member.id, 'name': member.name,
                               'email': member.email, 'phone': member.phone}}), 201


@auth_bp.route('/api/team/members/<int:member_id>', methods=['DELETE'])
def remove_team_member(member_id):
    user = _get_auth_user()
    if not user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    member = TeamMember.query.filter_by(id=member_id, leader_id=user.id).first()
    if not member:
        return jsonify({'success': False, 'error': 'Member not found'}), 404
    db.session.delete(member)
    db.session.commit()
    return jsonify({'success': True, 'message': f'{member.name} removed from team'}), 200


# ── Google OAuth 2.0 ───────────────────────────────────────────

def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Config.GOOGLE_CLIENT_ID, token=token)
    if state:
        return OAuth2Session(Config.GOOGLE_CLIENT_ID, state=state, 
                             redirect_uri=Config.GOOGLE_REDIRECT_URI,
                             scope=["openid", "https://www.googleapis.com/auth/userinfo.email", 
                                    "https://www.googleapis.com/auth/userinfo.profile"])
    return OAuth2Session(Config.GOOGLE_CLIENT_ID, 
                         redirect_uri=Config.GOOGLE_REDIRECT_URI,
                         scope=["openid", "https://www.googleapis.com/auth/userinfo.email", 
                                "https://www.googleapis.com/auth/userinfo.profile"])


@auth_bp.route('/auth/google')
def google_authorize():
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return "Google OAuth not configured. Please add GOOGLE_CLIENT_ID and SECRET to .env", 500
    
    google = get_google_auth()
    authorization_url, state = google.authorization_url("https://accounts.google.com/o/oauth2/v2/auth", 
                                                         access_type="offline")
    session['oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route('/auth/google/callback')
def google_callback():
    # If the user hits 'cancel' or there's an error
    if request.args.get('error'):
        return f"Error: {request.args.get('error')}"

    google = get_google_auth(state=session.get('oauth_state'))
    
    # Fetch token
    token = google.fetch_token("https://oauth2.googleapis.com/token",
                               client_secret=Config.GOOGLE_CLIENT_SECRET,
                               authorization_response=request.url)
    
    # Get user info
    user_info = google.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
    email = user_info.get('email', '').lower()
    name = user_info.get('name', 'Google User')

    if not email:
        return "Could not retrieve email from Google", 400

    # Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        # Auto-register new social user
        user = User(
            name=name,
            email=email,
            referral_code=generate_referral_code(),
            role='PARTICIPANT',
            is_verified=True # Social logins are pre-verified by Google
        )
        db.session.add(user)
        db.session.commit()
    
    session['user_id'] = user.id
    session['user_email'] = user.email
    session.permanent = True

    # Redirect back to the frontend dashboard or home
    return redirect('/login.html?social_success=1')
