from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Models
class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    activity_id = db.Column(db.Integer, db.ForeignKey('study_activity.id'), nullable=False)
    words = db.relationship('WordStudySession', backref='study_session', lazy=True)

class StudyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    study_sessions = db.relationship('StudySession', backref='activity', lazy=True)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    study_sessions = db.relationship('StudySession', secondary='word_study_session')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    words = db.relationship('Word', backref='group', lazy=True)
    study_sessions = db.relationship('StudySession', secondary='group_study_session')

# Association tables
word_study_session = db.Table('word_study_session',
    db.Column('word_id', db.Integer, db.ForeignKey('word.id'), primary_key=True),
    db.Column('study_session_id', db.Integer, db.ForeignKey('study_session.id'), primary_key=True)
)

group_study_session = db.Table('group_study_session',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('study_session_id', db.Integer, db.ForeignKey('study_session.id'), primary_key=True)
)

# Routes
@app.route('/api/dashboard/last_study_session', methods=['GET'])
def get_last_study_session():
    session = StudySession.query.order_by(StudySession.start_time.desc()).first()
    if session:
        return jsonify({'id': session.id, 'start_time': session.start_time, 'end_time': session.end_time})
    return jsonify({"message": "No study sessions found"}), 404

@app.route('/api/dashboard/study_progress', methods=['GET'])
def get_study_progress():
    # Example: Total time spent studying
    total_time = 0
    sessions = StudySession.query.all()
    for session in sessions:
        if session.start_time and session.end_time:
            delta = session.end_time - session.start_time
            total_time += delta.total_seconds()
    return jsonify({'total_time': total_time})

@app.route('/api/dashboard/quick-stats', methods=['GET'])
def get_quick_stats():
    total_sessions = StudySession.query.count()
    total_words = Word.query.count()
    return jsonify({'total_sessions': total_sessions, 'total_words': total_words})

@app.route('/api/study_activities/<int:activity_id>', methods=['GET'])
def get_study_activity(activity_id):
    activity = StudyActivity.query.get(activity_id)
    if activity:
        return jsonify({'id': activity.id, 'name': activity.name})
    return jsonify({"message": "Study activity not found"}), 404

@app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
def get_activity_study_sessions(activity_id):
       
    activity = StudyActivity.query.get(activity_id)
    if activity:
        sessions = [{'id': s.id, 'start_time': s.start_time, 'end_time': s.end_time} for s in activity.study_sessions]
        return jsonify(sessions)
    return jsonify({"message": "Study activity not found"}), 404

@app.route('/api/study_activities', methods=['POST'])
def create_study_activity():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({"message": "Name is required"}), 400
    activity = StudyActivity(name=data['name'])
    db.session.add(activity)
    db.session.commit()
    return jsonify({'id': activity.id, 'name': activity.name}), 201

@app.route('/api/words', methods=['GET'])
def get_all_words():
    words = Word.query.all()
    return jsonify([{'id': word.id, 'word': word.word, 'group_id': word.group_id} for word in words])

@app.route('/api/words/<int:word_id>', methods=['GET'])
def get_word(word_id):
    word = Word.query.get(word_id)
    if word:
        return jsonify({'id': word.id, 'word': word.word, 'group_id': word.group_id})
    return jsonify({"message": "Word not found"}), 404

@app.route('/api/groups', methods=['GET'])
def get_all_groups():
    groups = Group.query.all()
    return jsonify([{'id': group.id, 'name': group.name} for group in groups])

@app.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    group = Group.query.get(group_id)
    if group:
        return jsonify({'id': group.id, 'name': group.name})
    return jsonify({"message": "Group not found"}), 404

@app.route('/api/groups/<int:group_id>/words', methods=['GET'])
def get_group_words(group_id):
    group = Group.query.get(group_id)
    if group:
        words = [{'id': word.id, 'word': word.word} for word in group.words]
        return jsonify(words)
    return jsonify({"message": "Group not found"}), 404

@app.route('/api/groups/<int:group_id>/study_sessions', methods=['GET'])
def get_group_study_sessions(group_id):
    group = Group.query.get(group_id)
    if group:
        sessions = [{'id': s.id, 'start_time': s.start_time, 'end_time': s.end_time} for s in group.study_sessions]
        return jsonify(sessions)
    return jsonify({"message": "Group not found"}), 404

@app.route('/api/study_sessions', methods=['GET'])
def get_all_study_sessions():
    sessions = StudySession.query.all()
    return jsonify([{'id': s.id, 'start_time': s.start_time, 'end_time': s.end_time} for s in sessions])

@app.route('/api/study_sessions/<int:session_id>', methods=['GET'])
def get_study_session(session_id):
    session = StudySession.query.get(session_id)
    if session:
        return jsonify({'id': session.id, 'start_time': session.start_time, 'end_time': session.end_time})
    return jsonify({"message": "Study session not found"}), 404

@app.route('/api/study_sessions/<int:session_id>/words', methods=['GET'])
def get_session_words(session_id):
    session = StudySession.query.get(session_id)
    if session:
        words = [{'id': word.id, 'word': word.word} for word in session.words]
        return jsonify(words)
    return jsonify({"message": "Study session not found"}), 404

@app.route('/api/reset_history', methods=['POST'])
def reset_history():
    # Logic to reset study history (e.g., delete study sessions)
    StudySession.query.delete()
    db.session.commit()
    return jsonify({"message": "Study history has been reset"})

@app.route('/api/full_reset', methods=['POST'])
def full_reset():
    # Logic to reset all data
    db.session.query(StudySession).delete()
    db.session.query(StudyActivity).delete()
    db.session.query(Word).delete()
    db.session.query(Group).delete()
    db.session.commit()
    return jsonify({"message": "All data has been reset"})

@app.route('/api/study_sessions/<int:session_id>/words/<int:word_id>/review', methods=['POST'])
def review_word(session_id, word_id):
    # Logic to record a review action
    word = Word.query.get(word_id)
    if word:
        word.last_reviewed = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Review recorded successfully"})
    return jsonify({"message": "Word not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
