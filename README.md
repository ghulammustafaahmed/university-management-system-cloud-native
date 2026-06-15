```markdown
# ☁️ Cloud-Native Distributed University Management System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=flat&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=flat&logo=bootstrap&logoColor=white)

A production-grade cloud-native university management system built using a microservices architecture. The system is containerized with Docker and orchestrated using Kubernetes, modernizing traditional monolithic university systems with scalable distributed design.

---

## 🚀 Quick Start

The system runs behind an NGINX reverse proxy and is accessible at:

```

[http://localhost](http://localhost)

````

### Run with Docker Compose

```bash
git clone https://github.com/yourusername/university-management-system.git
cd university-management-system
docker-compose up --build
````

### Default Login

* Email: `ali@university.edu`
* Password: `password123`

---

## 🏗️ System Architecture

```
                    ┌────────────────────────────────────┐
                    │        NGINX Reverse Proxy          │
                    │              Port 80                │
                    └───────────────┬────────────────────┘
                                    │
                    ┌───────────────▼────────────────────┐
                    │     Frontend (Flask + Bootstrap)    │
                    │              Port 5000             │
                    └───────────────┬────────────────────┘
                                    │
     ┌──────────────┬──────────────┼──────────────┬──────────────┐
     │              │              │              │              │
┌────▼────┐  ┌──────▼─────┐  ┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│ Auth    │  │ Registration│  │ LMS       │  │ Results  │  │Attendance│
│ 5001    │  │ 5002        │  │ 5003      │  │ 5004     │  │ 5005     │
└────┬────┘  └──────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │              │              │
     └──────────────┴──────────────┼──────────────┴──────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │     MySQL DB        │
                         │     Port 3306       │
                         └─────────────────────┘
```

---

## 🧩 Microservices Overview

| Service              | HTTP Port | Socket Port | Responsibility                 |
| -------------------- | --------- | ----------- | ------------------------------ |
| Auth Service         | 5001      | 6001        | Authentication, JWT issuance   |
| Registration Service | 5002      | 6002        | Course enrollment management   |
| LMS Service          | 5003      | 6003        | Assignments and course content |
| Result Service       | 5004      | 6004        | Grades and GPA calculation     |
| Attendance Service   | 5005      | 6005        | Attendance tracking            |
| Profile Service      | 5006      | 6006        | Student profile management     |
| Frontend             | 5000      | —           | UI layer (Bootstrap + Jinja2)  |
| NGINX                | 80        | —           | Reverse proxy                  |
| MySQL                | 3306      | —           | Relational database            |

---

## 🛠️ Tech Stack

| Layer            | Technology               |
| ---------------- | ------------------------ |
| Backend          | Python, Flask            |
| Authentication   | JWT (Flask-JWT-Extended) |
| Database         | MySQL 8                  |
| Containerization | Docker                   |
| Orchestration    | Kubernetes (Minikube)    |
| Frontend         | Bootstrap 5, Jinja2      |
| Proxy            | NGINX                    |
| Communication    | REST + TCP Sockets       |
| Version Control  | Git & GitHub             |

---

## ⚙️ Prerequisites

* Docker Desktop (24+)
* Git (latest)
* RAM: 8GB+
* OS: Windows / Linux / macOS

Optional:

* Minikube (for Kubernetes deployment)
* kubectl

---

## 🚀 Deployment Options

### 1. Docker Compose (Recommended)

```bash
git clone https://github.com/yourusername/university-management-system.git
cd university-management-system
docker-compose up --build
```

Open:

```
http://localhost
```

---

### 2. Kubernetes (Minikube)

```bash
minikube start --driver=docker --memory=4096 --cpus=2

eval $(minikube docker-env)

docker build -t auth-service ./auth-service
docker build -t registration-service ./registration-service
docker build -t lms-service ./lms-service
docker build -t result-service ./result-service
docker build -t attendance-service ./attendance-service
docker build -t profile-service ./profile-service
docker build -t frontend ./frontend
docker build -t nginx-proxy ./nginx

kubectl apply -f k8s/
minikube service nginx-proxy -n university --url
```

---

### 3. Share via Ngrok

```bash
ngrok http 80
```

---

## 🧪 Kubernetes Commands (Demo)

```bash
kubectl get pods -n university
kubectl get deployments -n university
kubectl logs -l app=auth-service -n university

kubectl scale deployment auth-service --replicas=4 -n university
kubectl top pods -n university
```

---

## 🗄️ Database Schema

* students
* student_profiles
* courses
* enrollments
* assignments
* results
* attendance
* attendance_summary

All tables are normalized up to 3NF.

---

## 📁 Project Structure

```
university-management-system/
├── auth-service/
├── registration-service/
├── lms-service/
├── result-service/
├── attendance-service/
├── profile-service/
├── frontend/
├── nginx/
├── k8s/
├── scripts/
│   └── init.sql
├── docker-compose.yml
└── README.md
```

---

## 👥 Team

| Name                 | Role                 |
| -------------------- | -------------------- |
| Ghulam Mustafa Ahmed | Auth & Documentation |
| Ayaan Ahmed Soomro   | LMS & Results        |
| Muhammad Uzair       | Attendance & Profile |

---

## 👩‍🏫 Supervisor

Madam Areeba Nasim
Department of Electrical and Computer Engineering
Capital University of Science & Technology (CUST), Islamabad

---

## 🎯 SDG Alignment

* SDG 4: Quality Education
* SDG 9: Industry, Innovation & Infrastructure
* SDG 11: Sustainable Cities & Communities

---

## 📄 License

MIT License

---

## ⭐ Acknowledgments

* Faculty of CUST ECE Department
* Course: CPE4541 Cloud and Distributed Computing
* Supervisor guidance and academic support

---

## 📌 Footer

Built with ☁️ cloud-native architecture | June 2026

```

If you want, I can next:
- make a **more visually premium GitHub README (with icons + collapsible sections)**  
- or generate a **matching architecture diagram image (PNG/SVG)**  
- or create a **resume-ready project description**
```
