#!/bin/bash
# Production deployment script

set -e

echo "🚀 Starting Sikshya Kendra deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /var/www/sikshya_kendra
cd /var/www/sikshya_kendra

# Clone or update repository
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/yourusername/sikshya-kendra.git .
else
    echo "🔄 Updating repository..."
    git pull origin main
fi

# Create virtual environment
echo "🐍 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Setup database
echo "🗄️ Setting up database..."
sudo -u postgres createdb sikshya_db 2>/dev/null || true
sudo -u postgres createuser sikshya_user 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER sikshya_user WITH PASSWORD 'sikshya_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sikshya_db TO sikshya_user;"

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (if doesn't exist)
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sikshya.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

# Setup systemd service
echo "⚙️ Setting up systemd service..."
sudo tee /etc/systemd/system/sikshya.service > /dev/null <<EOF
[Unit]
Description=Sikshya Kendra Django App
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/sikshya_kendra
Environment="PATH=/var/www/sikshya_kendra/venv/bin"
ExecStart=/var/www/sikshya_kendra/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 std_portal.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx configuration
echo "🌐 Setting up Nginx..."
sudo tee /etc/nginx/sites-available/sikshya > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /var/www/sikshya_kendra/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/sikshya_kendra/media/;
        expires 7d;
    }
    
    client_max_body_size 10M;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/sikshya /etc/nginx/sites-enabled/
sudo nginx -t

# Set permissions
echo "🔒 Setting permissions..."
sudo chown -R www-data:www-data /var/www/sikshya_kendra
sudo chmod -R 755 /var/www/sikshya_kendra

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable sikshya
sudo systemctl start sikshya
sudo systemctl restart nginx
sudo systemctl restart redis-server

echo "✅ Deployment completed successfully!"
echo "🌐 Your site should be available at: http://yourdomain.com"
echo "👤 Admin panel: http://yourdomain.com/admin"
echo "📊 API docs: http://yourdomain.com/api/schema/swagger-ui/"