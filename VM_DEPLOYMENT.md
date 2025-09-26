# Deploy Face Recognition API on Google Cloud VM

## Overview

Deploy your Face Recognition API on a Google Cloud Compute Engine VM for full control over the server environment. This approach is ideal when you need persistent storage, specific system configurations, or want to run multiple services on the same machine.

## Prerequisites

- **Google Cloud Account** with billing enabled
- **GitHub repository**: `hishamac/face-gallery-api`
- **MongoDB Atlas account** (recommended) or local MongoDB
- **Basic Linux knowledge** (helpful but not required)

## VM Specifications for Face Recognition API

### Recommended Configuration:
- **Machine Type**: `e2-standard-4` (4 vCPUs, 16 GB RAM)
- **Boot Disk**: Ubuntu 20.04 LTS, 50 GB SSD
- **Region**: Choose closest to your users (e.g., `us-central1-a`)
- **Network**: Allow HTTP/HTTPS traffic

### Why These Specs?
- **16 GB RAM**: Face recognition with dlib requires significant memory
- **4 vCPUs**: Parallel processing for multiple face detections
- **50 GB SSD**: Fast I/O for image processing and storage

## Step 1: Create VM Instance (Browser Method)

### 1.1 Open Google Cloud Console

1. Go to: https://console.cloud.google.com
2. **Create or select project**
3. **Enable Compute Engine API** if prompted

### 1.2 Create VM Instance

1. **Navigate to**: Compute Engine → VM instances
2. **Click**: "CREATE INSTANCE"

### 1.3 Configure Instance

**Basic Configuration:**
- **Name**: `face-api-vm`
- **Region**: `us-central1` (or closest to you)
- **Zone**: `us-central1-a`

**Machine Configuration:**
- **Series**: E2
- **Machine type**: `e2-standard-4` (4 vCPU, 16 GB memory)

**Boot Disk:**
- **Operating system**: Ubuntu
- **Version**: Ubuntu 20.04 LTS
- **Boot disk type**: SSD persistent disk
- **Size**: 50 GB

**Firewall:**
- ✅ **Allow HTTP traffic**
- ✅ **Allow HTTPS traffic**

### 1.4 Advanced Options

Click **"Management, security, disks, networking, sole tenancy"**

**Management Tab - Startup Script:**
```bash
#!/bin/bash

# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.9 and pip
apt-get install -y python3.9 python3.9-pip python3.9-dev python3.9-venv

# Install system dependencies for face_recognition
apt-get install -y build-essential cmake
apt-get install -y libopenblas-dev liblapack-dev 
apt-get install -y libx11-dev libgtk-3-dev
apt-get install -y python3-dev
apt-get install -y git curl nginx supervisor

# Install Node.js (for any frontend needs)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs

# Create application directory
mkdir -p /opt/face-api
cd /opt/face-api

# Clone repository
git clone https://github.com/hishamac/face-gallery-api.git .
cd api

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install gunicorn for production
pip install gunicorn

# Create directories
mkdir -p uploads faces logs

# Set permissions
chown -R www-data:www-data /opt/face-api
chmod -R 755 /opt/face-api

echo "Face API VM setup completed!"
```

### 1.5 Create the VM

1. **Click**: "CREATE"
2. **Wait**: 2-3 minutes for VM to be created
3. **Note**: External IP address (you'll need this)

## Step 2: Configure the Application

### 2.1 SSH into VM

1. **In VM instances list**: Click "SSH" next to your VM
2. **Browser SSH window** will open

### 2.2 Set Environment Variables

Create environment file:
```bash
cd /opt/face-api/api
sudo nano .env
```

Add this content:
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-change-this
FLASK_DEBUG=False

# MongoDB Configuration (use MongoDB Atlas)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/face_gallery?retryWrites=true&w=majority
DATABASE_NAME=face_gallery

# File Configuration
UPLOAD_FOLDER=/opt/face-api/api/uploads
FACES_FOLDER=/opt/face-api/api/faces
MAX_CONTENT_LENGTH=16777216

# Face Recognition Configuration
DBSCAN_EPS=0.4
DBSCAN_MIN_SAMPLES=2
FACE_RECOGNITION_TOLERANCE=0.6
MIN_FACE_SIZE=50

# CORS Configuration
CORS_ORIGINS=*

# Server Configuration
PORT=5000
```

Save with `Ctrl+X`, `Y`, `Enter`

### 2.3 Test the Application

```bash
cd /opt/face-api/api
source venv/bin/activate
python app.py
```

If successful, you should see:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://[your-internal-ip]:5000
```

Press `Ctrl+C` to stop.

## Step 3: Production Setup

### 3.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/face-api.service
```

Add this content:
```ini
[Unit]
Description=Face Recognition API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/face-api/api
Environment=PATH=/opt/face-api/api/venv/bin
EnvironmentFile=/opt/face-api/api/.env
ExecStart=/opt/face-api/api/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 --timeout 300 --max-requests 1000 app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable face-api
sudo systemctl start face-api
sudo systemctl status face-api
```

### 3.2 Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/face-api
```

Add this content:
```nginx
server {
    listen 80;
    server_name YOUR_VM_EXTERNAL_IP;
    
    # Increase client max body size for image uploads
    client_max_body_size 50M;
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for face processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Serve static files directly
    location /uploads/ {
        alias /opt/face-api/api/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    location /faces/ {
        alias /opt/face-api/api/faces/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

Replace `YOUR_VM_EXTERNAL_IP` with your actual VM external IP.

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/face-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 4: Configure Firewall

### 4.1 Google Cloud Firewall Rules

1. **Go to**: VPC network → Firewall
2. **Click**: "CREATE FIREWALL RULE"

**Rule 1 - HTTP/HTTPS:**
- **Name**: `allow-face-api-http`
- **Direction**: Ingress
- **Targets**: Specified target tags
- **Target tags**: `face-api-server`
- **Source IP ranges**: `0.0.0.0/0`
- **Protocols and ports**: TCP, ports 80, 443

### 4.2 Add Network Tag to VM

1. **Go to**: Compute Engine → VM instances
2. **Click**: Your VM name
3. **Click**: "EDIT"
4. **Network tags**: Add `face-api-server`
5. **Click**: "SAVE"

## Step 5: Testing Your Deployment

### 5.1 Test API Endpoints

Open in browser:
```
http://YOUR_VM_EXTERNAL_IP/
```

Expected response:
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

### 5.2 Test Image Upload

Use curl or Postman:
```bash
curl -X POST -F "file=@test-image.jpg" http://YOUR_VM_EXTERNAL_IP/images/upload
```

## Step 6: SSL/HTTPS Setup (Optional)

### 6.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 6.2 Get SSL Certificate

First, point a domain to your VM IP, then:
```bash
sudo certbot --nginx -d yourdomain.com
```

## Step 7: Monitoring and Maintenance

### 7.1 Monitor Service Status

```bash
# Check API service
sudo systemctl status face-api

# Check nginx
sudo systemctl status nginx

# View API logs
sudo journalctl -u face-api -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 7.2 Update Application

```bash
cd /opt/face-api
sudo git pull origin main
sudo systemctl restart face-api
```

## Step 8: VM Management Commands

### 8.1 Start/Stop VM (from Cloud Console)

**Start VM:**
```bash
gcloud compute instances start face-api-vm --zone=us-central1-a
```

**Stop VM:**
```bash
gcloud compute instances stop face-api-vm --zone=us-central1-a
```

### 8.2 Cost Optimization

1. **Stop VM when not in use** to save costs
2. **Use preemptible instances** for development (up to 80% savings)
3. **Resize VM** if you need more/less resources
4. **Set up billing alerts** in Google Cloud Console

## Troubleshooting

### Common Issues:

**1. Service won't start:**
```bash
sudo systemctl status face-api
sudo journalctl -u face-api
```

**2. Nginx errors:**
```bash
sudo nginx -t
sudo systemctl status nginx
```

**3. Face recognition errors:**
- Check if you have enough RAM (16GB recommended)
- Monitor with `htop` or `free -h`

**4. Database connection:**
```bash
# Test MongoDB connection
cd /opt/face-api/api
source venv/bin/activate
python -c "from pymongo import MongoClient; print(MongoClient('your-connection-string').admin.command('ismaster'))"
```

## VM Costs Estimate

**Monthly costs** (us-central1):
- **e2-standard-4**: ~$120/month (if running 24/7)
- **50GB SSD**: ~$8/month
- **Network egress**: Variable based on usage

**Cost Optimization:**
- **Stop VM** when not needed: Pay only for storage (~$8/month)
- **Use preemptible**: Up to 80% discount (but can be terminated)
- **Schedule start/stop**: Use Cloud Scheduler for automatic management

## Benefits of VM Deployment

✅ **Full control** over the server environment
✅ **Persistent storage** on the VM
✅ **Custom configurations** possible
✅ **Multiple services** can run on same VM
✅ **Traditional server** management approach
✅ **Cost predictable** with fixed monthly pricing

## Comparison: VM vs Cloud Run

| Feature | VM | Cloud Run |
|---------|----|-----------| 
| **Cost** | Fixed monthly | Pay per request |
| **Scaling** | Manual | Automatic |
| **Management** | Full control | Fully managed |
| **Startup time** | Always running | Cold starts |
| **Persistent storage** | Yes | Temporary only |
| **Best for** | Always-on services | Variable traffic |

Your Face Recognition API is now running on a Google Cloud VM with production-grade setup including Nginx, systemd service, and proper security configuration! 🚀