import os
import socket
import threading
import time
import requests
import pymysql  # type: ignore
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from functools import wraps

# 1. Initialize the app ONCE
app = Flask(__name__)
CORS(app)

# 2. Set configuration on that instance
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 3. Set global variables
AUTH_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001')

def get_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'rootpassword'),
        database=os.getenv('DB_NAME', 'university_system'),
        cursorclass=pymysql.cursors.DictCursor
    )

def wait_for_db(retries=10, delay=3):
    for i in range(retries):
        try:
            get_db().close()
            print("DB ready!")
            return True
        except Exception as e:
            print(f"Waiting {i+1}/{retries}: {e}")
            time.sleep(delay)

def verify_token(token):
    try:
        resp = requests.post(f"{AUTH_URL}/verify", headers={'Authorization': f'Bearer {token}'}, timeout=5)
        return resp.json().get('student') if resp.status_code == 200 else None
    except:
        return None

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        student = verify_token(token)
        if not student:
            return jsonify({'error': 'Unauthorized'}), 401
        request.student = student
        return f(*args, **kwargs)
    return decorated

# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'LMS Service Running', 'port': 5003})

@app.route('/assignments', methods=['GET'])
@require_auth
def list_assignments():
    """Get assignments for all courses the student is enrolled in"""
    student_id = request.student['id']
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, c.course_name, c.course_code
                FROM assignments a
                JOIN courses c ON a.course_id = c.id
                WHERE a.course_id IN (
                    SELECT course_id FROM enrollments WHERE student_id=%s
                )
                ORDER BY a.due_date ASC
            """, (student_id,))
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

@app.route('/assignments', methods=['POST'])
@require_auth
def create_assignment():
    # FIX: Read from form data if available (multipart), otherwise fall back to JSON mapping
    if request.form:
        data = request.form
    else:
        data = request.get_json(silent=True) or {}
    
    # 1. Handle File Upload
    file_path = None
    file = request.files.get('file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_path = filename

    # 2. Database Operation
    try:
        course_id = int(data.get('course_id', 0))
        title = data.get('title')
        due_date = data.get('due_date')
        max_marks = int(data.get('max_marks', 100))
        uploaded_by = getattr(request, 'student', {}).get('name', 'Admin')
        description = data.get('description', '')

        conn = get_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO assignments 
                     (course_id, title, description, due_date, max_marks, uploaded_by, file_path) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (course_id, title, description, due_date, max_marks, uploaded_by, file_path))
        conn.commit()
        return jsonify({'message': 'Assignment created successfully'}), 201

    except Exception as e:
        import traceback
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

# 4. Add the missing Download Route
@app.route('/assignments/download/<filename>', methods=['GET'])
def download_assignment(filename):
    """Serve the requested file to the user without auth"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/assignments/<int:course_id>', methods=['GET'])
@require_auth
def course_assignments(course_id):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM assignments WHERE course_id=%s ORDER BY due_date", (course_id,))
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

@app.route('/courses/<int:course_id>/material', methods=['GET'])
@require_auth
def course_material(course_id):
    """Simulate course materials (static for demo)"""
    materials = [
        {'type': 'lecture', 'title': 'Week 1 - Introduction', 'file': 'week1.pdf'},
        {'type': 'lecture', 'title': 'Week 2 - Core Concepts', 'file': 'week2.pdf'},
        {'type': 'video',   'title': 'Tutorial Video 1',       'url': 'https://example.com/video1'},
        {'type': 'reading', 'title': 'Reference Book Chapter 1', 'pages': '1-25'},
    ]
    return jsonify({'course_id': course_id, 'materials': materials})

# ─── SOCKET SERVER ────────────────────────────────────────────────────────────
def run_socket_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 6003))
    s.listen(5)
    print("LMS Socket Server on port 6003")
    while True:
        try:
            conn, addr = s.accept()
            msg = conn.recv(1024).decode().strip()
            if msg.startswith("GET_ASSIGNMENTS:"):
                course_id = msg.split(":")[1]
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as cnt FROM assignments WHERE course_id=%s", (course_id,))
                    cnt = cur.fetchone()['cnt']
                db.close()
                conn.send(f"ASSIGNMENT_COUNT:{cnt}".encode())
            elif msg == "PING":
                conn.send(b"PONG:lms-service")
            conn.close()
        except Exception as e:
            print(f"Socket error: {e}")

if __name__ == '__main__':
    wait_for_db()
    t = threading.Thread(target=run_socket_server, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5003, debug=False)