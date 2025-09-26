#!/bin/bash

# Face Recognition API VM Setup Script
# This script automatically sets up your Face Recognition API on a fresh Ubuntu VM

set -e  # Exit on any error

echo "🚀 Starting Face Recognition API VM Setup..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Python 3.9 and essential packages
echo "🐍 Installing Python and dependencies..."
apt-get install -y python3.9 python3.9-pip python3.9-dev python3.9-venv
apt-get install -y build-essential cmake pkg-config
apt-get install -y libopenblas-dev liblapack-dev libatlas-base-dev
apt-get install -y libx11-dev libgtk-3-dev
apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
apt-get install -y libjpeg-dev libpng-dev libtiff-dev
apt-get install -y git curl nginx supervisor htop

# Create application user
echo "👤 Creating application user..."
useradd -r -s /bin/bash -d /opt/face-api face-api || true
mkdir -p /opt/face-api
chown face-api:face-api /opt/face-api

# Clone repository as face-api user
echo "📥 Cloning repository..."
cd /opt/face-api
if [ ! -d ".git" ]; then
    sudo -u face-api git clone https://github.com/hishamac/face-gallery-api.git .
else
    sudo -u face-api git pull origin main
fi

# Setup Python environment
echo "🔧 Setting up Python virtual environment..."
cd /opt/face-api/api
sudo -u face-api python3.9 -m venv venv
sudo -u face-api venv/bin/pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u face-api venv/bin/pip install -r requirements.txt
sudo -u face-api venv/bin/pip install gunicorn

# Create necessary directories
echo "📁 Creating application directories..."
sudo -u face-api mkdir -p uploads faces logs
sudo -u face-api mkdir -p /opt/face-api/api/uploads
sudo -u face-api mkdir -p /opt/face-api/api/faces

# Set proper permissions
chmod 755 /opt/face-api
chmod -R 755 /opt/face-api/api/uploads
chmod -R 755 /opt/face-api/api/faces

# Create environment file template
echo "⚙️ Creating environment configuration..."
cat > /opt/face-api/api/.env.template << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=CHANGE-THIS-TO-A-SECURE-RANDOM-STRING
FLASK_DEBUG=False

# MongoDB Configuration (Replace with your MongoDB Atlas connection string)
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

# CORS Configuration (Update with your frontend domain)
CORS_ORIGINS=*

# Server Configuration
PORT=5000
EOF

chown face-api:face-api /opt/face-api/api/.env.template

# Create systemd service
echo "🔄 Creating systemd service..."
cat > /etc/systemd/system/face-api.service << EOF
[Unit]
Description=Face Recognition API
After=network.target

[Service]
Type=exec
User=face-api
Group=face-api
WorkingDirectory=/opt/face-api/api
Environment=PATH=/opt/face-api/api/venv/bin
EnvironmentFile=/opt/face-api/api/.env
ExecStart=/opt/face-api/api/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 --timeout 300 --max-requests 1000 --access-logfile /opt/face-api/api/logs/access.log --error-logfile /opt/face-api/api/logs/error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/face-api << EOF
server {
    listen 80;
    server_name _;
    
    # Increase client max body size for image uploads
    client_max_body_size 50M;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Increase timeout for face processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # CORS headers (customize as needed)
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
    
    # Serve uploaded images directly
    location /uploads/ {
        alias /opt/face-api/api/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header 'Access-Control-Allow-Origin' '*' always;
    }
    
    # Serve face images directly
    location /faces/ {
        alias /opt/face-api/api/faces/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header 'Access-Control-Allow-Origin' '*' always;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/face-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Create log rotation
cat > /etc/logrotate.d/face-api << EOF
/opt/face-api/api/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 face-api face-api
    postrotate
        systemctl reload face-api || true
    endscript
}
EOF

# Create update script
cat > /opt/face-api/update.sh << EOF
#!/bin/bash
echo "🔄 Updating Face Recognition API..."
cd /opt/face-api
sudo -u face-api git pull origin main
cd api
sudo -u face-api venv/bin/pip install -r requirements.txt
systemctl restart face-api
echo "✅ Update completed!"
EOF

chmod +x /opt/face-api/update.sh

# Create monitoring script
cat > /opt/face-api/monitor.sh << EOF
#!/bin/bash
echo "📊 Face API System Status"
echo "========================"
echo
echo "🔄 Service Status:"
systemctl status face-api --no-pager -l
echo
echo "🌐 Nginx Status:"
systemctl status nginx --no-pager -l
echo
echo "💾 Memory Usage:"
free -h
echo
echo "💽 Disk Usage:"
df -h /
echo
echo "📈 API Logs (last 10 lines):"
tail -n 10 /opt/face-api/api/logs/error.log 2>/dev/null || echo "No error logs yet"
EOF

chmod +x /opt/face-api/monitor.sh

# Enable and start services
echo "🏁 Starting services..."
systemctl daemon-reload
systemctl enable face-api
systemctl enable nginx
systemctl restart nginx

# Create helpful aliases
cat > /home/ubuntu/.bash_aliases << EOF
# Face API aliases
alias face-status='sudo systemctl status face-api'
alias face-logs='sudo journalctl -u face-api -f'
alias face-restart='sudo systemctl restart face-api'
alias face-update='sudo /opt/face-api/update.sh'
alias face-monitor='sudo /opt/face-api/monitor.sh'
alias nginx-test='sudo nginx -t'
alias nginx-reload='sudo systemctl reload nginx'
EOF

# Final instructions
echo
echo "🎉 Face Recognition API VM Setup Complete!"
echo "=========================================="
echo
echo "⚠️  IMPORTANT: Complete these steps manually:"
echo
echo "1. Create your environment file:"
echo "   sudo cp /opt/face-api/api/.env.template /opt/face-api/api/.env"
echo "   sudo nano /opt/face-api/api/.env"
echo "   (Update MongoDB URI and secret key)"
echo
echo "2. Start the API service:"
echo "   sudo systemctl start face-api"
echo
echo "3. Check service status:"
echo "   sudo systemctl status face-api"
echo
echo "4. Test your API:"
echo "   curl http://localhost/"
echo "   curl http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google')/"
echo
echo "📋 Useful commands:"
echo "   face-status    - Check API status"
echo "   face-logs      - View live logs"
echo "   face-restart   - Restart API"
echo "   face-update    - Update from GitHub"
echo "   face-monitor   - System monitoring"
echo
echo "📁 Important paths:"
echo "   API Code: /opt/face-api/api/"
echo "   Logs: /opt/face-api/api/logs/"
echo "   Uploads: /opt/face-api/api/uploads/"
echo "   Faces: /opt/face-api/api/faces/"
echo
echo "🔧 Next steps:"
echo "   1. Configure your .env file with MongoDB connection"
echo "   2. Start the service"
echo "   3. Point your domain to this VM's external IP"
echo "   4. Set up SSL with Let's Encrypt (optional)"
echo
echo "✅ Setup completed successfully!"