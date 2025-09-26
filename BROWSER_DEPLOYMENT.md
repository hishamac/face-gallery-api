# Deploy Face Recognition API to Google Cloud Run (No SDK Required)

## Complete Browser-Based Deployment Guide

Deploy your `hishamac/face-gallery-api` repository directly from GitHub to Google Cloud Run using only your web browser - **no Google Cloud SDK installation required**.

## Prerequisites

- ✅ **Google Account** (Gmail account works)
- ✅ **GitHub repository** (you have: `hishamac/face-gallery-api`)
- ✅ **MongoDB Atlas account** (free tier available)
- ✅ **Web browser** (Chrome, Firefox, Safari, Edge)

## Step 1: Set Up Google Cloud Project

### 1.1 Create Google Cloud Account & Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Sign in** with your Google account
3. **Accept terms** and **enable billing** (required, but you get $300 free credits)
4. **Create a new project**:
   - Click the project dropdown (top left)
   - Click "NEW PROJECT"
   - **Project name**: `face-api-project` (or any name you prefer)
   - Click "CREATE"
5. **Select your new project** from the dropdown

### 1.2 Enable Required APIs

1. **Go to APIs & Services**: https://console.cloud.google.com/apis/library
2. **Search and enable these APIs** (click each, then click "ENABLE"):
   - **Cloud Build API**
   - **Cloud Run API** 
   - **Secret Manager API**
   - **Container Registry API**

## Step 2: Set Up MongoDB Atlas (Database)

### 2.1 Create MongoDB Atlas Account

1. **Go to MongoDB Atlas**: https://www.mongodb.com/atlas
2. **Sign up** for free account
3. **Create a cluster**:
   - Choose **M0 (Free)**
   - Select **Google Cloud Platform**
   - Choose region closest to you (e.g., us-central1)
   - Cluster name: `face-gallery-cluster`
   - Click "Create Cluster"

### 2.2 Configure Database Access

1. **Database Access** (left sidebar):
   - Click "Add New Database User"
   - **Username**: `face-api-user`
   - **Password**: Generate secure password (save it!)
   - **Database User Privileges**: Read and write to any database
   - Click "Add User"

2. **Network Access** (left sidebar):
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Click "Confirm"

### 2.3 Get Connection String

1. **Clusters** → Click "Connect" on your cluster
2. **Choose "Connect your application"**
3. **Driver**: Python, **Version**: 3.6 or later
4. **Copy the connection string** (save it!):
   ```
   mongodb+srv://face-api-user:<password>@face-gallery-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Replace `<password>`** with your actual password

## Step 3: Store Secrets in Google Cloud

### 3.1 Open Secret Manager

1. **Go to Secret Manager**: https://console.cloud.google.com/security/secret-manager
2. **Enable the Secret Manager API** if prompted

### 3.2 Create Secrets

**Create MongoDB URI Secret**:
1. Click "CREATE SECRET"
2. **Name**: `mongodb-uri`
3. **Secret value**: Your MongoDB connection string from Step 2.3
4. Click "CREATE SECRET"

**Create Flask Secret Key**:
1. Click "CREATE SECRET"
2. **Name**: `flask-secret-key`
3. **Secret value**: Generate a random string (e.g., `my-super-secret-key-12345-random`)
4. Click "CREATE SECRET"

**Create CORS Origins** (optional):
1. Click "CREATE SECRET"
2. **Name**: `cors-origins`
3. **Secret value**: `*` (for now, change to your frontend domain later)
4. Click "CREATE SECRET"

## Step 4: Deploy from GitHub to Cloud Run

### 4.1 Open Cloud Run

1. **Go to Cloud Run**: https://console.cloud.google.com/run
2. Click "CREATE SERVICE"

### 4.2 Choose Source

1. **Select "Continuously deploy new revisions from a source repository"** (the GitHub option)
2. Click "SET UP WITH CLOUD BUILD"

### 4.3 Connect Repository

1. **Repository provider**: GitHub
2. Click "MANAGE CONNECTED REPOSITORIES"
3. **Authenticate with GitHub** (sign in to your GitHub account)
4. **Select repository**: `hishamac/face-gallery-api`
5. **Authorize Google Cloud Build**
6. Click "DONE"

### 4.4 Configure Build

1. **Repository**: Select `hishamac/face-gallery-api`
2. **Branch**: `^main$`
3. **Build Type**: Dockerfile
4. **Source Location**: `/Dockerfile` (your API files are in the repository root)
5. Click "SAVE"

### 4.5 Configure Service

**Service Settings**:
- **Service name**: `face-api`
- **Region**: `us-central1` (or your preferred region)
- **CPU allocation and pricing**: CPU is only allocated during request processing
- **Ingress**: Allow all traffic
- **Authentication**: Allow unauthenticated invocations ✅

**Container Settings** (click "CONTAINER, NETWORKING, SECURITY"):
- **Memory**: `2 GiB`
- **CPU**: `1`
- **Request timeout**: `300` seconds
- **Maximum requests per container**: `10`

### 4.6 Add Environment Variables

In **Container** tab, **Environment variables** section:

Click "ADD VARIABLE" for each:
- **Name**: `FLASK_ENV`, **Value**: `production`
- **Name**: `PORT`, **Value**: `8080`
- **Name**: `UPLOAD_FOLDER`, **Value**: `/tmp/uploads`
- **Name**: `FACES_FOLDER`, **Value**: `/tmp/faces`
- **Name**: `DATABASE_NAME`, **Value**: `face_gallery`

### 4.7 Add Secrets

In **Container** tab, **Environment variables** section:

Click "REFERENCE A SECRET" for each:
1. **Secret**: `mongodb-uri` → **Reference method**: Latest version → **Expose as**: Environment variable → **Name**: `MONGODB_URI`
2. **Secret**: `flask-secret-key` → **Reference method**: Latest version → **Expose as**: Environment variable → **Name**: `SECRET_KEY`
3. **Secret**: `cors-origins` → **Reference method**: Latest version → **Expose as**: Environment variable → **Name**: `CORS_ORIGINS`

### 4.8 Deploy

1. Click "CREATE" at the bottom
2. **Wait for deployment** (5-10 minutes)
3. **Monitor progress** in the Cloud Build console

## Step 5: Test Your Deployed API

### 5.1 Get Your API URL

1. Once deployed, you'll see your service URL like:
   ```
   https://face-api-xxxxxxxxx-uc.a.run.app
   ```

### 5.2 Test the API

Open these URLs in your browser:

**Basic test**:
```
https://your-service-url/
```

**Expected response**:
```json
{
  "message": "Face Clustering API",
  "version": "2.0",
  "endpoints": {
    "images": "/images",
    "albums": "/albums",
    "sections": "/sections",
    "persons": "/persons",
    "faces": "/faces",
    "cluster": "/cluster",
    "stats": "/stats"
  }
}
```

## Step 6: Monitor and Manage

### 6.1 View Logs

1. **Go to Cloud Run**: https://console.cloud.google.com/run
2. **Click your service** (`face-api`)
3. **Click "LOGS" tab** to see real-time logs

### 6.2 Monitor Builds

1. **Go to Cloud Build**: https://console.cloud.google.com/cloud-build/builds
2. **View build history** and logs for each deployment

## Step 7: Automatic Updates

### 7.1 How It Works

Now whenever you:
1. **Make changes** to your code
2. **Push to GitHub** (`git push origin main`)
3. **Google Cloud automatically**:
   - Detects the changes
   - Builds new Docker image
   - Deploys to Cloud Run
   - Makes it live!

### 7.2 Update Your Frontend

Update your frontend to use the new API URL:
```javascript
const API_URL = 'https://face-api-xxxxxxxxx-uc.a.run.app';
```

## Troubleshooting

### Build Fails
1. **Check build logs** in Cloud Build console
2. **Verify Dockerfile path** is `/api/Dockerfile`
3. **Check repository permissions**

### Service Won't Start
1. **Check service logs** in Cloud Run console
2. **Verify environment variables** are set correctly
3. **Check MongoDB connection string**

### Database Connection Issues
1. **Verify MongoDB Atlas** is configured correctly
2. **Check network access** allows all IPs (0.0.0.0/0)
3. **Test connection string** format

## Cost Management

### Free Tier Limits
- **Cloud Run**: 2 million requests/month free
- **Cloud Build**: 120 build-minutes/day free
- **MongoDB Atlas**: 512MB storage free

### Monitor Costs
1. **Go to Billing**: https://console.cloud.google.com/billing
2. **Set up budget alerts**
3. **Monitor usage** regularly

## Security Best Practices

1. **Restrict CORS origins** to your actual frontend domain
2. **Use strong secret keys**
3. **Monitor access logs**
4. **Update dependencies** regularly via GitHub pushes

## Success! 🎉

Your Face Recognition API is now:
- ✅ **Deployed** on Google Cloud Run
- ✅ **Automatically updated** from GitHub
- ✅ **Scalable** and secure
- ✅ **Cost-effective** with pay-per-use pricing

**API URL**: `https://face-api-xxxxxxxxx-uc.a.run.app`

**Next Steps**:
1. Update your frontend to use the new API URL
2. Test all endpoints with your client application
3. Monitor performance and logs
4. Push code changes to GitHub for automatic deployments

No Google Cloud SDK installation was needed - everything was done through the web browser! 🚀