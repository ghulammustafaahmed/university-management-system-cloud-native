from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
import requests
import threading
import time
import socket
import concurrent.futures

app = Flask(__name__)
CORS(app)
AUTH_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001')
REG_URL  = os.getenv('REGISTRATION_SERVICE_URL', 'http://registration-service:5002')

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

def calculate_grade(marks, max_marks):
    pct = (marks / max_marks) * 100 if max_marks > 0 else 0
    if pct >= 90: return 'A+'
    elif pct >= 80: return 'A'
    elif pct >= 70: return 'B'
    elif pct >= 60: return 'C'
    elif pct >= 50: return 'D'
    return 'F'

def calculate_course_result(assessments):
    def avg(items):
        if not items:
            return 0
        return sum(float(i['marks_obtained']) / float(i['max_marks']) for i in items) / len(items)

    quizzes = [a for a in assessments if a['assessment_type'] == 'quiz']
    assignments = [a for a in assessments if a['assessment_type'] == 'assignment']
    midterms = [a for a in assessments if a['assessment_type'] == 'midterm']
    projects = [a for a in assessments if a['assessment_type'] == 'project']
    finals = [a for a in assessments if a['assessment_type'] == 'final']

    quiz_score = avg(quizzes) * 20
    assignment_score = avg(assignments) * 10
    midterm_score = avg(midterms) * 20
    project_score = avg(projects) * 10
    final_score = avg(finals) * 40

    pct = quiz_score + assignment_score + midterm_score + project_score + final_score
    return round(pct, 2)

def calculate_gpa_from_percentage(pct):
    if pct >= 90: return 4.0
    if pct >= 80: return 3.7
    if pct >= 70: return 3.0
    if pct >= 60: return 2.0
    if pct >= 50: return 1.0
    return 0.0

# Helper function to compute a baseline GPA from raw database letter grades (used by Socket Server)
def calculate_gpa_from_grades(rows):
    grade_map = {'A+': 4.0, 'A': 3.7, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    if not rows: return 0.0
    total = sum(grade_map.get(r['grade'], 0.0) for r in rows)
    return round(total / len(rows), 2)

# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Result Service Running', 'port': 5004})

@app.route('/results', methods=['GET'])
@require_auth
def my_results():
    student_id = request.student['id']
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, c.course_name, c.course_code
                FROM assessments a
                JOIN courses c ON a.course_id = c.id
                WHERE a.student_id = %s
                ORDER BY a.course_id, a.assessment_type
            """, (student_id,))
            rows = cursor.fetchall()

        from collections import defaultdict
        grouped = defaultdict(list)
        for r in rows:
            grouped[r['course_id']].append(r)

        results = []
        total_gpa = 0
        count = 0

        for course_id, assessments in grouped.items():
            by_type = defaultdict(list)
            for a in assessments:
                by_type[a['assessment_type']].append(a)

            breakdown = {}
            for atype, items in by_type.items():
                breakdown[atype] = {
                    "items": [
                        {
                            "id": item["id"],
                            "assessment_type": item["assessment_type"],
                            "marks_obtained": float(item["marks_obtained"]),
                            "max_marks": float(item["max_marks"]),
                            "attempt_no": item.get("attempt_no", 1),
                            "percentage": round(
                                (float(item["marks_obtained"]) / float(item["max_marks"])) * 100
                                if float(item["max_marks"]) else 0, 2
                            )
                        } for item in items
                    ],
                    "percentage": round(
                        sum(
                            (float(i["marks_obtained"]) / float(i["max_marks"])) * 100
                            for i in items if float(i["max_marks"])
                        ) / len(items) if items else 0, 2
                    )
                }

            quiz_score = breakdown.get('quiz', {}).get('percentage', 0)
            assignment_score = breakdown.get('assignment', {}).get('percentage', 0)
            midterm_score = breakdown.get('midterm', {}).get('percentage', 0)
            project_score = breakdown.get('project', {}).get('percentage', 0)
            final_score = breakdown.get('final', {}).get('percentage', 0)

            pct = (
                quiz_score * 0.2 +
                assignment_score * 0.1 +
                midterm_score * 0.2 +
                project_score * 0.1 +
                final_score * 0.4
            )

            grade = calculate_grade(pct, 100)
            gpa = calculate_gpa_from_percentage(pct)

            results.append({
                "course_id": course_id,
                "course_name": assessments[0]['course_name'],
                "course_code": assessments[0]['course_code'],
                "percentage": round(pct, 2),
                "grade": grade,
                "gpa": gpa,
                "breakdown": breakdown
            })
            total_gpa += gpa
            count += 1

        cgpa = round(total_gpa / count, 2) if count else 0
        return jsonify({"results": results, "cgpa": cgpa})
    finally:
        conn.close()

@app.route('/assessments', methods=['POST'])
@require_auth
def add_assessment():
    """Add assessment marks (quiz, midterm, assignment, project, final)"""
    try:
        data = request.get_json(silent=True)
        print("RECEIVED DATA:", data)

        if not data:
            return jsonify({'error': 'Invalid or missing JSON body'}), 400

        required = ['student_id', 'course_id', 'assessment_type', 'marks_obtained', 'max_marks']
        for f in required:
            if f not in data or data[f] is None:
                return jsonify({'error': f'{f} is required'}), 400

        # Type conversion backup safety layer
        try:
            student_id = int(data['student_id'])
            course_id = int(data['course_id'])
            attempt_no = int(data.get('attempt_no', 1))
            marks_obtained = float(data['marks_obtained'])
            max_marks = float(data['max_marks'])
            semester = int(data.get('semester', 1))
        except (ValueError, TypeError) as type_err:
            return jsonify({'error': f'Data type casting verification failed: {str(type_err)}'}), 400

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # 1. INSERT assessment
                cursor.execute("""
                    INSERT INTO assessments
                    (student_id, course_id, assessment_type, attempt_no, marks_obtained, max_marks, semester)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (student_id, course_id, data['assessment_type'], attempt_no, marks_obtained, max_marks, semester))

                # 2. GET all assessments for course
                cursor.execute("""
                    SELECT * FROM assessments WHERE student_id=%s AND course_id=%s
                """, (student_id, course_id))
                assessments = cursor.fetchall()

                # 3. CALCULATE RESULT
                percentage = calculate_course_result(assessments)
                grade = calculate_grade(percentage, 100)
                gpa = calculate_gpa_from_percentage(percentage)

                # 4. UPSERT course_results
                cursor.execute("""
                    INSERT INTO course_results
                    (student_id, course_id, semester, total_marks, percentage, grade, gpa_points)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        total_marks=%s, percentage=%s, grade=%s, gpa_points=%s
                """, (
                    student_id, course_id, semester, percentage, percentage, grade, gpa,
                    percentage, percentage, grade, gpa
                ))

            conn.commit()
            return jsonify({
                "message": "Assessment saved and results updated successfully",
                "percentage": percentage,
                "grade": grade,
                "gpa": gpa
            }), 201
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/transcript/<int:student_id>', methods=['GET'])
@require_auth
def transcript(student_id):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.*, c.course_name, c.course_code, c.credits,
                       s.name as student_name, s.roll_number
                FROM results r
                JOIN courses c ON r.course_id = c.id
                JOIN students s ON r.student_id = s.id
                WHERE r.student_id = %s ORDER BY r.semester
            """, (student_id,))
            results = cursor.fetchall()
        pct = calculate_course_result(results)
        gpa = calculate_gpa_from_percentage(pct)
        return jsonify({
            'student_id': student_id,
            'gpa': gpa,
            'results': results,
            'total_credits': sum(r.get('credits', 3) for r in results)
        })
    finally:
        conn.close()

# ─── MULTITHREADING BENCHMARK ─────────────────────────────────────────────────
@app.route('/benchmark', methods=['POST'])
def run_benchmark():
    data = request.get_json() or {}
    num_users = data.get('num_users', 50)
    results_list = []
    lock = threading.Lock()
    import time as t

    def simulate_db_query(user_id):
        start = t.time()
        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM students")
                cur.fetchone()
            conn.close()
            elapsed = t.time() - start
            with lock:
                results_list.append({'user': user_id, 'time_ms': round(elapsed*1000, 2), 'status': 'success'})
        except Exception as e:
            with lock:
                results_list.append({'user': user_id, 'time_ms': 0, 'status': 'error'})

    start_all = t.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(simulate_db_query, i) for i in range(num_users)]
        concurrent.futures.wait(futures)
    total_time = round((t.time() - start_all) * 1000, 2)
    avg_time = round(sum(r['time_ms'] for r in results_list) / len(results_list), 2) if results_list else 0

    return jsonify({
        'num_users': num_users,
        'total_time_ms': total_time,
        'avg_response_ms': avg_time,
        'successful': sum(1 for r in results_list if r['status'] == 'success'),
        'failed': sum(1 for r in results_list if r['status'] == 'error'),
        'results': results_list
    })

# ─── SOCKET SERVER ────────────────────────────────────────────────────────────
def run_socket_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 6004))
    s.listen(5)
    print("Result Socket Server on port 6004")
    while True:
        try:
            conn, addr = s.accept()
            msg = conn.recv(1024).decode().strip()
            if msg.startswith("GET_GPA:"):
                student_id = msg.split(":")[1]
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT grade FROM course_results WHERE student_id=%s", (student_id,))
                    rows = cur.fetchall()
                db.close()
                # FIX: Called correct helper mapping function to avoid thread crashing
                gpa = calculate_gpa_from_grades(rows) if rows else 0.0
                conn.send(f"GPA:{gpa}".encode())
            elif msg == "PING":
                conn.send(b"PONG:result-service")
            conn.close()
        except Exception as e:
            print(f"Socket error: {e}")

if __name__ == '__main__':
    wait_for_db()
    t = threading.Thread(target=run_socket_server, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5004, debug=False)