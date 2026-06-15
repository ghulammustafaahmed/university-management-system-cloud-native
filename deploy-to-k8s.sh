#!/bin/bash
# ============================================================
# University System V2 — Kubernetes Deployment Script
# Run this from: C:\Users\sunny\university-system-v2\university-system-v2\
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   University System V2 — Kubernetes Deployment       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Step 1: Start Minikube
echo "[1/6] Starting Minikube..."
minikube start --driver=docker --memory=4096 --cpus=2
echo "✅ Minikube started"

# Step 2: Point Docker to Minikube's internal registry
echo ""
echo "[2/6] Connecting Docker to Minikube registry..."
eval $(minikube docker-env)
echo "✅ Docker now points to Minikube"

# Step 3: Build all images inside Minikube
echo ""
echo "[3/6] Building Docker images inside Minikube..."
docker build -t auth-service:latest         ./auth-service
docker build -t registration-service:latest  ./registration-service
docker build -t lms-service:latest           ./lms-service
docker build -t result-service:latest        ./result-service
docker build -t attendance-service:latest    ./attendance-service
docker build -t profile-service:latest       ./profile-service
docker build -t frontend:latest              ./frontend
docker build -t nginx-proxy:latest           ./nginx
echo "✅ All images built"

# Step 4: Apply Kubernetes manifests
echo ""
echo "[4/6] Deploying to Kubernetes..."
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-mysql.yaml

echo "  Waiting 40 seconds for MySQL to initialize..."
sleep 40

kubectl apply -f k8s/04-auth-service.yaml
kubectl apply -f k8s/05-registration-service.yaml
kubectl apply -f k8s/06-lms-service.yaml
kubectl apply -f k8s/07-result-service.yaml
kubectl apply -f k8s/08-attendance-service.yaml
kubectl apply -f k8s/09-profile-service.yaml
kubectl apply -f k8s/10-frontend.yaml
kubectl apply -f k8s/11-nginx.yaml
echo "✅ All manifests applied"

# Step 5: Wait for pods to be ready
echo ""
echo "[5/6] Waiting for all pods to become Ready..."
kubectl wait --for=condition=ready pod -l app=mysql        -n university --timeout=120s
kubectl wait --for=condition=ready pod -l app=auth-service -n university --timeout=90s
kubectl wait --for=condition=ready pod -l app=frontend     -n university --timeout=90s
echo "✅ Core pods are ready"

# Step 6: Show status and URL
echo ""
echo "[6/6] Deployment complete!"
echo ""
kubectl get pods -n university
echo ""
echo "🌐 Your app URL:"
minikube service nginx-proxy -n university --url
echo ""
echo "💡 Commands to use:"
echo "   kubectl get pods -n university"
echo "   kubectl top pods -n university"
echo "   kubectl logs -l app=auth-service -n university"
echo "   kubectl scale deployment auth-service --replicas=4 -n university"
