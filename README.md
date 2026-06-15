# University Management System v2 — AI-Enhanced

## Architecture
Internet → NGINX (port 80) → Frontend (port 5000) → 6 Microservices → MySQL

## Services
| Service | Port | Purpose |
|---------|------|---------|
| NGINX | 80 | Reverse proxy, rate limiting |
| Frontend | 5000 | Web UI (Flask + Bootstrap 5) |
| Auth | 5001 | Login, JWT tokens |
| Registration | 5002 | Course enrollment |
| LMS | 5003 | Assignments, materials |
| Result | 5004 | Grades, GPA |
| Attendance | 5005 | Attendance tracking |
| Profile | 5006 | Student profiles |
| MySQL | 3309 | Database |

## Quick Start
```bash
docker-compose up --build
```
Then open: http://localhost

## Demo Credentials
- Admin: admin@university.edu / password123
- Student: ali@university.edu / password123
