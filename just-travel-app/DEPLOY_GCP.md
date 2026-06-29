# Just Travel - Google Cloud Platform Deployment Guide

This guide explains how to deploy the "Just Travel" application to **Google Cloud Platform (GCP)** using **Cloud Run**.

Cloud Run is ideal for this project because:
1.  **Serverless:** Scales to zero when not in use (low cost).
2.  **Container-based:** Uses the same Docker setup we already have.
3.  **HTTPS:** Automatically provides SSL certificates.

---

## 📋 Prerequisites

1.  **Google Cloud Project:** Create one at [console.cloud.google.com](https://console.cloud.google.com).
2.  **Billing Enabled:** Required for building/deploying (even if using free tier).
3.  **gcloud CLI:** Installed and logged in (`gcloud init`).

---

## 🚀 Deployment Steps

### 1. Enable Required Services

Run these commands in your terminal to enable the necessary APIs:

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Configure Environment Variables (Secrets)

For security, we will use **Secret Manager** for all your API keys.

**Run these commands one by one.** You will be prompted to enter the value from your `.env` file for each one.

**Critical Secrets (Required):**
```bash
# Google Gemini API Key
gcloud secrets create google_api_key --data-file=-
# (Paste value of GOOGLE_API_KEY and press Ctrl+D)

# Google Maps API Key
gcloud secrets create google_maps_api_key --data-file=-
# (Paste value of GOOGLE_MAPS_API_KEY and press Ctrl+D)

# NextAuth Secret
gcloud secrets create nextauth_secret --data-file=-
# (Paste value of NEXTAUTH_SECRET and press Ctrl+D)
```

**Agent Capabilities (Recommended):**
```bash
# Amadeus (Flights)
gcloud secrets create amadeus_client_id --data-file=-
gcloud secrets create amadeus_client_secret --data-file=-

# Neo4j (Graph DB)
gcloud secrets create neo4j_uri --data-file=-
gcloud secrets create neo4j_username --data-file=-
gcloud secrets create neo4j_password --data-file=-

# Apify (Social Trends)
gcloud secrets create apify_api_token --data-file=-

# OpenWeatherMap (Weather)
gcloud secrets create openweathermap_api_key --data-file=-

# RapidAPI (Hotels)
gcloud secrets create rapidapi_key --data-file=-

# Google OAuth (Optional - for "Sign in with Google")
gcloud secrets create google_client_id --data-file=-
gcloud secrets create google_client_secret --data-file=-
```

### 3. Deploy Backend (Cloud Run)

**A. Build and Push Container**
```bash
export PROJECT_ID=$(gcloud config get-value project)
gcloud builds submit --tag gcr.io/$PROJECT_ID/just-travel-backend ./
```

**B. Deploy Service**
Only mapping the secrets you actually created. If you skipped some optional ones, remove them from this command.

```bash
gcloud run deploy just-travel-backend \
  --image gcr.io/$PROJECT_ID/just-travel-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=production \
  --set-secrets GOOGLE_API_KEY=google_api_key:latest,GOOGLE_MAPS_API_KEY=google_maps_api_key:latest,NEXTAUTH_SECRET=nextauth_secret:latest,AMADEUS_CLIENT_ID=amadeus_client_id:latest,AMADEUS_CLIENT_SECRET=amadeus_client_secret:latest,NEO4J_URI=neo4j_uri:latest,NEO4J_USERNAME=neo4j_username:latest,NEO4J_PASSWORD=neo4j_password:latest,APIFY_API_TOKEN=apify_api_token:latest,OPENWEATHERMAP_API_KEY=openweathermap_api_key:latest,RAPIDAPI_KEY=rapidapi_key:latest,GOOGLE_CLIENT_ID=google_client_id:latest,GOOGLE_CLIENT_SECRET=google_client_secret:latest
```

**Copy the Backend URL** provided at the end (e.g., `https://just-travel-backend-xyz-uc.a.run.app`).

### 4. Deploy Frontend (Cloud Run)

**A. Update `next.config.js` (Optional)**
Ensure your `next.config.js` uses `output: 'standalone'` for Docker builds (it likely already does).

**B. Build and Push Container**
```bash
# Navigate to frontend folder first!
cd frontend

gcloud builds submit --tag gcr.io/$PROJECT_ID/just-travel-frontend ./
```

**C. Deploy Service**
Replace `[BACKEND_URL]` with the URL you got in Step 3.

```bash
gcloud run deploy just-travel-frontend \
  --image gcr.io/$PROJECT_ID/just-travel-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=[BACKEND_URL]
```

**Success!** You will get a final URL (e.g., `https://just-travel-frontend-xyz-uc.a.run.app`). This is your live application.

---

## 🔄 Redis Strategy (Optional)

The app works without Redis, but background tasks won't run. For a hackathon submission, you have two options:

**Option A: Skip Redis (Recommended for Simplicity)**
The app creates itineraries synchronously if Redis is missing. The user just waits a bit longer (15-30s). *This is the easiest path.*

**Option B: Use Google Cloud Memorystore ($$)**
It costs money (~$30/mo minimum).
1. Create a Redis instance: `gcloud redis instances create just-travel-redis --region us-central1`
2. Get the IP address: `gcloud redis instances describe just-travel-redis --region us-central1`
3. Update Backend Deployment: Add `--set-env-vars REDIS_URL=redis://[REDIS_IP]:6379`

**Option C: Use Redis Cloud (Free)**
1. Sign up for a free dataset at [Redis.com](https://redis.com).
2. Get the public endpoint (`redis-123.c1.us-central1.gce.cloud.redislabs.com:12345`).
3. Update Backend Deployment: Add `--set-env-vars REDIS_URL=redis://[USER]:[PASS]@[ENDPOINT]`

---

## ⚠️ Troubleshooting

*   **Public Access:** Ensure you chose "Allow unauthenticated invocations" (y) when prompted, or passed the flag `--allow-unauthenticated`.
*   **CORS:** If the frontend can't talk to the backend, update the `CORS_ORIGINS` variable on the **Backend**:
    ```bash
    gcloud run services update just-travel-backend \
      --update-env-vars CORS_ORIGINS="https://your-frontend-url.run.app"
    ```
