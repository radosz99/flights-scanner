#!/bin/bash

# Automated Let's Encrypt SSL Certificate Setup
# This script will automatically obtain and configure SSL certificates for your domain

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  Let's Encrypt SSL Setup (Automated)${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Domain name is required${NC}"
    echo ""
    echo "Usage: ./init-letsencrypt.sh your-domain.com [email@example.com]"
    echo ""
    echo "Example: ./init-letsencrypt.sh flights.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}
STAGING=${3:-0} # Set to 1 for testing to avoid rate limits

# Validate email
if [ -z "$EMAIL" ]; then
    echo -e "${YELLOW}Warning: No email provided. Using --register-unsafely-without-email${NC}"
    echo "It's recommended to provide an email for certificate expiry notifications"
    EMAIL_ARG="--register-unsafely-without-email"
else
    EMAIL_ARG="--email $EMAIL"
fi

# Set up directories
echo -e "${GREEN}Setting up directories...${NC}"
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p nginx/conf.d

# Pre-flight checks
echo -e "${GREEN}Running pre-flight checks...${NC}"
echo -e "${YELLOW}1. Checking if domain resolves...${NC}"
if command -v dig &> /dev/null; then
    RESOLVED_IP=$(dig +short $DOMAIN | tail -n1)
    if [ -z "$RESOLVED_IP" ]; then
        echo -e "${RED}ERROR: Domain $DOMAIN does not resolve to any IP${NC}"
        echo "Please ensure your DNS records are configured correctly"
        exit 1
    fi
    echo -e "   Domain resolves to: ${GREEN}$RESOLVED_IP${NC}"
else
    echo -e "   ${YELLOW}Skipping DNS check (dig not available)${NC}"
fi

echo -e "${YELLOW}2. Checking if port 80 is accessible...${NC}"
if command -v nc &> /dev/null; then
    if nc -z localhost 80; then
        echo -e "   Port 80 is ${GREEN}accessible${NC}"
    else
        echo -e "   ${RED}ERROR: Port 80 is not accessible${NC}"
        echo "Please ensure nginx is running and port 80 is not blocked"
        exit 1
    fi
else
    echo -e "   ${YELLOW}Skipping port check (nc not available)${NC}"
fi

# Check if certificate already exists
if [ -d "certbot/conf/live/$DOMAIN" ]; then
    echo -e "${YELLOW}Certificate for $DOMAIN already exists!${NC}"
    read -p "Do you want to renew it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
    RENEW=1
else
    RENEW=0
fi

# Create temporary nginx configuration for ACME challenge
echo -e "${GREEN}Creating temporary nginx configuration...${NC}"
cat > nginx/conf.d/default.conf << EOF
# Temporary HTTP server for ACME challenge
server {
    listen 80;
    server_name $DOMAIN;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Temporary proxy to backend/frontend
    location /api/ {
        proxy_pass http://backend:8900/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://frontend:8901;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Start services
echo -e "${GREEN}Starting Docker services...${NC}"
docker-compose --profile production up -d nginx

# Wait for nginx to be ready
echo -e "${GREEN}Waiting for nginx to be ready...${NC}"
sleep 5

# Test ACME challenge accessibility
echo -e "${GREEN}Testing ACME challenge accessibility...${NC}"
mkdir -p certbot/www/.well-known/acme-challenge
echo "test" > certbot/www/.well-known/acme-challenge/test.txt
sleep 2
if curl -f -s http://localhost/.well-known/acme-challenge/test.txt > /dev/null 2>&1; then
    echo -e "   ${GREEN}ACME challenge path is accessible${NC}"
else
    echo -e "   ${YELLOW}WARNING: ACME challenge path may not be accessible${NC}"
    echo "   This might cause certificate validation to fail"
fi
rm -f certbot/www/.well-known/acme-challenge/test.txt

# Obtain certificate
echo -e "${GREEN}Obtaining SSL certificate from Let's Encrypt...${NC}"

if [ $STAGING -eq 1 ]; then
    echo -e "${YELLOW}Using staging server (test mode)${NC}"
    STAGING_ARG="--staging"
else
    STAGING_ARG=""
fi

if [ $RENEW -eq 1 ]; then
    # Force renewal
    echo -e "${YELLOW}Renewing existing certificate...${NC}"
    docker-compose --profile production run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        $EMAIL_ARG \
        --agree-tos \
        --force-renewal \
        --verbose \
        $STAGING_ARG \
        -d $DOMAIN
else
    # New certificate
    echo -e "${YELLOW}Requesting new certificate for $DOMAIN...${NC}"
    echo -e "${YELLOW}This may take a minute...${NC}"
    docker-compose --profile production run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        $EMAIL_ARG \
        --agree-tos \
        --no-eff-email \
        --verbose \
        --force-renewal \
        $STAGING_ARG \
        -d $DOMAIN
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to obtain certificate!${NC}"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo "  1. Domain $DOMAIN doesn't point to this server's IP address"
    echo "  2. Port 80 is not accessible from the internet (firewall/security group)"
    echo "  3. DNS hasn't propagated yet (wait 5-10 minutes after DNS changes)"
    echo "  4. Another service is using port 80"
    echo ""
    echo -e "${YELLOW}Checking certbot logs for more details:${NC}"
    if [ -f "certbot/conf/logs/letsencrypt.log" ]; then
        tail -20 certbot/conf/logs/letsencrypt.log
    else
        echo "No log file found at certbot/conf/logs/letsencrypt.log"
    fi
    echo ""
    echo -e "${YELLOW}You can also check the log with:${NC}"
    echo "  docker-compose logs certbot"
    exit 1
fi

# Create production nginx configuration with SSL
echo -e "${GREEN}Creating production nginx configuration with SSL...${NC}"
cat > nginx/conf.d/default.conf << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL certificate paths (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration - Mozilla Intermediate compatibility
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend:8900/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Increase timeouts for long-running scan operations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Frontend proxy
    location / {
        proxy_pass http://frontend:8901;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Reload nginx with new configuration
echo -e "${GREEN}Reloading nginx with SSL configuration...${NC}"
docker-compose --profile production exec nginx nginx -s reload

# Start certbot for auto-renewal
echo -e "${GREEN}Starting certbot auto-renewal service...${NC}"
docker-compose --profile production up -d certbot

echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}     SSL Setup Complete! 🎉${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "Your site is now available at:"
echo -e "  ${GREEN}https://$DOMAIN${NC}"
echo ""
echo -e "Certificate details:"
echo -e "  Domain: ${GREEN}$DOMAIN${NC}"
echo -e "  Auto-renewal: ${GREEN}Enabled${NC} (checks twice daily)"
echo -e "  Certificate location: ${GREEN}./certbot/conf/live/$DOMAIN/${NC}"
echo ""
echo -e "${YELLOW}Note: Certificates will auto-renew every 60 days${NC}"
echo ""
