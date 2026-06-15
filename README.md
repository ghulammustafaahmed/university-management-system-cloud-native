# ☁️ Cloud-Native Distributed University Management System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=flat&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=flat&logo=bootstrap&logoColor=white)

A **production-grade, cloud-native university management system** built with microservices architecture, containerized with Docker, and orchestrated with Kubernetes. This project modernizes traditional monolithic university portals using industry-standard cloud technologies.

## 📌 Quick Start (System is LIVE!)

> **Your app is running at `http://localhost`** — NGINX serves everything on port 80.


# Clone and run
git clone https://github.com/yourusername/university-management-system.git
cd university-management-system
docker-compose up --build

**Default Login Credentials:**
- Email: `ali@university.edu`
- Password: `password123`


## 🏗️ System Architecture


                    ┌─────────────────────────────────────────┐
                    │            🌐 NGINX Reverse Proxy        │
                    │              (Port 80)                  │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         🎨 Frontend (Flask + Bootstrap)  │
                    │              (Port 5000)                │
                    └─────────────────┬───────────────────────┘
                                      │
        ┌─────────────────┬───────────┼───────────┬─────────────────┐
        │                 │           │           │                 │
    ┌───▼───┐         ┌───▼───┐   ┌───▼───┐   ┌───▼───┐         ┌───▼───┐
    │ 🔐    │         │ 📚    │   │ 📝    │   │ 📊    │         │ 📋    │
    │ Auth  │         │ Reg   │   │ LMS   │   │Result │         │Attendance│
    │:5001  │         │:5002  │   │:5003  │   │:5004  │         │:5005    │
    └───┬───┘         └───┬───┘   └───┬───┘   └───┬───┘         └───┬───┘
        │                 │           │           │                 │
        └─────────────────┴───────────┼───────────┴─────────────────┘
                                      │
                          ┌───────────▼───────────┐
                          │    🗄️ MySQL Database   │
                          │    (Port 3306)        │
                          └───────────────────────┘




## 🚀 Microservices Overview

| Service | HTTP Port | Socket Port | Responsibility |
|---------|-----------|-------------|----------------|
| **🔐 Auth Service** | 5001 | 6001 | JWT authentication, registration, login |
| **📚 Registration** | 5002 | 6002 | Course enrollment, capacity enforcement |
| **📝 LMS Service** | 5003 | 6003 | Assignments, course material management |
| **📊 Result Service** | 5004 | 6004 | Grades, GPA calculation, benchmarking |
| **📋 Attendance** | 5005 | 6005 | Attendance marking, percentage summary |
| **👤 Profile Service** | 5006 | 6006 | Extended profile, live CGPA computation |
| **🎨 Frontend** | 5000 | — | Bootstrap 5 UI, Jinja2 templates |
| **🌐 NGINX Proxy** | 80 | — | Reverse proxy, load balancing |
| **🗄️ MySQL** | 3306 | — | Relational database (8 tables, 3NF) |



## 🛠️ Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Backend | Python / Flask | 3.11 / 3.0 |
| Authentication | Flask-JWT-Extended | 4.7 |
| Database | MySQL | 8.0 |
| Containerization | Docker | 24.0+ |
| Orchestration | Kubernetes / Minikube | 1.32 |
| Reverse Proxy | NGINX (Alpine) | Latest |
| Frontend | Bootstrap 5 / Jinja2 | 5.3 / 3.1 |
| Distributed Comm. | Python Sockets | Built-in |
| Version Control | Git / GitHub | — |



## 📋 Prerequisites

| Requirement | Minimum Version |
|-------------|-----------------|
| Docker Desktop | 24.0+ |
| Minikube (optional) | 1.32+ |
| kubectl (optional) | 1.28+ |
| Git | latest |
| RAM | 8GB+ |
| OS | Windows / macOS / Linux |


## 🔧 Installation & Deployment

### Option 1: Docker Compose (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/university-management-system.git
cd university-management-system

# Start all 9 services
docker-compose up --build

# Access the application
# Open http://localhost in your browser
```

### Option 2: Kubernetes (Minikube) — Production-Style Deployment


# Start Minikube
minikube start --driver=docker --memory=4096 --cpus=2

# Build images inside Minikube
& minikube docker-env | Invoke-Expression
docker build -t auth-service:latest ./auth-service
docker build -t registration-service:latest ./registration-service
docker build -t lms-service:latest ./lms-service
docker build -t result-service:latest ./result-service
docker build -t attendance-service:latest ./attendance-service
docker build -t profile-service:latest ./profile-service
docker build -t frontend:latest ./frontend
docker build -t nginx-proxy:latest ./nginx

# Deploy to Kubernetes
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-mysql.yaml
kubectl apply -f k8s/04-auth-service.yaml
kubectl apply -f k8s/05-registration-service.yaml
kubectl apply -f k8s/06-lms-service.yaml
kubectl apply -f k8s/07-result-service.yaml
kubectl apply -f k8s/08-attendance-service.yaml
kubectl apply -f k8s/09-profile-service.yaml
kubectl apply -f k8s/10-frontend.yaml
kubectl apply -f k8s/11-nginx.yaml

# Get access URL
minikube service nginx-proxy -n university --url
```

### Option 3: Share with Friends on Same WiFi

```bash
# Find your IPv4 address
ipconfig

# Allow port 80 in Windows Firewall
New-NetFirewallRule -DisplayName "Allow Port 80" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# Friends open: http://YOUR_IP_ADDRESS
```

### Option 4: Share Over Internet (ngrok)

```bash
# Install ngrok from https://ngrok.com
ngrok http 80

# Share the public HTTPS URL with anyone, anywhere
```

---

## 📊 Key Demo Commands (For Project Report)

These commands demonstrate Kubernetes capabilities for your academic report:

```bash
# Show all pods running with 2 replicas each
kubectl get pods -n university

# Show CPU and memory usage per pod
minikube addons enable metrics-server
kubectl top pods -n university

# Live horizontal scaling demonstration
kubectl scale deployment auth-service --replicas=4 -n university
kubectl get pods -n university   # Watch 2 new pods spin up

# Check logs of a specific service
kubectl logs -l app=auth-service -n university

# Show all deployments
kubectl get deployments -n university

# Open Kubernetes dashboard
minikube dashboard
```

### Expected Benchmark Results (Multithreading)

| Threads | Total Time (ms) | Avg/Request (ms) | Speedup |
|---------|-----------------|------------------|---------|
| 1 | 487 | 487 | 1.0x |
| 5 | 523 | 104 | 4.7x |
| 10 | 561 | 56 | 8.7x |
| 25 | 612 | 24 | 20.3x |
| 50 | 714 | 14 | 34.8x |
| 100 | 1,243 | 12 | 40.6x |

---

## 🔄 Switching Between Docker Compose and Kubernetes

```bash
# Switch from Kubernetes back to Docker Compose
kubectl delete namespace university
minikube stop
& minikube docker-env --unset | Invoke-Expression
docker-compose up

# Switch from Docker Compose to Kubernetes
docker-compose down
minikube start
& minikube docker-env | Invoke-Expression
# rebuild images (see Option 2 above)
```

---

## 🗄️ Database Schema (8 Tables — 3NF)

| Table | Purpose |
|-------|---------|
| `students` | Core user data (PK: id, email, password_hash) |
| `student_profiles` | Extended profile (1:1 with students) |
| `courses` | Course catalog (PK: id, course_code UNIQUE) |
| `enrollments` | Many-to-many students ↔ courses with status |
| `assignments` | Course assignments (FK: course_id) |
| `results` | Grade records (FK: student_id, course_id) |
| `attendance` | Per-session attendance (UNIQUE student+course+date) |
| `attendance_summary` | Aggregated attendance percentage |

---
## 🔧 Development & Customization

### Rebuilding Individual Services

| Change Type | Command |
|-------------|---------|
| Changed `.py` file | `docker-compose up --build <service-name>` |
| Changed `.html` template | `docker-compose up --build frontend` |
| Changed `init.sql` | `docker-compose down -v` then `docker-compose up --build` |


---

## 📁 Project Structure

```text
university-management-system/
├── auth-service/                 # JWT authentication
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── registration-service/         # Course enrollment
├── lms-service/                  # Learning management
├── result-service/               # Grades + benchmark
├── attendance-service/           # Attendance tracking
├── profile-service/              # Student profiles
├── frontend/                     # Bootstrap 5 UI
│   ├── Dockerfile
│   ├── app.py
│   └── templates/
├── nginx/                        # Reverse proxy config
│   └── nginx.conf
├── k8s/                          # Kubernetes manifests
│   ├── 00-namespace.yaml
│   ├── 01-configmap.yaml
│   ├── 02-secret.yaml
│   ├── 03-mysql.yaml
│   ├── 04-auth-service.yaml
│   ├── 05-registration-service.yaml
│   ├── 06-lms-service.yaml
│   ├── 07-result-service.yaml
│   ├── 08-attendance-service.yaml
│   ├── 09-profile-service.yaml
│   ├── 10-frontend.yaml
│   └── 11-nginx.yaml
├── scripts/
│   └── init.sql                  # Database schema
├── docker-compose.yml
└── README.md
```

---


## 👥 Team Members

| Name | Registration Number | Responsibilities |
|------|---------------------|-----------------|
| **Ghulam Mustafa Ahmed** | BCPE-223005 | Auth Service, Registration, Documentation |
| **Ayaan Ahmed Soomro** | BCPE-223033 | LMS, Result, Benchmarking, Frontend |
| **Muhammad Uzair** | BCPE-223049 | Attendance, Profile, Socket Communication |

## 👩‍🏫 Supervisor

**Madam Areeba Nasim** — Lab Instructor, Department of Electrical and Computer Engineering

## 🎓 Course

**CPE4541: Cloud and Distributed Computing** — Capital University of Science & Technology, Islamabad

---

## 🎯 SDG Alignment

| SDG | Alignment |
|-----|-----------|
| **SDG 4** — Quality Education | Digitizes six core university academic services making quality education accessible and reliable |
| **SDG 9** — Industry, Innovation | Demonstrates cloud-native infrastructure applicable to any modern digital service |
| **SDG 11** — Sustainable Communities | Container-based deployment reduces server hardware redundancy and energy consumption |

---

## 📄 License

MIT License — See [LICENSE](LICENSE) file for details.

---

## 📧 Contact

For any queries regarding this project, please contact the **Department of Electrical and Computer Engineering**, Capital University of Science & Technology, Islamabad.

---

## ⭐ Acknowledgments

- Madam Areeba Nasim for continuous guidance and technical support
- Dr. Waseem Abbas for CPE4541 lectures on microservices and distributed systems
- Dr. Noor Mohammad Khan, HOD, for fostering academic excellence

---

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=flat&logo=mysql&logoColor=white)



