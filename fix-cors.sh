#!/bin/bash

echo "🔧 Fixing CORS Headers Duplication Issue..."
echo "=========================================="

# Backup current nginx config
BACKUP_FILE="/etc/nginx/sites-available/face-api.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp /etc/nginx/sites-available/face-api "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Create clean nginx configuration without CORS headers
echo "🔄 Creating clean Nginx configuration..."
sudo tee /etc/nginx/sites-available/face-api > /dev/null << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
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
    
    # API endpoints - Flask handles CORS
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
        
        # Let Flask handle all CORS headers
    }
    
    # Serve uploaded images directly
    location /uploads/ {
        alias /opt/face-api/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        # Flask handles CORS for consistency
    }
    
    # Serve face images directly
    location /faces/ {
        alias /opt/face-api/faces/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        # Flask handles CORS for consistency
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

echo "🔄 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration test failed!"
    echo "🔄 Restoring backup..."
    sudo cp "$BACKUP_FILE" /etc/nginx/sites-available/face-api
    echo "⚠️  Backup restored. Please check the configuration manually."
    exit 1
fi

echo ""
echo "🎉 CORS Fix Complete!"
echo "===================="
echo ""
echo "✅ Flask-CORS will now handle all CORS headers"
echo "✅ No more duplicate CORS headers from Nginx"
echo ""
echo "📝 Make sure your .env file has:"
echo "   CORS_ORIGINS=https://face-gallery-client.vercel.app"
echo ""
echo "🔄 Restart your Flask app to apply changes:"
echo "   sudo systemctl restart face-api"
echo ""
echo "🧪 Test your API from the browser now!"