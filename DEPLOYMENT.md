# Deployment Guide 部署指南

## Google Cloud Run Deployment

### Prerequisites 前置要求

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Create a GCP project and enable billing
3. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com
   ```

### Quick Deploy 快速部署

```bash
# 1. Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Set your API key as a secret
gcloud secrets create google-api-key --data-file=- <<< "YOUR_GOOGLE_API_KEY"

# 3. Deploy to Cloud Run
gcloud run deploy douban-rag \
  --source . \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=YOUR_API_KEY"
```

### Automated Deployment with Cloud Build

For CI/CD, use the `cloudbuild.yaml`:

```bash
# Trigger a build
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_GOOGLE_API_KEY="YOUR_API_KEY"
```

### Cost Optimization 成本优化

- **min-instances=0**: Scale to zero when not in use (free when idle)
- **max-instances=1**: Limit scaling for personal use
- **memory=4Gi**: Required for BGE-M3 embeddings model

### Expected Monthly Cost 预估月费用

| Usage | Cost |
|-------|------|
| Idle (no requests) | $0 |
| Light use (~50 req/day) | $1-5 |
| Medium use (~200 req/day) | $10-15 |

### Notes 注意事项

1. **Cold Start**: First request after idle may take 30-60 seconds as the model loads
2. **Data Persistence**: ChromaDB data is stored in the container and will be lost on restart. For persistent storage, configure Cloud Storage bucket mounting.
3. **Timeout**: Set to 300s to allow for model loading

### Local Testing with Docker

```bash
# Build image
docker build -t douban-rag .

# Run locally
docker run -p 8080:8080 -e GOOGLE_API_KEY="your_key" douban-rag
```

Open http://localhost:8080 to access the app.
