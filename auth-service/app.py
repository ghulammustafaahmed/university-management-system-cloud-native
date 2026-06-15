from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymysql
import bcrypt
import os
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'supersecretkey123')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
jwt = JWTManager(app)

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
            print("Database connection successful!")
            return True
        except Exception as e:
            print(f"Waiting for DB... attempt {i+1}/{retries}: {e}")
            time.sleep(delay)
    return False

# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Auth Service Running', 'port': 5001})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['name', 'email', 'password', 'roll_number', 'department']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO students (name, email, password_hash, roll_number, department, semester) VALUES (%s,%s,%s,%s,%s,%s)",
                (data['name'], data['email'], password_hash, data['roll_number'], data['department'], data.get('semester', 1))
            )
        conn.commit()
        return jsonify({'message': 'Student registered successfully'}), 201
    except pymysql.err.IntegrityError as e:
        return jsonify({'error': 'Email or roll number already exists'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students WHERE email = %s", (data['email'],))
            student = cursor.fetchone()

        if not student:
            return jsonify({'error': 'Invalid credentials'}), 401

        stored_hash = student['password_hash'].encode('utf-8')
        password = data['password'].encode('utf-8')

        if not bcrypt.checkpw(password, stored_hash):
            return jsonify({'error': 'Invalid credentials'}), 401

        token = create_access_token(identity=str(student['id']))

        return jsonify({
            'access_token': token,
            'student': {
                'id': student['id'],
                'name': student['name'],
                'email': student['email'],
                'roll_number': student['roll_number'],
                'department': student['department'],
                'is_admin': student.get('is_admin', 0)
            }
        })

    finally:
        conn.close()

@app.route('/verify', methods=['POST'])
def verify_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'error': 'Missing token'}), 401

    from flask_jwt_extended import decode_token

    try:
        decoded = decode_token(token)
        student_id = decoded['sub']
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, roll_number, department, semester, is_admin
                FROM students WHERE id = %s
            """, (student_id,))
            student = cursor.fetchone()

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({'student': student})
    finally:
        conn.close()
    """Endpoint for other services to verify tokens"""
    student_id = get_jwt_identity()
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, roll_number, department FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        return jsonify({'valid': True, 'student': student})
    finally:
        conn.close()

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    student_id = get_jwt_identity()
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, roll_number, department, semester, created_at FROM students WHERE id = %s", (student_id,))
            student = cursor.fetchone()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        return jsonify(student)
    finally:
        conn.close()
@app.route('/students', methods=['GET'])
def list_students():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'error': 'Missing token'}), 401

    from flask_jwt_extended import decode_token

    try:
        decode_token(token)  # just validate token
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, roll_number, department, semester, is_admin, created_at
                FROM students
                ORDER BY name
            """)
            students = cursor.fetchall()

        return jsonify(students)

    finally:
        conn.close()

# ─── DISTRIBUTED SOCKET SERVER ──────────────────────────────────────────────
import socket

def run_socket_server():
    """Python socket server for distributed service communication"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 6001))
    s.listen(5)
    print("Auth Socket Server listening on port 6001")
    while True:
        try:
            conn, addr = s.accept()
            msg = conn.recv(1024).decode('utf-8').strip()
            if msg.startswith("VERIFY_STUDENT:"):
                student_id = msg.split(":")[1]
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT id, name, email FROM students WHERE id=%s", (student_id,))
                    row = cur.fetchone()
                db.close()
                response = f"VALID:{row['name']}:{row['email']}" if row else "INVALID"
                conn.send(response.encode('utf-8'))
            elif msg == "PING":
                conn.send(b"PONG:auth-service")
            conn.close()
        except Exception as e:
            print(f"Socket error: {e}")

if __name__ == '__main__':
    wait_for_db()
    t = threading.Thread(target=run_socket_server, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5001, debug=False)


