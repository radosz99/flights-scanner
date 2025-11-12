# Nginx Setup - IMPORTANT

## Quick Start (Required Before First Deployment)

**CRITICAL**: Before starting nginx for the first time, you MUST create the `.htpasswd` file or nginx will fail to start.

### Option 1: Use Default Credentials (Quick)

```bash
cd nginx
cp .htpasswd.example .htpasswd
```

**Default credentials:**
- Username: `admin`
- Password: `changeme`

**⚠️ WARNING**: Change these credentials immediately after deployment!

### Option 2: Create Custom Credentials (Recommended)

```bash
cd nginx
./create-htpasswd.sh
```

This will prompt you to create a username and password.

## Why This Is Required

The nginx configuration requires HTTP Basic Auth for API documentation endpoints (`/api/docs`, `/api/redoc`). The auth configuration references `/etc/nginx/.htpasswd`, and nginx will **fail to start** if this file doesn't exist.

## After Deployment

1. **Change default password** if you used Option 1:
   ```bash
   cd nginx
   ./create-htpasswd.sh
   ```

2. **Restart nginx** to apply changes:
   ```bash
   make docker-restart
   ```

## Troubleshooting

### Nginx won't start / No logs

**Cause**: `.htpasswd` file is missing

**Solution**:
```bash
cd nginx
cp .htpasswd.example .htpasswd
make docker-restart
```

### Can't access API docs

**Cause**: Invalid credentials or .htpasswd file issue

**Solution**:
```bash
cd nginx
./create-htpasswd.sh  # Create new credentials
make docker-restart
```

## Security Notes

- The `.htpasswd` file is in `.gitignore` and won't be committed
- The `.htpasswd.example` file IS committed with default credentials
- Always change default credentials in production
- Use strong passwords: `openssl rand -base64 24`
