import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Database configuration
DATABASE = 'words.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Helper function for pagination
def paginate(query, page=1, per_page=100):
    offset = (page - 1) * per_page
    items = query[offset:offset + per_page]
    total_items = len(query)
    total_pages = (total_items + per_page - 1) // per_page
    
    return {
        "items": items,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_items,
            "items_per_page": per_page
        }
    }

# API Routes
@app.route('/api/dashboard/last_study_session', methods=['GET'])
def get_last_study_session():
    db = get_db()
    cursor = db.cursor()
    
    query = """
        SELECT ss.*, g.name as group_name 
        FROM study_sessions ss
        JOIN groups g ON ss.group_id = g.id
        ORDER BY ss.created_at DESC
        LIMIT 1
    """
    
    result = cursor.execute(query).fetchone()
    
    if result:
        return jsonify({
            "id": result['id'],
            "group_id": result['group_id'],
            "created_at": result['created_at'],
            "study_activity_id": result['study_activity_id'],
            "group_name": result['group_name']
        })
    return jsonify({"message": "No study sessions found"}), 404

@app.route('/api/dashboard/study_progress', methods=['GET'])
def get_study_progress():
    db = get_db()
    cursor = db.cursor()
    
    total_studied = cursor.execute(
        "SELECT COUNT(DISTINCT word_id) FROM word_review_items"
    ).fetchone()[0]
    
    total_words = cursor.execute(
        "SELECT COUNT(*) FROM words"
    ).fetchone()[0]
    
    return jsonify({
        "total_words_studied": total_studied,
        "total_available_words": total_words
    })

@app.route('/api/dashboard/quick-stats', methods=['GET'])
def get_quick_stats():
    db = get_db()
    cursor = db.cursor()
    
    # Calculate success rate
    stats = cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_count
        FROM word_review_items
    """).fetchone()
    
    success_rate = (stats['correct_count'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    # Get other stats
    total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions").fetchone()[0]
    active_groups = cursor.execute("SELECT COUNT(DISTINCT group_id) FROM study_sessions").fetchone()[0]
    
    return jsonify({
        "success_rate": success_rate,
        "total_study_sessions": total_sessions,
        "total_active_groups": active_groups,
        "study_streak_days": 0  # This would require additional logic to calculate
    })

# Similar implementations for other endpoints...

@app.route('/api/study_sessions/<int:session_id>/words/<int:word_id>/review', methods=['POST'])
def review_word(session_id, word_id):
    db = get_db()
    cursor = db.cursor()
    
    data = request.get_json()
    correct = data.get('correct', False)
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
        VALUES (?, ?, ?, ?)
    """, (word_id, session_id, correct, created_at))
    
    db.commit()
    
    return jsonify({
        "success": True,
        "word_id": word_id,
        "study_session_id": session_id,
        "correct": correct,
        "created_at": created_at
    })

@app.route('/api/reset_history', methods=['POST'])
def reset_history():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM word_review_items")
    cursor.execute("DELETE FROM study_sessions")
    
    db.commit()
    
    return jsonify({
        "success": True,
        "message": "Study history has been reset"
    })

@app.route('/api/full_reset', methods=['POST'])
def full_reset():
    db = get_db()
    cursor = db.cursor()
    
    # Delete all data from all tables
    tables = [
        'word_review_items',
        'study_sessions',
        'study_activities',
        'words_group',
        'words',
        'groups'
    ]
    
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
    
    db.commit()
    
    return jsonify({
        "success": True,
        "message": "System has been fully reset"
    })

if __name__ == '__main__':
    # Create schema.sql file with the following content:
    """
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY,
        japanese TEXT,
        romaji TEXT,
        english TEXT,
        parts TEXT
    );

    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE IF NOT EXISTS words_group (
        id INTEGER PRIMARY KEY,
        words_id INTEGER,
        group_id INTEGER,
        FOREIGN KEY (words_id) REFERENCES words(id),
        FOREIGN KEY (group_id) REFERENCES groups(id)
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY,
        group_id INTEGER,
        study_activity_id INTEGER,
        created_at DATETIME,
        FOREIGN KEY (group_id) REFERENCES groups(id),
        FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
    );

    CREATE TABLE IF NOT EXISTS study_activities (
        id INTEGER PRIMARY KEY,
        study_sessions_id INTEGER,
        group_id INTEGER,
        created_at DATETIME,
        FOREIGN KEY (study_sessions_id) REFERENCES study_sessions(id),
        FOREIGN KEY (group_id) REFERENCES groups(id)
    );

    CREATE TABLE IF NOT EXISTS word_review_items (
        word_id INTEGER,
        study_session_id INTEGER,
        correct BOOLEAN,
        created_at DATETIME,
        FOREIGN KEY (word_id) REFERENCES words(id),
        FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
    );
    """
    
    init_db()
    app.run(debug=True)
