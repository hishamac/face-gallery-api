# Quick VM Deployment Guide - Face Recognition API

## 🚀 Super Quick Setup (5 minutes)

### Step 1: Create VM with Auto-Setup

1. **Go to**: https://console.cloud.google.com/compute/instances
2. **Click**: "CREATE INSTANCE"
3. **Configure**:
   - **Name**: `face-api-vm`
   - **Region**: `us-central1-a`
   - **Machine type**: `e2-standard-4` (4 vCPU, 16 GB RAM)
   - **Boot disk**: Ubuntu 20.04 LTS, 50 GB SSD
   - **Firewall**: ✅ Allow HTTP traffic, ✅ Allow HTTPS traffic

4. **Advanced Options** → **Management** → **Startup script**:

Copy and paste this entire script:

```bash
#!/bin/bash
cd /tmp
curl -O https://raw.githubusercontent.com/hishamac/face-gallery-api/main/api/vm-setup.sh
chmod +x vm-setup.sh
./vm-setup.sh 2>&1 | tee setup.log
```

5. **Click**: "CREATE"

### Step 2: Complete Setup (after VM starts)

**SSH into your VM** (click SSH button in console):

```bash
# 1. Create environment file
sudo cp /opt/face-api/api/.env.template /opt/face-api/api/.env
sudo nano /opt/face-api/api/.env
```

**Update these values in the .env file**:
```bash
SECRET_KEY=your-super-secure-random-secret-key-here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/face_gallery?retryWrites=true&w=majority
CORS_ORIGINS=https://your-frontend-domain.com
```

```bash
# 2. Start the API service
sudo systemctl start face-api

# 3. Check everything is working
face-status
```

### Step 3: Test Your API

**Get your VM's external IP**:
```bash
curl http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google'
```

**Test the API**:
```
http://YOUR_VM_EXTERNAL_IP/
```

## 🎉 Done!

Your Face Recognition API is now running on:
- **VM**: Google Cloud Compute Engine
- **URL**: `http://YOUR_VM_EXTERNAL_IP`
- **Features**: Nginx reverse proxy, systemd service, automatic restarts
- **Cost**: ~$120/month (if running 24/7)

## 📋 Useful Commands

```bash
face-status     # Check API status
face-logs       # View live logs  
face-restart    # Restart API service
face-update     # Update from GitHub
face-monitor    # Full system status
```

## 💡 VM vs Cloud Run Comparison

| Feature | **VM** | **Cloud Run** |
|---------|---------|---------------|
| **Setup** | Manual configuration | Automatic |
| **Cost** | $120/month fixed | $0-50/month variable |
| **Control** | Full server control | Limited |
| **Scaling** | Manual | Automatic |
| **Maintenance** | You manage | Google manages |
| **Storage** | Persistent | Temporary |
| **Best for** | Always-on, full control | Variable traffic, serverless |

## 🔧 Advanced Configuration

### SSL/HTTPS Setup
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Cost Optimization
```bash
# Stop VM when not needed
gcloud compute instances stop face-api-vm --zone=us-central1-a

# Start when needed  
gcloud compute instances start face-api-vm --zone=us-central1-a
```

### Monitoring
```bash
# View all logs
sudo journalctl -u face-api -f

# System resources
htop
df -h
free -h
```

Your Face Recognition API is now fully deployed on Google Cloud VM! 🚀