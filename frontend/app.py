from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import requests, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'university-secret-key-2024')
CORS(app)

AUTH_URL    = os.getenv('AUTH_SERVICE_URL',    'http://auth-service:5001')
REG_URL     = os.getenv('REG_SERVICE_URL',     'http://registration-service:5002')
LMS_URL     = os.getenv('LMS_SERVICE_URL',     'http://lms-service:5003')
RESULT_URL  = os.getenv('RESULT_SERVICE_URL',  'http://result-service:5004')
ATTEND_URL  = os.getenv('ATTEND_SERVICE_URL',  'http://attendance-service:5005')
PROFILE_URL = os.getenv('PROFILE_SERVICE_URL', 'http://profile-service:5006')

@app.context_processor
def inject_globals():
    return {'now_hour': datetime.now().hour}

def auth_headers():
    return {'Authorization': f'Bearer {session.get("token","")}'}

def api_get(url):
    try:
        r = requests.get(url, headers=auth_headers(), timeout=5)

        print("GET:", url, r.status_code, r.text)  # DEBUG

        if r.status_code != 200:
            return {"error": r.text, "results": [], "cgpa": 0}

        return r.json()

    except Exception as e:
        print("REQUEST FAILED:", url, str(e))
        return {"error": str(e), "results": [], "cgpa": 0}

def api_post(url, data):
    try:
        headers = auth_headers()
        headers["Content-Type"] = "application/json"

        r = requests.post(url, json=data, headers=headers, timeout=5)

        print("POST:", url)
        print("DATA:", data)
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)

        # SAFE JSON PARSING
        try:
            response_data = r.json()
        except Exception:
            response_data = {"error": "Invalid JSON response", "raw": r.text}

        return response_data, r.status_code

    except Exception as e:
        return {"error": str(e)}, 500

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'token' in session else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data = {
            'email': request.form['email'],
            'password': request.form['password']
        }

        try:
            r = requests.post(f"{AUTH_URL}/login", json=data, timeout=5)
            resp = r.json()

            # ❌ IMPORTANT FIX: check BOTH status AND response
            if r.status_code != 200:
                flash(resp.get('error', 'Invalid email or password'), 'danger')
                return render_template('login.html')

            # ✅ success
            session['token'] = resp['access_token']
            session['student'] = resp['student']
            session['is_admin'] = resp['student'].get('is_admin', 0)

            flash('Welcome back!', 'success')

            return redirect(
                url_for('admin_dashboard') if session['is_admin'] else url_for('dashboard')
            )

        except Exception:
            flash('Auth service unavailable. Please try again.', 'warning')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data = {'name':request.form['name'],'email':request.form['email'],
                'password':request.form['password'],'roll_number':request.form['roll_number'],
                'department':request.form['department'],'semester':int(request.form.get('semester',1))}
        resp, code = api_post(f"{AUTH_URL}/register", data)
        if code == 201:
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        flash(resp.get('error','Registration failed.'), 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    sid = session['student']['id']
    courses     = api_get(f"{REG_URL}/my-courses")
    results     = api_get(f"{RESULT_URL}/results")
    profile     = api_get(f"{PROFILE_URL}/profile/{sid}")
    attendance  = api_get(f"{ATTEND_URL}/summary/{sid}")
    assignments = api_get(f"{LMS_URL}/assignments")
    return render_template('dashboard.html', student=session['student'],
        courses=courses if isinstance(courses,list) else [],
        results=results, profile=profile,
        attendance=attendance if isinstance(attendance,list) else [],
        assignments=assignments if isinstance(assignments,list) else [])

@app.route('/admin')
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required.','danger')
        return redirect(url_for('dashboard'))
    students = api_get(f"{AUTH_URL}/students")
    courses  = api_get(f"{REG_URL}/courses")
    stats = {'students': len(students) if isinstance(students,list) else 0,
             'courses':  len(courses)  if isinstance(courses,list)  else 0}
    return render_template('admin_dashboard.html', students=students, courses=courses, stats=stats)

@app.route('/courses')
@login_required
def courses():
    all_c  = api_get(f"{REG_URL}/courses")
    my_c   = api_get(f"{REG_URL}/my-courses")
    enrolled_ids = {c['id'] for c in (my_c if isinstance(my_c,list) else [])}
    return render_template('courses.html', courses=all_c if isinstance(all_c,list) else [], enrolled_ids=enrolled_ids)

@app.route('/courses/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    resp, code = api_post(f"{REG_URL}/enroll", {'course_id': course_id})
    flash(resp.get('message', resp.get('error','')), 'success' if code==201 else 'danger')
    return redirect(url_for('courses'))

@app.route('/courses/drop/<int:course_id>', methods=['POST'])
@login_required
def drop(course_id):
    resp, code = api_post(f"{REG_URL}/drop", {'course_id': course_id})
    flash(resp.get('message', resp.get('error','')), 'success' if code==200 else 'danger')
    return redirect(url_for('courses'))

@app.route('/results')
@login_required
def results():
    data = api_get(f"{RESULT_URL}/results")

    results = []
    cgpa = 0

    if isinstance(data, dict):
        results = data.get("results", [])
        cgpa = data.get("cgpa", 0)

    return render_template(
        'results.html',
        results=results,
        cgpa=cgpa
    )
@app.route('/attendance')
@login_required
def attendance():
    sid = session['student']['id']
    summary = api_get(f"{ATTEND_URL}/summary/{sid}")
    detail  = api_get(f"{ATTEND_URL}/detail/{sid}")
    return render_template('attendance.html', summary=summary if isinstance(summary,list) else [], detail=detail)

@app.route('/profile')
@login_required
def profile():
    data = api_get(f"{PROFILE_URL}/profile/{session['student']['id']}")
    return render_template('profile.html', profile=data)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    sid = session['student']['id']
    data = {k: request.form.get(k,'') for k in ['bio','father_name','guardian_phone','phone','address']}
    resp, code = api_post(f"{PROFILE_URL}/profile/{sid}/update", data)
    flash('Profile updated!' if code==200 else resp.get('error','Update failed'), 'success' if code==200 else 'danger')
    return redirect(url_for('profile'))

@app.route('/assignments')
@login_required
def assignments():
    data = api_get(f"{LMS_URL}/assignments")
    return render_template('assignments.html', assignments=data if isinstance(data,list) else [])
#ADMIN ATTENDANCE ROUTE
@app.route('/admin/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    data = {
        "student_id": request.form['student_id'],
        "course_id": request.form['course_id'],
        "date": request.form['date'],
        "status": request.form['status']
    }

    resp, code = api_post(f"{ATTEND_URL}/mark", data)

    flash(
        resp.get('message', resp.get('error', 'Attendance updated')),
        'success' if code == 200 else 'danger'
    )

    return redirect(url_for('admin_dashboard'))
#ADMIN RESULTS ROUTE
@app.route('/admin/assessments/add', methods=['POST'])
@login_required
def add_assessment():
    try:
        data = {
            "student_id": request.form['student_id'],
            "course_id": request.form['course_id'],
            "assessment_type": request.form['assessment_type'],
            "attempt_no": request.form.get('attempt_no', 1),
            "marks_obtained": request.form['marks_obtained'],
            "max_marks": request.form['max_marks']
        }

        resp, code = api_post(f"{RESULT_URL}/assessments", data)
        print("ASSESSMENT RESPONSE:", resp, code)

        flash(
            resp.get('message', resp.get('error', 'Saved')),
            'success' if code == 201 else 'danger'
        )

        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        flash(f"Assessment failed: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))
@app.route('/admin/assignments/add', methods=['POST'])
@login_required
def admin_add_assignment():
    """Forward the assignment form data and file to the LMS service"""
    if not session.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard'))

    # Extract all text fields from the form
    data = dict(request.form)
    
    # Extract the file buffer
    files = {}
    file = request.files.get('file')
    if file and file.filename != '':
        # Package the file for the requests library
        files = {'file': (file.filename, file.read(), file.content_type)}

    try:
        headers = auth_headers()
        # Important: Let 'requests' handle the Content-Type header for multipart/form-data automatically
        r = requests.post(f"{LMS_URL}/assignments", data=data, files=files, headers=headers, timeout=10)
        
        if r.status_code == 201:
            flash('Assignment uploaded successfully!', 'success')
        else:
            # Grab the error from the backend JSON response
            backend_error = r.json().get('error', 'Failed to upload assignment')
            flash(f"Upload Error: {backend_error}", 'danger')
            
    except Exception as e:
        flash(f"Proxy Connection Error: Could not reach LMS Service. {str(e)}", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/assignments/download/<filename>')
def proxy_download(filename):
    # Ask the LMS service for the file
    LMS_URL = os.getenv('LMS_SERVICE_URL', 'http://lms-service:5003')
    response = requests.get(f"{LMS_URL}/assignments/download/{filename}", stream=True)
    
    if response.status_code == 200:
        from flask import Response
        # Return the file content to the user's browser
        return Response(response.content, headers=dict(response.headers))
    return "File not found", 404

@app.route('/ai-chat', methods=['POST'])
@login_required
def ai_chat():
    question = request.json.get('question','')
    student = session['student']
    results_data = api_get(f"{RESULT_URL}/results")
    system_prompt = f"""You are a helpful university academic advisor AI assistant for UniPortal.
Student: {student['name']}, Department: {student['department']}, Semester: {student['semester']}
Current GPA: {results_data.get('gpa','N/A') if isinstance(results_data,dict) else 'N/A'}
Answer questions about academics, study tips, course advice, and university life.
Be concise, friendly, and helpful. Keep responses under 150 words."""
    try:
        import urllib.request, json as _json
        payload = _json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":300,
            "system":system_prompt,"messages":[{"role":"user","content":question}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
            headers={"Content-Type":"application/json","anthropic-version":"2023-06-01"},method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            reply = data['content'][0]['text']
    except:
        reply = f"Great question! For '{question}' — I recommend checking your course materials, speaking with your academic advisor, or visiting the student services office. I'm here to help guide your academic journey!"
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
