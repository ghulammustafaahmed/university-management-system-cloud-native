from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql, os, requests, time

app = Flask(__name__)
CORS(app)
AUTH_URL = os.getenv('AUTH_SERVICE_URL','http://auth-service:5001')

def get_db():
    return pymysql.connect(host=os.getenv('DB_HOST','localhost'),user=os.getenv('DB_USER','root'),
        password=os.getenv('DB_PASSWORD','rootpassword'),database=os.getenv('DB_NAME','university_system'),
        cursorclass=pymysql.cursors.DictCursor)

def wait_for_db(retries=10, delay=3):
    for i in range(retries):
        try: get_db().close(); print("DB ready!"); return True
        except Exception as e: print(f"Waiting {i+1}/{retries}: {e}"); time.sleep(delay)

def verify_token(token):
    try:
        r = requests.post(f"{AUTH_URL}/verify", headers={'Authorization':f'Bearer {token}'}, timeout=5)
        return r.json().get('student') if r.status_code==200 else None
    except: return None

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def d(*args,**kwargs):
        student = verify_token(request.headers.get('Authorization','').replace('Bearer ',''))
        if not student: return jsonify({'error':'Unauthorized'}),401
        request.student = student
        return f(*args,**kwargs)
    return d

@app.route('/health')
def health(): return jsonify({'status':'Attendance Service Running','port':5005})

@app.route('/summary/<int:student_id>')
@require_auth
def summary(student_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT s.*, c.course_name, c.course_code FROM attendance_summary s
                JOIN courses c ON s.course_id=c.id WHERE s.student_id=%s""", (student_id,))
            return jsonify(cur.fetchall())
    finally: conn.close()

@app.route('/detail/<int:student_id>')
@require_auth
def detail(student_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT a.*, c.course_name, c.course_code FROM attendance a
                JOIN courses c ON a.course_id=c.id WHERE a.student_id=%s ORDER BY a.date DESC LIMIT 50""", (student_id,))
            return jsonify(cur.fetchall())
    finally: conn.close()

@app.route('/mark', methods=['POST'])
@require_auth
def mark_attendance():
    d = request.get_json()
    required = ['student_id','course_id','date','status']
    for f in required:
        if not d.get(f): return jsonify({'error':f'{f} required'}),400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO attendance (student_id,course_id,date,status,marked_by) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE status=%s",
                (d['student_id'],d['course_id'],d['date'],d['status'],request.student['name'],d['status']))
            # Update summary
            cur.execute("SELECT COUNT(*) as total, SUM(status='present' OR status='late') as attended FROM attendance WHERE student_id=%s AND course_id=%s",
                (d['student_id'],d['course_id']))
            row = cur.fetchone()
            pct = round((row['attended']/row['total'])*100,2) if row['total'] else 0
            cur.execute("INSERT INTO attendance_summary (student_id,course_id,total_classes,attended,percentage) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE total_classes=%s,attended=%s,percentage=%s",
                (d['student_id'],d['course_id'],row['total'],row['attended'],pct,row['total'],row['attended'],pct))
        conn.commit()
        return jsonify({'message':'Attendance marked','percentage':pct}),201
    finally: conn.close()

@app.route('/bulk-mark', methods=['POST'])
@require_auth
def bulk_mark():
    """Mark attendance for entire class"""
    d = request.get_json()
    course_id = d.get('course_id')
    date = d.get('date')
    records = d.get('records',[])  # [{student_id, status}]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for rec in records:
                cur.execute("INSERT INTO attendance (student_id,course_id,date,status,marked_by) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE status=%s",
                    (rec['student_id'],course_id,date,rec['status'],request.student['name'],rec['status']))
        conn.commit()
        return jsonify({'message':f'{len(records)} records saved'}),201
    finally: conn.close()

if __name__=='__main__':
    wait_for_db()
    app.run(host='0.0.0.0',port=5005,debug=False)
