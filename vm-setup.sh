#!/bin/bash

# Face Recognition API VM Setup Script
# This script automatically sets up your Face Recognition API on a fresh Ubuntu VM

set -e  # Exit on any error

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root or with sudo" 
   echo "Usage: sudo ./vm-setup.sh"
   exit 1
fi

echo "🚀 Starting Face Recognition API VM Setup..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.9 and essential packages
echo "🐍 Installing Python and dependencies..."
sudo apt-get install -y python3 python3-pip python3-dev python3-venv
sudo apt-get install -y build-essential cmake pkg-config
sudo apt-get install -y libopenblas-dev liblapack-dev libatlas-base-dev
sudo apt-get install -y libx11-dev libgtk-3-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y libjpeg-dev libpng-dev libtiff-dev
sudo apt-get install -y git curl nginx htop

# Create application user
echo "👤 Creating application user..."
sudo useradd -r -s /bin/bash -d /opt/face-api face-api || true
sudo mkdir -p /opt/face-api
sudo chown face-api:face-api /opt/face-api

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
cd /opt/face-api
sudo -u face-api python3 -m venv venv
sudo -u face-api venv/bin/pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
# Install dlib first (it's often problematic)
sudo -u face-api venv/bin/pip install dlib
sudo -u face-api venv/bin/pip install -r requirements.txt
sudo -u face-api venv/bin/pip install gunicorn

# Create necessary directories
echo "📁 Creating application directories..."
sudo -u face-api mkdir -p uploads faces logs

# Set proper permissions
sudo chmod 755 /opt/face-api
sudo chmod -R 755 /opt/face-api/uploads
sudo chmod -R 755 /opt/face-api/faces

# Create environment file template
echo "⚙️ Creating environment configuration..."
sudo tee /opt/face-api/.env.template > /dev/null << EOF
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# MongoDB Configuration
MONGODB_URI=mongodb+srv://cdgprjs:cdgprjs@cluster0.ff19f.mongodb.net/1dfasdf?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME=face_galleryw

# Upload Configuration
UPLOAD_FOLDER=uploads
FACES_FOLDER=faces
MAX_CONTENT_LENGTH=16777216

# Clustering Configuration
DBSCAN_EPS=0.4
DBSCAN_MIN_SAMPLES=1
FACE_RECOGNITION_TOLERANCE=0.5
MIN_FACE_SIZE=50

# CORS Configuration
CORS_ORIGINS=https://face-gallery-client.vercel.app

# Server Configuration
PORT=5000
EOF

sudo chown face-api:face-api /opt/face-api/.env.template

# Create systemd service
echo "🔄 Creating systemd service..."
sudo tee /etc/systemd/system/face-api.service > /dev/null << EOF
[Unit]
Description=Face Recognition API
After=network.target

[Service]
Type=exec
User=face-api
Group=face-api
WorkingDirectory=/opt/face-api
Environment=PATH=/opt/face-api/venv/bin
EnvironmentFile=/opt/face-api/.env
ExecStart=/opt/face-api/venv/bin/gunicorn --workers 1 --bind 127.0.0.1:5000 --timeout 300 --max-requests 1000 --access-logfile /opt/face-api/logs/access.log --error-logfile /opt/face-api/logs/error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/face-api > /dev/null << EOF
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
        alias /opt/face-api/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header 'Access-Control-Allow-Origin' '*' always;
    }
    
    # Serve face images directly
    location /faces/ {
        alias /opt/face-api/faces/;
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
sudo ln -sf /etc/nginx/sites-available/face-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Create self-signed SSL certificate for HTTPS
echo "🔐 Creating self-signed SSL certificate..."
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/face-api.key \
    -out /etc/nginx/ssl/face-api.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=face-api"

# Set proper permissions for SSL files
sudo chmod 600 /etc/nginx/ssl/face-api.key
sudo chmod 644 /etc/nginx/ssl/face-api.crt

# Update Nginx configuration to support HTTPS
echo "🌐 Updating Nginx configuration for HTTPS..."
sudo tee /etc/nginx/sites-available/face-api > /dev/null << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/face-api.crt;
    ssl_certificate_key /etc/nginx/ssl/face-api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Increase client max body size for image uploads
    client_max_body_size 50M;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
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
        alias /opt/face-api/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header 'Access-Control-Allow-Origin' '*' always;
    }
    
    # Serve face images directly
    location /faces/ {
        alias /opt/face-api/faces/;
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

# Create log rotation
sudo tee /etc/logrotate.d/face-api > /dev/null << EOF
/opt/face-api/logs/*.log {
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
sudo tee /opt/face-api/update.sh > /dev/null << EOF
#!/bin/bash
echo "🔄 Updating Face Recognition API..."
cd /opt/face-api
sudo -u face-api git pull origin main
cd /opt/face-api
sudo -u face-api venv/bin/pip install -r requirements.txt
sudo systemctl restart face-api
echo "✅ Update completed!"
EOF

sudo chmod +x /opt/face-api/update.sh

# Create monitoring script
sudo tee /opt/face-api/monitor.sh > /dev/null << EOF
#!/bin/bash
echo "📊 Face API System Status"
echo "========================"
echo
echo "🔄 Service Status:"
sudo systemctl status face-api --no-pager -l
echo
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager -l
echo
echo "💾 Memory Usage:"
free -h
echo
echo "💽 Disk Usage:"
df -h /
echo
echo "📈 API Logs (last 10 lines):"
tail -n 10 /opt/face-api/logs/error.log 2>/dev/null || echo "No error logs yet"
EOF

sudo chmod +x /opt/face-api/monitor.sh

# Create validation script
sudo tee /opt/face-api/validate-setup.sh > /dev/null << EOF
#!/bin/bash
echo "🔍 Validating Face API Setup..."
echo "=============================="

# Check Python environment
echo "1. Python Environment:"
if [ -f "/opt/face-api/venv/bin/python" ]; then
    echo "   ✅ Virtual environment exists"
    /opt/face-api/venv/bin/python --version
else
    echo "   ❌ Virtual environment missing"
fi

# Check dependencies
echo "2. Dependencies:"
/opt/face-api/venv/bin/pip list | grep -E "(flask|face-recognition|dlib|gunicorn)" || echo "   ❌ Some dependencies missing"

# Check files
echo "3. Application Files:"
[ -f "/opt/face-api/app.py" ] && echo "   ✅ app.py found" || echo "   ❌ app.py missing"
[ -f "/opt/face-api/requirements.txt" ] && echo "   ✅ requirements.txt found" || echo "   ❌ requirements.txt missing"
[ -f "/opt/face-api/.env.template" ] && echo "   ✅ .env.template found" || echo "   ❌ .env.template missing"

# Check directories
echo "4. Directories:"
[ -d "/opt/face-api/uploads" ] && echo "   ✅ uploads directory" || echo "   ❌ uploads directory missing"
[ -d "/opt/face-api/faces" ] && echo "   ✅ faces directory" || echo "   ❌ faces directory missing"
[ -d "/opt/face-api/logs" ] && echo "   ✅ logs directory" || echo "   ❌ logs directory missing"

# Check services
echo "5. Services:"
sudo systemctl is-enabled nginx >/dev/null && echo "   ✅ Nginx enabled" || echo "   ❌ Nginx not enabled"
sudo systemctl is-active nginx >/dev/null && echo "   ✅ Nginx running" || echo "   ❌ Nginx not running"

echo
echo "Setup validation completed!"
echo "Next: Create .env file and start face-api service"
EOF

sudo chmod +x /opt/face-api/validate-setup.sh

# Create Let's Encrypt setup script (for when domain is available)
sudo tee /opt/face-api/setup-letsencrypt.sh > /dev/null << EOF
#!/bin/bash
echo "🔐 Setting up Let's Encrypt SSL Certificate..."
echo "============================================="

# Check if domain is provided
if [ -z "\$1" ]; then
    echo "❌ Please provide your domain name"
    echo "Usage: sudo /opt/face-api/setup-letsencrypt.sh your-domain.com"
    exit 1
fi

DOMAIN=\$1

echo "📦 Installing Certbot..."
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

echo "🔒 Obtaining SSL certificate for \$DOMAIN..."
sudo certbot --nginx -d \$DOMAIN --non-interactive --agree-tos --email admin@\$DOMAIN

echo "⚙️ Setting up auto-renewal..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

echo "✅ Let's Encrypt SSL setup completed!"
echo "Your API is now available at: https://\$DOMAIN"
EOF

sudo chmod +x /opt/face-api/setup-letsencrypt.sh

# Create IP-to-HTTPS access script
sudo tee /opt/face-api/get-https-access.sh > /dev/null << EOF
#!/bin/bash
echo "🌐 HTTPS Access Information"
echo "=========================="

# Get external IP
EXTERNAL_IP=\$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google' 2>/dev/null || curl -s https://ipinfo.io/ip 2>/dev/null || echo "Unable to detect")

echo "🔒 HTTPS URLs (Self-signed certificate):"
echo "   Local:    https://localhost/"
echo "   External: https://\$EXTERNAL_IP/"
echo
echo "⚠️  Browser Security Warning:"
echo "   - Click 'Advanced' or 'Show Details'"
echo "   - Click 'Proceed to localhost (unsafe)' or similar"
echo "   - This is normal for self-signed certificates"
echo
echo "🔐 For trusted certificates:"
echo "   1. Get a domain name"
echo "   2. Point domain to this IP: \$EXTERNAL_IP"
echo "   3. Run: sudo /opt/face-api/setup-letsencrypt.sh your-domain.com"
echo
echo "🧪 Test HTTPS connection:"
echo "   curl -k https://\$EXTERNAL_IP/"
EOF

sudo chmod +x /opt/face-api/get-https-access.sh

# Enable and start services
echo "🏁 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable nginx
sudo systemctl restart nginx

# Note: Don't start face-api service yet - needs .env file first

# Create helpful aliases
# Determine the non-root user's home directory
if [ "$SUDO_USER" ]; then
    USER_HOME=$(eval echo ~$SUDO_USER)
    USER_NAME=$SUDO_USER
else
    USER_HOME=$HOME
    USER_NAME=$(whoami)
fi

# Only create aliases if we have a valid user home directory
if [ -d "$USER_HOME" ] && [ "$USER_NAME" != "root" ]; then
    echo "📝 Creating helpful aliases for user $USER_NAME..."
    sudo tee "$USER_HOME/.bash_aliases" > /dev/null << EOF
# Face API aliases
alias face-status='sudo systemctl status face-api'
alias face-logs='sudo journalctl -u face-api -f'
alias face-restart='sudo systemctl restart face-api'
alias face-update='sudo /opt/face-api/update.sh'
alias face-monitor='sudo /opt/face-api/monitor.sh'
alias face-validate='sudo /opt/face-api/validate-setup.sh'
alias nginx-test='sudo nginx -t'
alias nginx-reload='sudo systemctl reload nginx'
alias https-info='sudo /opt/face-api/get-https-access.sh'
alias setup-ssl='sudo /opt/face-api/setup-letsencrypt.sh'
EOF
    sudo chown $USER_NAME:$USER_NAME "$USER_HOME/.bash_aliases"
    echo "✅ Aliases created in $USER_HOME/.bash_aliases"
else
    echo "⚠️  Skipping alias creation - no suitable user home directory found"
fi

# Final instructions
echo
echo "🎉 Face Recognition API VM Setup Complete!"
echo "=========================================="
echo
echo "⚠️  IMPORTANT: Complete these steps manually:"
echo
echo "1. Create your environment file:"
echo "   sudo cp /opt/face-api/.env.template /opt/face-api/.env"
echo "   sudo nano /opt/face-api/.env"
echo "   (Update MongoDB URI and secret key)"
echo
echo "2. Start the API service:"
echo "   sudo systemctl enable face-api"
echo "   sudo systemctl start face-api"
echo
echo "3. Validate setup:"
echo "   face-validate"
echo
echo "4. Check service status:"
echo "   face-status"
echo
echo "5. Test your API:"
echo "   # HTTP (will redirect to HTTPS):"
echo "   curl http://localhost/"
echo "   # HTTPS (self-signed certificate):"
echo "   curl -k https://localhost/"
echo "   curl -k https://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google')/"
echo
echo "📋 Useful commands:"
echo "   face-status    - Check API status"
echo "   face-logs      - View live logs"
echo "   face-restart   - Restart API"
echo "   face-update    - Update from GitHub"
echo "   face-monitor   - System monitoring"
echo "   face-validate  - Validate setup"
echo "   https-info     - Get HTTPS access URLs"
echo "   setup-ssl      - Setup Let's Encrypt (requires domain)"
echo
echo "📁 Important paths:"
echo "   API Code: /opt/face-api/"
echo "   Logs: /opt/face-api/logs/"
echo "   Uploads: /opt/face-api/uploads/"
echo "   Faces: /opt/face-api/faces/"
echo
echo "🔧 Next steps:"
echo "   1. Configure your .env file with MongoDB connection"
echo "   2. Start the service"
echo "   3. Access your API via HTTPS (self-signed certificate)"
echo "   4. For production: Get a domain and use Let's Encrypt for trusted SSL"
echo
echo "🔐 SSL Information:"
echo "   - Self-signed certificate created for immediate HTTPS"
echo "   - Browsers will show security warning (click 'Advanced' -> 'Proceed')"
echo "   - HTTP traffic automatically redirects to HTTPS"
echo "   - For trusted certificates, get a domain and use Let's Encrypt"
echo
echo "✅ Setup completed successfully!"