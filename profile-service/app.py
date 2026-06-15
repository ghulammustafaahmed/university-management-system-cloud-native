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

def wait_for_db(retries=10,delay=3):
    for i in range(retries):
        try: get_db().close(); print("DB ready!"); return True
        except Exception as e: print(f"Waiting {i+1}/{retries}: {e}"); time.sleep(delay)

def verify_token(token):
    try:
        r = requests.post(f"{AUTH_URL}/verify",headers={'Authorization':f'Bearer {token}'},timeout=5)
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
def health(): return jsonify({'status':'Profile Service Running','port':5006})

@app.route('/profile/<int:student_id>')
@require_auth
def get_profile(student_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT s.id,s.name,s.email,s.roll_number,s.department,s.semester,s.phone,s.address,
                p.bio,p.cgpa,p.total_credits,p.father_name,p.guardian_phone,p.batch_year,p.expected_graduation
                FROM students s LEFT JOIN student_profiles p ON s.id=p.student_id WHERE s.id=%s""",(student_id,))
            row = cur.fetchone()
            if not row: return jsonify({'error':'Not found'}),404
            # Calculate live CGPA from results
            cur.execute("SELECT grade FROM results WHERE student_id=%s",(student_id,))
            grades = cur.fetchall()
            gp = {'A+':4.0,'A':4.0,'B':3.0,'C':2.0,'D':1.0,'F':0.0}
            if grades:
                cgpa = round(sum(gp.get(g['grade'],0) for g in grades)/len(grades),2)
                row['cgpa'] = cgpa
                # Update in DB
                cur.execute("UPDATE student_profiles SET cgpa=%s WHERE student_id=%s",(cgpa,student_id))
                conn.commit()
            return jsonify(row)
    finally: conn.close()

@app.route('/profile/<int:student_id>/update', methods=['POST'])
@require_auth
def update_profile(student_id):
    d = request.get_json()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Update students table
            cur.execute("UPDATE students SET phone=%s,address=%s WHERE id=%s",
                (d.get('phone'),d.get('address'),student_id))
            # Upsert profile
            cur.execute("""INSERT INTO student_profiles (student_id,bio,father_name,guardian_phone) VALUES (%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE bio=%s,father_name=%s,guardian_phone=%s""",
                (student_id,d.get('bio'),d.get('father_name'),d.get('guardian_phone'),
                 d.get('bio'),d.get('father_name'),d.get('guardian_phone')))
        conn.commit()
        return jsonify({'message':'Profile updated'})
    finally: conn.close()

@app.route('/all')
@require_auth
def all_profiles():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT s.id,s.name,s.roll_number,s.department,s.semester,p.cgpa
                FROM students s LEFT JOIN student_profiles p ON s.id=p.student_id ORDER BY s.name""")
            return jsonify(cur.fetchall())
    finally: conn.close()

if __name__=='__main__':
    wait_for_db()
    app.run(host='0.0.0.0',port=5006,debug=False)
