#!/bin/bash
# ============================================================
# AUREON SAAS PLATFORM - SERVER SETUP SCRIPT
# Rhematek Production Shield + Scale8
# Server: 147.93.47.35
# Domain: aureon.rhematek-solutions.com
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
PROJECT_NAME="aureon"
PROJECT_DIR="/opt/aureon"
DOMAIN="aureon.rhematek-solutions.com"
ADMIN_EMAIL="alerts@rhematek-solutions.com"
GIT_REPO="git@github.com:rhematek/aureon.git"  # Update with your repo

# ============================================================
# HELPER FUNCTIONS
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
}

# ============================================================
# PHASE 1: SYSTEM PREPARATION
# ============================================================

prepare_system() {
    log_step "PHASE 1: SYSTEM PREPARATION"

    # Update system
    log_info "Updating system packages..."
    apt-get update && apt-get upgrade -y

    # Install essential tools
    log_info "Installing essential tools..."
    apt-get install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        net-tools \
        ufw \
        fail2ban \
        certbot \
        python3-certbot-nginx \
        nginx \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release

    log_success "System prepared"
}

# ============================================================
# PHASE 2: INSTALL DOCKER
# ============================================================

install_docker() {
    log_step "PHASE 2: DOCKER INSTALLATION"

    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed: $(docker --version)"
    else
        log_info "Installing Docker..."

        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

        # Add Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        # Start and enable Docker
        systemctl start docker
        systemctl enable docker

        log_success "Docker installed: $(docker --version)"
    fi

    # Install Docker Compose standalone (for compatibility)
    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing Docker Compose standalone..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi

    log_success "Docker Compose installed: $(docker-compose --version)"
}

# ============================================================
# PHASE 3: CONFIGURE FIREWALL
# ============================================================

configure_firewall() {
    log_step "PHASE 3: FIREWALL CONFIGURATION"

    log_info "Configuring UFW firewall..."

    # Reset UFW
    ufw --force reset

    # Default policies
    ufw default deny incoming
    ufw default allow outgoing

    # Allow SSH
    ufw allow 22/tcp

    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    # Allow Docker ports (internal)
    # Note: Docker manages its own iptables rules

    # Enable UFW
    ufw --force enable

    log_success "Firewall configured"
    ufw status
}

# ============================================================
# PHASE 4: CONFIGURE FAIL2BAN
# ============================================================

configure_fail2ban() {
    log_step "PHASE 4: FAIL2BAN CONFIGURATION"

    log_info "Configuring Fail2Ban..."

    # Create jail.local
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/*error.log
findtime = 600
bantime = 7200
maxretry = 10
EOF

    # Restart Fail2Ban
    systemctl restart fail2ban
    systemctl enable fail2ban

    log_success "Fail2Ban configured"
}

# ============================================================
# PHASE 5: CLONE PROJECT
# ============================================================

clone_project() {
    log_step "PHASE 5: PROJECT SETUP"

    # Create project directory
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR

    # Clone or update repository
    if [ -d ".git" ]; then
        log_info "Updating existing repository..."
        git pull origin main
    else
        log_info "Cloning repository..."
        # If using SSH
        # git clone $GIT_REPO .
        # Or copy files manually
        log_warning "Please copy project files to $PROJECT_DIR"
    fi

    # Create required directories
    mkdir -p logs
    mkdir -p staticfiles
    mkdir -p mediafiles

    # Set permissions
    chmod -R 755 $PROJECT_DIR

    log_success "Project directory ready"
}

# ============================================================
# PHASE 6: CONFIGURE ENVIRONMENT
# ============================================================

configure_environment() {
    log_step "PHASE 6: ENVIRONMENT CONFIGURATION"

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_info "Creating .env file from template..."

        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        else
            cat > "$PROJECT_DIR/.env" << EOF
# Django Settings
DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://aureon_user:$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")@db:5432/aureon

# Redis
REDIS_URL=redis://redis-cache:6379/0
CELERY_BROKER_URL=redis://redis-queue:6379/0

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key

# Stripe
STRIPE_PUBLIC_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Sentry
SENTRY_DSN=

# Domain
SITE_URL=https://$DOMAIN
EOF
        fi

        log_warning "Please edit .env file with your actual values!"
        log_warning "File location: $PROJECT_DIR/.env"
    else
        log_success ".env file exists"
    fi
}

# ============================================================
# PHASE 7: SSL CERTIFICATE
# ============================================================

configure_ssl() {
    log_step "PHASE 7: SSL CERTIFICATE"

    log_info "Obtaining SSL certificate..."

    # Stop nginx temporarily
    systemctl stop nginx 2>/dev/null || true

    # Get certificate
    certbot certonly --standalone \
        -d $DOMAIN \
        -d www.$DOMAIN \
        --email $ADMIN_EMAIL \
        --agree-tos \
        --non-interactive \
        || log_warning "SSL certificate may already exist or failed"

    log_success "SSL certificate configured"
}

# ============================================================
# PHASE 8: NGINX CONFIGURATION
# ============================================================

configure_nginx() {
    log_step "PHASE 8: NGINX CONFIGURATION"

    log_info "Configuring Nginx..."

    # Create Nginx config
    cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
# Rate limiting zone
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

# Upstream
upstream aureon_app {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/aureon_access.log;
    error_log /var/log/nginx/aureon_error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias $PROJECT_DIR/mediafiles/;
        expires 7d;
    }

    # Health check (no rate limit)
    location /api/health/ {
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API endpoints (rate limited)
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 90;
    }

    # Login endpoint (strict rate limit)
    location /api/auth/login/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Webhooks (no rate limit, signature verified in app)
    location /webhooks/ {
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Admin (rate limited)
    location /admin/ {
        limit_req zone=login burst=10 nodelay;
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Frontend and catch-all
    location / {
        proxy_pass http://aureon_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /500.html;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Test and restart Nginx
    nginx -t
    systemctl restart nginx
    systemctl enable nginx

    log_success "Nginx configured"
}

# ============================================================
# PHASE 9: DEPLOY APPLICATION
# ============================================================

deploy_application() {
    log_step "PHASE 9: APPLICATION DEPLOYMENT"

    cd $PROJECT_DIR

    log_info "Building and starting containers..."

    # Build and start with production compose
    docker compose -f docker-compose.prod.yml build --no-cache
    docker compose -f docker-compose.prod.yml up -d

    # Wait for services
    log_info "Waiting for services to start..."
    sleep 30

    # Run migrations
    log_info "Running database migrations..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

    # Collect static files
    log_info "Collecting static files..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

    # Create superuser if not exists
    log_info "Creating superuser..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@rhematek-solutions.com', 'AdminPass123!')
    print('Superuser created')
else:
    print('Superuser already exists')
"

    # Create notification templates
    log_info "Creating notification templates..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py create_notification_templates || true

    log_success "Application deployed"
}

# ============================================================
# PHASE 10: VERIFICATION
# ============================================================

verify_deployment() {
    log_step "PHASE 10: DEPLOYMENT VERIFICATION"

    cd $PROJECT_DIR

    # Check container status
    log_info "Checking container status..."
    docker compose -f docker-compose.prod.yml ps

    # Health check
    log_info "Running health check..."
    sleep 5
    http_code=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/api/health/ || echo "000")

    if [ "$http_code" == "200" ]; then
        log_success "Health check passed (HTTP 200)"
    else
        log_error "Health check failed (HTTP $http_code)"
    fi

    # Check logs
    log_info "Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=20

    echo ""
    echo "============================================================"
    echo "  DEPLOYMENT COMPLETE"
    echo "============================================================"
    echo ""
    echo "  URL: https://$DOMAIN"
    echo "  Admin: https://$DOMAIN/admin/"
    echo "  API Docs: https://$DOMAIN/api/docs/"
    echo "  Health: https://$DOMAIN/api/health/"
    echo ""
    echo "  Default Admin:"
    echo "    Email: admin@rhematek-solutions.com"
    echo "    Password: AdminPass123! (CHANGE IMMEDIATELY!)"
    echo ""
    echo "  RHEMATEK PRODUCTION SHIELD: ENGAGED"
    echo "============================================================"
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  AUREON SERVER SETUP"
    echo "  Rhematek Production Shield + Scale8"
    echo "  Server: $(hostname) ($(curl -s ifconfig.me))"
    echo "  Target: $DOMAIN"
    echo "  Date: $(date)"
    echo "============================================================"
    echo ""

    # Confirm
    read -p "Continue with server setup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi

    # Run all phases
    prepare_system
    install_docker
    configure_firewall
    configure_fail2ban
    clone_project
    configure_environment
    configure_ssl
    configure_nginx
    deploy_application
    verify_deployment

    echo ""
    echo "Setup complete! Please update the .env file and restart if needed."
}

# Handle command line arguments
case "${1:-}" in
    --deploy-only)
        deploy_application
        verify_deployment
        ;;
    --verify)
        verify_deployment
        ;;
    --ssl)
        configure_ssl
        configure_nginx
        ;;
    *)
        main
        ;;
esac
