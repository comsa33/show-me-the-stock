#!/bin/bash
# TeamCity build script for show-me-the-stock application

set -e

# Build configuration
DOCKER_REGISTRY="192.168.0.5:5000"
PROJECT_NAME="show-me-the-stock"
BUILD_NUMBER=${BUILD_NUMBER:-"latest"}

# Backend image build
echo "Building backend image..."
cd web-version/backend
docker build -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${BUILD_NUMBER} \
  --target production \
  --build-arg BUILD_NUMBER=${BUILD_NUMBER} .

# Frontend image build
echo "Building frontend image..."
cd ../frontend
docker build -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${BUILD_NUMBER} \
  --target production \
  --build-arg BUILD_NUMBER=${BUILD_NUMBER} .

# Push images to registry
echo "Pushing images to registry..."
docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${BUILD_NUMBER}
docker push ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${BUILD_NUMBER}

# Update Helm values with new image tags
echo "Updating Helm chart values..."
cd ../../deploy/show-me-the-stock
sed -i "s/tag: \"\"/tag: \"${BUILD_NUMBER}\"/g" values.yaml

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
helm upgrade --install ${PROJECT_NAME} . \
  --namespace ${PROJECT_NAME} \
  --create-namespace \
  --set backend.image.tag=${BUILD_NUMBER} \
  --set frontend.image.tag=${BUILD_NUMBER} \
  --set geminiApiKey="${GEMINI_API_KEY}" \
  --set alphaVantageApiKey="${ALPHA_VANTAGE_API_KEY}" \
  --set secretKey="${SECRET_KEY}" \
  --wait --timeout=600s

echo "Deployment completed successfully!"

# Health check
echo "Performing health check..."
kubectl wait --for=condition=ready pod -l app=${PROJECT_NAME} -n ${PROJECT_NAME} --timeout=300s
echo "Application is ready!"