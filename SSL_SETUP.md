# Automatic SSL Setup with Let's Encrypt

This guide shows you how to set up SSL certificates **automatically** in just 2 steps!

## Prerequisites

1. A domain name pointing to your server's IP address
2. Ports 80 and 443 open in your firewall
3. Docker and Docker Compose installed

## Quick Setup (2 Steps!)

### Step 1: Start the Application

```bash
docker-compose up -d
```

Wait for all services to be healthy (~1-2 minutes).

### Step 2: Run the SSL Setup Script

```bash
./init-letsencrypt.sh your-domain.com your-email@example.com
```

**That's it!** The script will:
- Automatically obtain SSL certificates from Let's Encrypt
- Configure nginx with HTTPS
- Set up automatic certificate renewal (every 60 days)
- Redirect HTTP to HTTPS

## Examples

### With email (recommended for expiry notifications):
```bash
./init-letsencrypt.sh flights.example.com admin@example.com
```

### Without email:
```bash
./init-letsencrypt.sh flights.example.com
```

### Testing mode (to avoid rate limits during testing):
```bash
./init-letsencrypt.sh flights.example.com admin@example.com 1
```

## What Happens Automatically

1. **Certificate Generation**: Obtains SSL certificates from Let's Encrypt
2. **Nginx Configuration**: Updates nginx to use HTTPS with security best practices
3. **HTTP → HTTPS Redirect**: All HTTP traffic automatically redirects to HTTPS
4. **Auto-Renewal**: Certbot checks twice daily and renews certificates before expiry
5. **Nginx Reload**: Nginx automatically reloads every 6 hours to pick up renewed certificates

## Checking Certificate Status

View certificate information:
```bash
docker-compose exec certbot certbot certificates
```

Force certificate renewal:
```bash
docker-compose exec certbot certbot renew --force-renewal
docker-compose exec nginx nginx -s reload
```

## Troubleshooting

### "Failed to obtain certificate"

**Check your domain DNS:**
```bash
nslookup your-domain.com
```
Make sure it points to your server's IP address.

**Check if ports are open:**
```bash
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

**Check nginx logs:**
```bash
docker-compose logs nginx
```

### Certificate already exists

If you run the script again, it will ask if you want to renew the certificate.

### Rate Limits

Let's Encrypt has rate limits (50 certificates per domain per week). For testing, use staging mode:
```bash
./init-letsencrypt.sh your-domain.com your-email@example.com 1
```

## Manual Operations (Optional)

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart nginx only
docker-compose restart nginx
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Nginx logs only
docker-compose logs -f nginx

# Certbot logs only
docker-compose logs -f certbot
```

## Certificate Renewal

Certificates are automatically renewed by the Certbot service. No manual action required!

The Certbot container:
- Runs continuously
- Checks for renewal twice daily
- Renews certificates 30 days before expiry
- Nginx automatically reloads every 6 hours to pick up changes

## Security Features

The automatic setup includes:
- TLS 1.2 and 1.3 only
- Strong cipher suites (Mozilla Intermediate compatibility)
- OCSP stapling
- HSTS (HTTP Strict Transport Security)
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)

## No SSL / HTTP Only Mode

If you don't want SSL, just don't run the `init-letsencrypt.sh` script. The application will work over HTTP on port 80.

## Support

For issues with Let's Encrypt: https://community.letsencrypt.org/
For nginx configuration: https://nginx.org/en/docs/
