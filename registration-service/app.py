from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
import requests
import threading
import time
import socket

app = Flask(__name__)
CORS(app)

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
            conn = get_db()
            conn.close()
            print("Database ready!")
            return True
        except Exception as e:
            print(f"Waiting for DB {i+1}/{retries}: {e}")
            time.sleep(delay)
    return False

def verify_token(token):
    """Verify JWT token with auth service"""
    try:
        resp = requests.post(f"{AUTH_URL}/verify", headers={'Authorization': f'Bearer {token}'}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('student')
    except Exception as e:
        print(f"Auth service error: {e}")
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
    return jsonify({'status': 'Registration Service Running', 'port': 5002})

@app.route('/courses', methods=['GET'])
def list_courses():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, COUNT(e.id) as enrolled_count
                FROM courses c LEFT JOIN enrollments e ON c.id = e.course_id AND e.status='active'
                GROUP BY c.id
            """)
            courses = cursor.fetchall()
        return jsonify(courses)
    finally:
        conn.close()

@app.route('/enroll', methods=['POST'])
@require_auth
def enroll():
    data = request.get_json()
    course_id = data.get('course_id')
    if not course_id:
        return jsonify({'error': 'course_id required'}), 400

    student_id = request.student['id']
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Check course exists and has space
            cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
            course = cursor.fetchone()
            if not course:
                return jsonify({'error': 'Course not found'}), 404

            cursor.execute("SELECT COUNT(*) as cnt FROM enrollments WHERE course_id=%s AND status='active'", (course_id,))
            count = cursor.fetchone()['cnt']
            if count >= course['max_students']:
                return jsonify({'error': 'Course is full'}), 400

            # Check already enrolled
            cursor.execute("SELECT * FROM enrollments WHERE student_id=%s AND course_id=%s", (student_id, course_id))
            if cursor.fetchone():
                return jsonify({'error': 'Already enrolled in this course'}), 409

            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s,%s)", (student_id, course_id))
        conn.commit()
        return jsonify({'message': f'Enrolled in {course["course_name"]} successfully'}), 201
    finally:
        conn.close()

@app.route('/my-courses', methods=['GET'])
@require_auth
def my_courses():
    student_id = request.student['id']
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, e.enrolled_at, e.status
                FROM enrollments e JOIN courses c ON e.course_id = c.id
                WHERE e.student_id = %s AND e.status = 'active'
            """, (student_id,))
            courses = cursor.fetchall()
        return jsonify(courses)
    finally:
        conn.close()

@app.route('/drop', methods=['POST'])
@require_auth
def drop_course():
    data = request.get_json()
    course_id = data.get('course_id')
    student_id = request.student['id']
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE enrollments SET status='dropped' WHERE student_id=%s AND course_id=%s", (student_id, course_id))
        conn.commit()
        return jsonify({'message': 'Course dropped successfully'})
    finally:
        conn.close()

# ─── SOCKET SERVER (Distributed communication) ────────────────────────────────
def run_socket_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 6002))
    s.listen(5)
    print("Registration Socket Server on port 6002")
    while True:
        try:
            conn, addr = s.accept()
            msg = conn.recv(1024).decode('utf-8').strip()
            if msg.startswith("GET_ENROLLMENTS:"):
                student_id = msg.split(":")[1]
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT course_id FROM enrollments WHERE student_id=%s AND status='active'", (student_id,))
                    rows = cur.fetchall()
                db.close()
                ids = ",".join(str(r['course_id']) for r in rows)
                conn.send(f"COURSES:{ids}".encode('utf-8'))
            elif msg == "PING":
                conn.send(b"PONG:registration-service")
            conn.close()
        except Exception as e:
            print(f"Socket error: {e}")

if __name__ == '__main__':
    wait_for_db()
    t = threading.Thread(target=run_socket_server, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5002, debug=False)
