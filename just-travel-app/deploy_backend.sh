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

echo "📦 Building Backend Container (Cloud Build)..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/just-travel-backend" ./

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy just-travel-backend \
  --image "gcr.io/$PROJECT_ID/just-travel-backend" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=production \
  --set-secrets GOOGLE_API_KEY=google_api_key:latest \
  --set-secrets GOOGLE_MAPS_API_KEY=google_maps_api_key:latest \
  --set-secrets NEXTAUTH_SECRET=nextauth_secret:latest \
  --set-secrets AMADEUS_CLIENT_ID=amadeus_client_id:latest \
  --set-secrets AMADEUS_CLIENT_SECRET=amadeus_client_secret:latest \
  --set-secrets NEO4J_URI=neo4j_uri:latest \
  --set-secrets NEO4J_USERNAME=neo4j_username:latest \
  --set-secrets NEO4J_PASSWORD=neo4j_password:latest \
  --set-secrets APIFY_API_TOKEN=apify_api_token:latest \
  --set-secrets OPENWEATHERMAP_API_KEY=openweathermap_api_key:latest \
  --set-secrets RAPIDAPI_KEY=rapidapi_key:latest \
  --set-secrets GOOGLE_CLIENT_ID=google_client_id:latest \
  --set-secrets GOOGLE_CLIENT_SECRET=google_client_secret:latest

echo "✅ Backend Deployment Complete!"
