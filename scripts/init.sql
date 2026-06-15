CREATE DATABASE IF NOT EXISTS university_system;
USE university_system;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(50),
    semester INT DEFAULT 1,
    phone VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    is_admin TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT UNIQUE NOT NULL,
    bio TEXT,
    cgpa DECIMAL(4,2) DEFAULT 0.00,
    total_credits INT DEFAULT 0,
    father_name VARCHAR(100),
    guardian_phone VARCHAR(20),
    batch_year INT,
    expected_graduation INT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    credits INT DEFAULT 3,
    instructor VARCHAR(100),
    max_students INT DEFAULT 40,
    schedule VARCHAR(100),
    room VARCHAR(50),
    semester INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE,
    max_marks INT DEFAULT 100,
    uploaded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    marks_obtained FLOAT DEFAULT 0,
    max_marks INT DEFAULT 100,
    grade VARCHAR(5),
    semester INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('present','absent','late') DEFAULT 'present',
    marked_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, course_id, date)
);

CREATE TABLE IF NOT EXISTS attendance_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    total_classes INT DEFAULT 0,
    attended INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0.00,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_summary (student_id, course_id)
);

INSERT IGNORE INTO courses (course_code, course_name, department, credits, instructor, max_students, schedule, room, semester) VALUES
('CS101', 'Introduction to Programming', 'Computer Science', 3, 'Dr. Ahmed Khan', 40, 'Mon/Wed 9:00-10:30', 'CS-101', 1),
('CS201', 'Data Structures & Algorithms', 'Computer Science', 3, 'Dr. Sara Ali', 40, 'Tue/Thu 10:00-11:30', 'CS-201', 2),
('CS301', 'Operating Systems', 'Computer Science', 3, 'Dr. Usman Malik', 35, 'Mon/Wed 11:00-12:30', 'CS-301', 3),
('CS401', 'Computer Networks', 'Computer Science', 3, 'Dr. Ayesha Raza', 35, 'Tue/Thu 2:00-3:30', 'CS-401', 4),
('MATH101', 'Calculus I', 'Mathematics', 3, 'Dr. Hassan Siddiqui', 50, 'Mon/Wed/Fri 8:00-9:00', 'MATH-101', 1),
('ENG101', 'English Communication', 'Languages', 2, 'Ms. Fatima Noor', 45, 'Tue/Thu 3:00-4:00', 'ENG-101', 1),
('CS501', 'Machine Learning', 'Computer Science', 3, 'Dr. Bilal Chaudhry', 30, 'Mon/Wed 2:00-3:30', 'CS-501', 5),
('CS601', 'Cloud Computing', 'Computer Science', 3, 'Dr. Zainab Tariq', 30, 'Tue/Thu 11:00-12:30', 'CS-601', 6);

INSERT IGNORE INTO students (name, email, password_hash, roll_number, department, semester, is_admin) VALUES
('Admin User', 'admin@university.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBACuqBgWO1kFi', 'ADMIN-001', 'Administration', 1, 1),
('Ali Hassan', 'ali@university.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBACuqBgWO1kFi', 'CS-2022-001', 'Computer Science', 3, 0),
('Sara Khan', 'sara@university.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBACuqBgWO1kFi', 'CS-2022-002', 'Computer Science', 3, 0);

INSERT IGNORE INTO student_profiles (student_id, cgpa, batch_year, expected_graduation)
SELECT id, 3.5, 2022, 2026 FROM students WHERE roll_number IN ('CS-2022-001','CS-2022-002');

INSERT IGNORE INTO enrollments (student_id, course_id)
SELECT s.id, c.id FROM students s JOIN courses c ON c.course_code IN ('CS101','CS201','MATH101','ENG101')
WHERE s.roll_number='CS-2022-001';

INSERT IGNORE INTO results (student_id, course_id, marks_obtained, max_marks, grade, semester)
SELECT s.id, c.id, 85, 100, 'A', 1 FROM students s JOIN courses c ON c.course_code='CS101' WHERE s.roll_number='CS-2022-001';
INSERT IGNORE INTO results (student_id, course_id, marks_obtained, max_marks, grade, semester)
SELECT s.id, c.id, 72, 100, 'B', 2 FROM students s JOIN courses c ON c.course_code='CS201' WHERE s.roll_number='CS-2022-001';
INSERT IGNORE INTO results (student_id, course_id, marks_obtained, max_marks, grade, semester)
SELECT s.id, c.id, 91, 100, 'A+', 1 FROM students s JOIN courses c ON c.course_code='MATH101' WHERE s.roll_number='CS-2022-001';

INSERT IGNORE INTO attendance_summary (student_id, course_id, total_classes, attended, percentage)
SELECT s.id, c.id, 20, 18, 90.0 FROM students s JOIN courses c ON c.course_code='CS101' WHERE s.roll_number='CS-2022-001';
INSERT IGNORE INTO attendance_summary (student_id, course_id, total_classes, attended, percentage)
SELECT s.id, c.id, 20, 15, 75.0 FROM students s JOIN courses c ON c.course_code='CS201' WHERE s.roll_number='CS-2022-001';
INSERT IGNORE INTO attendance_summary (student_id, course_id, total_classes, attended, percentage)
SELECT s.id, c.id, 15, 14, 93.3 FROM students s JOIN courses c ON c.course_code='MATH101' WHERE s.roll_number='CS-2022-001';
