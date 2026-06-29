#!/bin/bash

# Stop on error
set -e

echo "🔍 Checking GCP Configuration..."
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Project ID not set."
    echo "Please run 'gcloud config set project <YOUR_PROJECT_ID>' first."
    exit 1
fi

echo "✅ Using Project: $PROJECT_ID"

# Get Backend URL
BACKEND_URL=$1

if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  Backend URL not provided."
    echo "Please enter the Backend URL (e.g., https://just-travel-backend-xyz-uc.a.run.app):"
    read BACKEND_URL
fi

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Error: Backend URL is required."
    exit 1
fi

echo "✅ Using Backend URL: $BACKEND_URL"

echo "📦 Building Frontend Container (Cloud Build)..."
# Navigate to frontend directory for build context context is root but dockerfile is in frontend?
# Wait, typically we build from root with -f frontend/Dockerfile or inside frontend
# Looking at DEPLOY_GCP.md, it says "Navigate to frontend folder first!" then "gcloud builds submit ... ./"
# So I should change directory or use the correct build path.
# Let's check if we are in the root.
# The script is in root.
# So we need to build the frontend.

cd frontend

gcloud builds submit --config cloudbuild.yaml --substitutions=_NEXT_PUBLIC_API_URL=$BACKEND_URL .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy just-travel-frontend \
  --image "gcr.io/$PROJECT_ID/just-travel-frontend" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL

echo "✅ Frontend Deployment Complete!"
