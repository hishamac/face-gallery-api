# Deploy Face Recognition API from GitHub to Google Cloud Run

## Overview
This guide shows how to deploy your API directly from your GitHub repository (`hishamac/face-gallery-api`) to Google Cloud Run with automatic continuous deployment.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **GitHub repository** (you already have: `hishamac/face-gallery-api`)
3. **Google Cloud SDK** installed locally (optional for setup)

## Step-by-Step Deployment

### 1. Set up Google Cloud Project

```bash
# Login to Google Cloud (if using CLI)
gcloud auth login

# Create or select project
gcloud projects create your-face-api-project
gcloud config set project your-face-api-project

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Set up MongoDB Atlas (Required)

1. Go to [MongoDB Atlas](https://mongodb.com/atlas)
2. Create a free cluster
3. Create a database user with read/write permissions
4. Add network access (0.0.0.0/0 for Google Cloud)
5. Copy your connection string

### 3. Store Secrets in Google Cloud Secret Manager

```bash
# Store your MongoDB URI
echo -n "mongodb+srv://username:password@cluster.mongodb.net/face_gallery?retryWrites=true&w=majority" | \
  gcloud secrets create mongodb-uri --data-file=-

# Store your secret key
echo -n "your-super-secure-secret-key-here" | \
  gcloud secrets create flask-secret-key --data-file=-

# Store CORS origins
echo -n "https://your-frontend-domain.com" | \
  gcloud secrets create cors-origins --data-file=-
```

### 4. Deploy from Google Cloud Console

#### Option A: Using Google Cloud Console (Recommended)

1. **Go to Google Cloud Run**: https://console.cloud.google.com/run
2. **Click "CREATE SERVICE"**
3. **Select "Continuously deploy from a repository"** (the GitHub option you saw)
4. **Set up source repository**:
   - **Repository Provider**: GitHub
   - **Repository**: `hishamac/face-gallery-api`
   - **Branch**: `^main$`
   - **Build Type**: Dockerfile
   - **Source Location**: `/api/Dockerfile`

5. **Configure the service**:
   - **Service name**: `face-api`
   - **Region**: `us-central1` (or your preferred region)
   - **CPU allocation**: CPU is only allocated during request processing
   - **Ingress**: Allow all traffic
   - **Authentication**: Allow unauthenticated invocations

6. **Configure container settings**:
   - **Memory**: `2 GiB`
   - **CPU**: `1`
   - **Maximum requests per container**: `10`
   - **Timeout**: `300` seconds
   - **Maximum instances**: `10`

7. **Add environment variables**:
   - `FLASK_ENV`: `production`
   - `PORT`: `8080`
   - `UPLOAD_FOLDER`: `/tmp/uploads`
   - `FACES_FOLDER`: `/tmp/faces`

8. **Add secrets** (click "Add a secret"):
   - **Secret**: `mongodb-uri` → **Environment variable**: `MONGODB_URI`
   - **Secret**: `flask-secret-key` → **Environment variable**: `SECRET_KEY`
   - **Secret**: `cors-origins` → **Environment variable**: `CORS_ORIGINS`

9. **Click "CREATE"**

#### Option B: Using Cloud Build Trigger (Advanced)

Create a `cloudbuild.yaml` in your repository root:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/face-api', './api']
    
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/face-api']
    
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
    - 'run'
    - 'deploy'
    - 'face-api'
    - '--image'
    - 'gcr.io/$PROJECT_ID/face-api'
    - '--region'
    - 'us-central1'
    - '--allow-unauthenticated'
    - '--memory'
    - '2Gi'
    - '--cpu'
    - '1'
    - '--timeout'
    - '300'
    - '--max-instances'
    - '10'
    - '--update-secrets'
    - 'MONGODB_URI=mongodb-uri:latest'
    - '--update-secrets'
    - 'SECRET_KEY=flask-secret-key:latest'
    - '--update-secrets'
    - 'CORS_ORIGINS=cors-origins:latest'
    - '--update-env-vars'
    - 'FLASK_ENV=production,PORT=8080,UPLOAD_FOLDER=/tmp/uploads,FACES_FOLDER=/tmp/faces'

images:
  - gcr.io/$PROJECT_ID/face-api
```

### 5. Connect GitHub Repository

When you select "Continuously deploy from a repository":

1. **Authorize Google Cloud Build** to access your GitHub account
2. **Select repository**: `hishamac/face-gallery-api`
3. **Choose branch**: `main`
4. **Build configuration**: Dockerfile
5. **Dockerfile location**: `/api/Dockerfile` (since your API is in the api folder)

### 6. Configure Build Settings

In the build configuration:
- **Build context**: Root directory
- **Dockerfile path**: `api/Dockerfile`
- **Build environment**: Cloud Build

### 7. Automatic Deployments

Once set up:
- **Every push to main branch** will trigger a new deployment
- **Build logs** are available in Google Cloud Build
- **Rollback** is available through Cloud Run console
- **Traffic splitting** for blue-green deployments

## Environment Variables Configuration

Your service will need these environment variables:

```bash
# Required
MONGODB_URI=mongodb+srv://...          # From Secret Manager
SECRET_KEY=your-secret-key             # From Secret Manager
FLASK_ENV=production
PORT=8080

# File handling
UPLOAD_FOLDER=/tmp/uploads
FACES_FOLDER=/tmp/faces
MAX_CONTENT_LENGTH=16777216

# Face recognition settings
DBSCAN_EPS=0.4
DBSCAN_MIN_SAMPLES=2
FACE_RECOGNITION_TOLERANCE=0.6

# CORS (from Secret Manager or environment)
CORS_ORIGINS=https://your-frontend.com
```

## Monitoring Your Deployment

### View Deployment Status:
1. **Cloud Run Console**: https://console.cloud.google.com/run
2. **Cloud Build History**: https://console.cloud.google.com/cloud-build/builds
3. **GitHub Actions**: In your repository's Actions tab

### Check Logs:
```bash
# View service logs
gcloud run logs read --service=face-api --region=us-central1

# View build logs
gcloud builds log [BUILD_ID]
```

## Testing Your Deployed API

Once deployed, you'll get a URL like:
`https://face-api-[hash]-uc.a.run.app`

Test it:
```bash
# Test the API
curl https://your-service-url/

# Expected response:
{
  "message": "Face Clustering API",
  "version": "2.0",
  "endpoints": {
    "images": "/images",
    "albums": "/albums",
    ...
  }
}
```

## Updating Your API

Simply push changes to your GitHub repository:

```bash
git add .
git commit -m "Update API"
git push origin main
```

Cloud Run will automatically:
1. Detect the push
2. Build a new container image
3. Deploy the new version
4. Route traffic to the new version

## Benefits of GitHub Integration

✅ **Automatic deployments** on every push
✅ **Version control** integration
✅ **Rollback capabilities** 
✅ **Build history** and logs
✅ **No manual Docker builds** required
✅ **Collaborative development** workflow
✅ **Branch-based deployments** (can deploy from different branches)

## Troubleshooting

### Common Issues:

1. **Build fails**: Check `cloudbuild.yaml` or Dockerfile path
2. **Service won't start**: Check environment variables and secrets
3. **Database connection fails**: Verify MongoDB Atlas connection string
4. **Memory issues**: Increase memory allocation to 4 GiB

### Debug Commands:

```bash
# Check service status
gcloud run services describe face-api --region=us-central1

# View recent revisions
gcloud run revisions list --service=face-api --region=us-central1

# Check build history
gcloud builds list --limit=10
```

## Cost Optimization

- **Set max instances** to control scaling
- **Use minimum instances = 0** to scale to zero
- **Monitor usage** in Google Cloud Console
- **Set up billing alerts**

Your Face Recognition API will be live at a Google Cloud Run URL with automatic deployments from your GitHub repository!