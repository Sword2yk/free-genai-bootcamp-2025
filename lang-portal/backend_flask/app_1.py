from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///language_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    activity_id = db.Column(db.Integer, db.ForeignKey('study_activity.id'))
    
class StudyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sessions = db.relationship('StudySession', backref='activity', lazy=True)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    last_reviewed = db.Column(db.DateTime)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    words = db.relationship('Word', backref='group', lazy=True)

# API Routes

# Dashboard Endpoints
@app.route('/api/dashboard/last_study_session', methods=['GET'])
def get_last_study_session():
    session = StudySession.query.order_by(StudySession.start_time.desc()).first()
    if session:
        return jsonify({
            'id': session.id,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'activity_id': session.activity_id
        })
    return jsonify({'message': 'No study sessions found'}), 404

@app.route('/api/dashboard/study_progress', methods=['GET'])
def get_study_progress():
    sessions = StudySession.query.all()
    total_time = sum(
        (session.end_time - session.start_time).total_seconds()
        for session in sessions
        if session.end_time
    )
    return jsonify({
        'total_sessions': len(sessions),
        'total_time': total_time,
        'average_time': total_time / len(sessions) if sessions else 0
    })

@app.route('/api/dashboard/quick-stats', methods=['GET'])
def get_quick_stats():
    return jsonify({
        'total_words': Word.query.count(),
        'total_groups': Group.query.count(),
        'total_sessions': StudySession.query.count()
    })

# Study Activities Endpoints
@app.route('/api/study_activities/<int:id>', methods=['GET'])
def get_study_activity(id):
    activity = StudyActivity.query.get_or_404(id)
    return jsonify({
        'id': activity.id,
        'name': activity.name
    })

@app.route('/api/study_activities/<int:id>/study_sessions', methods=['GET'])
def get_activity_sessions(id):
    activity = StudyActivity.query.get_or_404(id)
    sessions = [{
        'id': session.id,
        'start_time': session.start_time,
        'end_time': session.end_time
    } for session in activity.sessions]
    return jsonify(sessions)

@app.route('/api/study_activities', methods=['POST'])
def create_study_activity():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Name is required'}), 400
    
    activity = StudyActivity(name=data['name'])
    db.session.add(activity)
    db.session.commit()
    return jsonify({
        'id': activity.id,
        'name': activity.name
    }), 201

# Words Endpoints
@app.route('/api/words', methods=['GET'])
def get_words():
    words = Word.query.all()
    return jsonify([{
        'id': word.id,
        'word': word.word,
        'group_id': word.group_id
    } for word in words])

@app.route('/api/words/<int:id>', methods=['GET'])
def get_word(id):
    word = Word.query.get_or_404(id)
    return jsonify({
        'id': word.id,
        'word': word.word,
        'group_id': word.group_id
    })

# Groups Endpoints
@app.route('/api/groups', methods=['GET'])
def get_groups():
    groups = Group.query.all()
    return jsonify([{
        'id': group.id,
        'name': group.name
    } for group in groups])

@app.route('/api/groups/<int:id>', methods=['GET'])
def get_group(id):
    group = Group.query.get_or_404(id)
    return jsonify({
        'id': group.id,
        'name': group.name
    })

@app.route('/api/groups/<int:id>/words', methods=['GET'])
def get_group_words(id):
    group = Group.query.get_or_404(id)
    return jsonify([{
        'id': word.id,
        'word': word.word
    } for word in group.words])

@app.route('/api/groups/<int:id>/study_sessions', methods=['GET'])
def get_group_sessions(id):
    group = Group.query.get_or_404(id)
    # Assuming there's a relationship between groups and study sessions
    sessions = StudySession.query.filter_by(group_id=id).all()
    return jsonify([{
        'id': session.id,
        'start_time': session.start_time,
        'end_time': session.end_time
    } for session in sessions])

# Study Sessions Endpoints
@app.route('/api/study_sessions', methods=['GET'])
def get_study_sessions():
    sessions = StudySession.query.all()
    return jsonify([{
        'id': session.id,
        'start_time': session.start_time,
        'end_time': session.end_time,
        'activity_id': session.activity_id
    } for session in sessions])

@app.route('/api/study_sessions/<int:id>', methods=['GET'])
def get_study_session(id):
    session = StudySession.query.get_or_404(id)
    return jsonify({
        'id': session.id,
        'start_time': session.start_time,
        'end_time': session.end_time,
        'activity_id': session.activity_id
    })

@app.route('/api/study_sessions/<int:id>/words', methods=['GET'])
def get_session_words(id):
    session = StudySession.query.get_or_404(id)
    # Assuming there's a relationship between sessions and words
    words = Word.query.filter_by(session_id=id).all()
    return jsonify([{
        'id': word.id,
        'word': word.word
    } for word in words])

# Reset Endpoints
@app.route('/api/reset_history', methods=['POST'])
def reset_history():
    StudySession.query.delete()
    db.session.commit()
    return jsonify({'message': 'Study history has been reset successfully'})

@app.route('/api/full_reset', methods=['POST'])
def full_reset():
    StudySession.query.delete()
    Word.query.delete()
    Group.query.delete()
    StudyActivity.query.delete()
    db.session.commit()
    return jsonify({'message': 'All data has been reset successfully'})

@app.route('/api/study_sessions/<int:session_id>/words/<int:word_id>/review', methods=['POST'])
def review_word(session_id, word_id):
    session = StudySession.query.get_or_404(session_id)
    word = Word.query.get_or_404(word_id)
    
    word.last_reviewed = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Word review recorded successfully',
        'word_id': word_id,
        'session_id': session_id,
        'review_time': word.last_reviewed
    })

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'message': 'Internal server error'}), 500

# Initialize Database
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
