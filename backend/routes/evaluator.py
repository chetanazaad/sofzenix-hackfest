from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from models import db, Evaluator, Evaluation, User

evaluator_bp = Blueprint('evaluator', __name__)


# ── Auth Guard ────────────────────────────────────────────────────────────────

def evaluator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('evaluator_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Auth ──────────────────────────────────────────────────────────────────────

@evaluator_bp.route('/api/evaluator/login', methods=['POST'])
def evaluator_login():
    data = request.get_json() or {}
    login_id = data.get('login_id', '').strip()
    password = data.get('password', '').strip()

    if not login_id or not password:
        return jsonify({'success': False, 'error': 'Login ID and password required'}), 400

    ev = Evaluator.query.filter_by(login_id=login_id).first()
    if ev and ev.password == password:
        ev.last_login = datetime.utcnow()
        db.session.commit()
        session['evaluator_id']   = ev.id
        session['evaluator_name'] = ev.name
        return jsonify({'success': True, 'evaluator': ev.to_dict()}), 200

    return jsonify({'success': False, 'error': 'Invalid login ID or password'}), 401


@evaluator_bp.route('/api/evaluator/logout', methods=['POST'])
def evaluator_logout():
    session.pop('evaluator_id', None)
    session.pop('evaluator_name', None)
    return jsonify({'success': True}), 200


@evaluator_bp.route('/api/evaluator/me', methods=['GET'])
def evaluator_me():
    eid = session.get('evaluator_id')
    if not eid:
        return jsonify({'logged_in': False}), 200
    ev = Evaluator.query.get(eid)
    if not ev:
        return jsonify({'logged_in': False}), 200
    return jsonify({'logged_in': True, 'evaluator': ev.to_dict()}), 200


# ── Dashboard Stats ───────────────────────────────────────────────────────────

@evaluator_bp.route('/api/evaluator/stats', methods=['GET'])
@evaluator_required
def evaluator_stats():
    eid = session['evaluator_id']
    total_participants = User.query.filter_by(role='participant').count()
    my_evals = Evaluation.query.filter_by(evaluator_id=eid).all()
    in_progress = sum(1 for e in my_evals if e.status == 'IN_PROGRESS')
    completed   = sum(1 for e in my_evals if e.status == 'COMPLETED')
    return jsonify({
        'total_participants': total_participants,
        'in_progress': in_progress,
        'completed': completed,
    }), 200


# ── Participants List (for Judging Queue) ─────────────────────────────────────

@evaluator_bp.route('/api/evaluator/participants', methods=['GET'])
@evaluator_required
def evaluator_participants():
    eid = session['evaluator_id']
    participants = User.query.filter_by(role='participant').order_by(User.created_at.asc()).all()

    result = []
    for u in participants:
        ev = Evaluation.query.filter_by(participant_id=u.id).first()
        entry = {
            'id': u.id, 'name': u.name, 'email': u.email,
            'phone': u.phone, 'college': u.college, 'branch': u.branch,
            'participation_type': u.participation_type, 'team_name': u.team_name,
            'is_verified': u.is_verified,
            'evaluation': None,
            'my_status': 'AVAILABLE',
            'other_evaluator': None,
        }
        if ev:
            entry['evaluation'] = ev.to_dict()
            if ev.evaluator_id == eid:
                entry['my_status'] = ev.status  # IN_PROGRESS or COMPLETED
            else:
                other = Evaluator.query.get(ev.evaluator_id)
                entry['my_status'] = 'TAKEN'
                entry['other_evaluator'] = other.name if other else 'Another Evaluator'
        result.append(entry)

    # Sort: AVAILABLE first, then IN_PROGRESS, then COMPLETED/TAKEN
    order = {'AVAILABLE': 0, 'IN_PROGRESS': 1, 'COMPLETED': 2, 'TAKEN': 3}
    result.sort(key=lambda x: order.get(x['my_status'], 99))

    return jsonify({'participants': result}), 200


# ── Choose Participant (claim for evaluation) ─────────────────────────────────

@evaluator_bp.route('/api/evaluator/choose/<int:uid>', methods=['POST'])
@evaluator_required
def choose_participant(uid):
    eid = session['evaluator_id']
    existing = Evaluation.query.filter_by(participant_id=uid).first()
    if existing:
        return jsonify({'success': False, 'error': 'This participant is already being evaluated'}), 409
    ev = Evaluation(participant_id=uid, evaluator_id=eid, status='IN_PROGRESS', chosen_at=datetime.utcnow())
    db.session.add(ev)
    db.session.commit()
    return jsonify({'success': True, 'evaluation': ev.to_dict()}), 201


# ── Submit Scores ─────────────────────────────────────────────────────────────

@evaluator_bp.route('/api/evaluator/score/<int:uid>', methods=['POST'])
@evaluator_required
def score_participant(uid):
    eid = session['evaluator_id']
    ev = Evaluation.query.filter_by(participant_id=uid, evaluator_id=eid).first()
    if not ev:
        return jsonify({'success': False, 'error': 'Evaluation not found or not yours'}), 404

    data = request.get_json() or {}
    ev.innovation_score   = int(data.get('innovation_score', 0))
    ev.technical_score    = int(data.get('technical_score', 0))
    ev.impact_score       = int(data.get('impact_score', 0))
    ev.presentation_score = int(data.get('presentation_score', 0))
    ev.scalability_score  = int(data.get('scalability_score', 0))
    ev.total_score        = (ev.innovation_score + ev.technical_score +
                             ev.impact_score + ev.presentation_score + ev.scalability_score)
    ev.comments           = data.get('comments', '')
    ev.status             = 'COMPLETED'
    ev.completed_at       = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'evaluation': ev.to_dict()}), 200


# ── Set Meet Link ─────────────────────────────────────────────────────────────

@evaluator_bp.route('/api/evaluator/meet-link/<int:uid>', methods=['POST'])
@evaluator_required
def set_meet_link(uid):
    eid = session['evaluator_id']
    ev = Evaluation.query.filter_by(participant_id=uid, evaluator_id=eid).first()
    if not ev:
        return jsonify({'success': False, 'error': 'Evaluation not found or not yours'}), 404
    data = request.get_json() or {}
    ev.meet_link = data.get('meet_link', '').strip()
    db.session.commit()
    return jsonify({'success': True}), 200


# ── Leaderboard (sorted by total_score) ──────────────────────────────────────

@evaluator_bp.route('/api/evaluator/leaderboard', methods=['GET'])
@evaluator_required
def leaderboard():
    evals = (Evaluation.query
             .filter_by(status='COMPLETED')
             .order_by(Evaluation.total_score.desc())
             .all())
    result = []
    for rank, ev in enumerate(evals, 1):
        u = User.query.get(ev.participant_id)
        result.append({
            'rank': rank,
            'participant_id': ev.participant_id,
            'name': u.name if u else 'Unknown',
            'college': u.college if u else '',
            'team_name': u.team_name if u else '',
            'participation_type': u.participation_type if u else '',
            'total_score': ev.total_score,
            'innovation_score': ev.innovation_score,
            'technical_score': ev.technical_score,
            'impact_score': ev.impact_score,
            'presentation_score': ev.presentation_score,
            'scalability_score': ev.scalability_score,
            'comments': ev.comments,
        })
    return jsonify({'leaderboard': result}), 200
