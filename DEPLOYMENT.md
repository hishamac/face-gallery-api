# Deploying Face Recognition API to Google Cloud

## Prerequisites

1. **Google Cloud Account**: Sign up at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)
3. **MongoDB Atlas**: Set up at [mongodb.com/atlas](https://mongodb.com/atlas) (recommended for cloud deployment)

## Setup Steps

### 1. Initialize Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing one)
gcloud projects create your-face-api-project
gcloud config set project your-face-api-project

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Set up MongoDB Atlas

1. Go to [MongoDB Atlas](https://mongodb.com/atlas)
2. Create a free cluster
3. Create a database user
4. Whitelist Google Cloud IPs (or use 0.0.0.0/0 for simplicity)
5. Get your connection string

### 3. Environment Configuration

Create a `.env` file with your production settings:

```bash
# Copy the template
cp .env.production .env

# Edit with your values
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
SECRET_KEY=your-super-secure-random-secret-key
CORS_ORIGINS=https://your-frontend-domain.com
```

## Deployment Options

### Option A: Google Cloud Run (Recommended)

**Advantages:**
- Serverless and scales to zero
- Pay only for what you use
- Automatic HTTPS
- Easy to deploy and update

**Steps:**

```bash
# Build and deploy in one command
gcloud run deploy face-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars FLASK_ENV=production \
  --set-env-vars MONGODB_URI="your-mongodb-connection-string" \
  --set-env-vars SECRET_KEY="your-secret-key"
```

**Manual Docker Build (Alternative):**

```bash
# Build the Docker image
gcloud builds submit --tag gcr.io/your-project-id/face-api

# Deploy to Cloud Run
gcloud run deploy face-api \
  --image gcr.io/your-project-id/face-api \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1
```

### Option B: Google App Engine

**Advantages:**
- Fully managed
- Built-in monitoring and logging
- Automatic scaling

**Steps:**

```bash
# Deploy to App Engine
gcloud app deploy app.yaml

# View your application
gcloud app browse
```

## Optional: Google Cloud Storage Setup

For persistent file storage across instances:

```bash
# Create a storage bucket
gsutil mb gs://your-face-api-bucket

# Make bucket publicly readable (optional)
gsutil iam ch allUsers:objectViewer gs://your-face-api-bucket

# Add to your environment variables
GCS_BUCKET_NAME=your-face-api-bucket
```

Then update your `requirements.txt` to include:
```
google-cloud-storage==2.10.0
```

## Configuration for Production

### Environment Variables to Set

For Cloud Run:
```bash
gcloud run services update face-api \
  --update-env-vars FLASK_ENV=production \
  --update-env-vars MONGODB_URI="your-connection-string" \
  --update-env-vars SECRET_KEY="your-secret-key" \
  --update-env-vars CORS_ORIGINS="https://your-frontend.com"
```

For App Engine, add to `app.yaml`:
```yaml
env_variables:
  FLASK_ENV: production
  MONGODB_URI: "your-connection-string"
  SECRET_KEY: "your-secret-key"
  CORS_ORIGINS: "https://your-frontend.com"
```

## Testing Your Deployment

```bash
# Get your service URL
gcloud run services list

# Test the API
curl https://your-service-url.run.app/
```

## Monitoring and Logs

```bash
# View logs (Cloud Run)
gcloud run logs read --service face-api

# View logs (App Engine)
gcloud app logs tail -s default
```

## Scaling and Performance

### Cloud Run Configuration:
- **Memory**: 2-4 GB recommended for face recognition
- **CPU**: 1-2 vCPUs
- **Timeout**: 300-900 seconds for processing
- **Concurrency**: 1-10 concurrent requests per instance

### App Engine Configuration:
- Use `automatic_scaling` with appropriate instance limits
- Set reasonable CPU utilization targets

## Cost Optimization

1. **Use Cloud Run** for variable workloads
2. **Set max instances** to control costs
3. **Use MongoDB Atlas free tier** for development
4. **Enable billing alerts** in Google Cloud Console
5. **Consider Cloud Storage** for file persistence

## Troubleshooting

### Common Issues:

1. **Memory errors during face recognition:**
   ```bash
   gcloud run services update face-api --memory 4Gi
   ```

2. **Timeout errors:**
   ```bash
   gcloud run services update face-api --timeout 900
   ```

3. **MongoDB connection issues:**
   - Check connection string format
   - Verify network access settings in Atlas
   - Check environment variable names

4. **File upload issues:**
   - Files in `/tmp` are ephemeral
   - Consider using Google Cloud Storage
   - Check MAX_CONTENT_LENGTH settings

### Debug Commands:

```bash
# Check service status
gcloud run services describe face-api

# View recent deployments
gcloud run revisions list --service face-api

# Check environment variables
gcloud run services describe face-api --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

## Security Best Practices

1. **Use Secret Manager** for sensitive data:
   ```bash
   # Store secrets
   echo -n "your-secret-key" | gcloud secrets create secret-key --data-file=-
   
   # Update Cloud Run to use secrets
   gcloud run services update face-api \
     --update-secrets SECRET_KEY=secret-key:latest
   ```

2. **Enable authentication** if needed:
   ```bash
   gcloud run services update face-api --no-allow-unauthenticated
   ```

3. **Use HTTPS only** (enabled by default)

4. **Restrict CORS origins** in production

## Updating Your Application

```bash
# For Cloud Run (rebuild and redeploy)
gcloud run deploy face-api --source .

# For App Engine
gcloud app deploy
```

Your Face Recognition API will be available at:
- **Cloud Run**: `https://face-api-[hash].run.app`
- **App Engine**: `https://your-project-id.appspot.com`