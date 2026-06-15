#!/bin/bash
# Remove all Kubernetes resources (keeps Minikube running)
kubectl delete namespace university
echo "✅ All university resources deleted"

# To also stop Minikube completely:
# minikube stop
# minikube delete
