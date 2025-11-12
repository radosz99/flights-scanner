# Nginx Configuration and HTTP Basic Authentication

This directory contains the nginx configuration for the Flights Scanner API, including HTTP Basic Authentication for API documentation endpoints.

## Overview

The nginx reverse proxy:
- Routes `/api/*` requests to the backend FastAPI server
- Routes `/` requests to the frontend Nuxt.js server
- Protects API documentation endpoints with HTTP Basic Auth
- Handles SSL/TLS certificates via Certbot

## Protected Endpoints

The following endpoints require HTTP Basic Authentication:
- `/api/docs` - Swagger UI
- `/api/redoc` - ReDoc documentation
- `/api/openapi.json` - OpenAPI schema

All other API endpoints are publicly accessible (though some require API keys for write operations).

## Setting Up HTTP Basic Authentication

### Quick Setup (Recommended)

Use the provided script to create credentials:

```bash
cd nginx
./create-htpasswd.sh
```

This will:
1. Check if `htpasswd` is installed
2. Prompt for username and password
3. Create or update the `.htpasswd` file with bcrypt-hashed password
4. Show instructions for accessing the docs

### Manual Setup

If you prefer to create the file manually or don't have `htpasswd` installed:

#### Option 1: Using htpasswd command

```bash
# Install htpasswd if not available:
# - Ubuntu/Debian: sudo apt-get install apache2-utils
# - CentOS/RHEL: sudo yum install httpd-tools
# - macOS: pre-installed with Apache

# Create .htpasswd file with first user
htpasswd -Bc nginx/.htpasswd username

# Add more users
htpasswd -B nginx/.htpasswd another_user
```

#### Option 2: Using openssl

```bash
# Generate password hash
openssl passwd -apr1

# Manually create .htpasswd file
echo "username:hashed_password_here" > nginx/.htpasswd
```

#### Option 3: Online generator

1. Visit: https://hostingcanada.org/htpasswd-generator/
2. Enter username and password
3. Copy the generated line
4. Create `nginx/.htpasswd` with the content

### Apply Changes

After creating or updating `.htpasswd`, restart nginx:

```bash
# From project root
make docker-restart

# Or manually
docker-compose restart nginx
```

## Managing Users

### Add or Update User

```bash
cd nginx
./create-htpasswd.sh
```

### Remove User

```bash
htpasswd -D nginx/.htpasswd username
```

### List All Users

```bash
cat nginx/.htpasswd
# Output shows: username:hashed_password
```

### Change Password

Run the script again with the same username - it will update the password:

```bash
cd nginx
./create-htpasswd.sh
```

## File Structure

```
nginx/
├── nginx.conf              # Main nginx configuration
├── conf.d/
│   └── default.conf       # Server blocks and routing rules
├── create-htpasswd.sh     # Script to create/update credentials
├── .htpasswd              # Password file (gitignored, create this)
└── README.md              # This file
```

## Security Notes

### Password File Security

- ✅ **`.htpasswd` is in `.gitignore`** - Never committed to version control
- ✅ **Mounted as read-only** in docker-compose.yml
- ✅ **Uses bcrypt hashing** - Strong password encryption
- ⚠️ **Keep credentials secure** - Store them in a password manager

### Password Strength

Use strong passwords for production:
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Generate with: `openssl rand -base64 24`

### Best Practices

1. **Create separate accounts** for each team member
2. **Rotate passwords** regularly (every 90 days)
3. **Remove accounts** immediately when access is no longer needed
4. **Monitor access** via nginx logs: `docker-compose logs nginx | grep docs`

## Accessing Protected Documentation

Once credentials are set up:

1. **Open browser** and navigate to:
   - https://wylot.eu/api/docs (Swagger UI)
   - https://wylot.eu/api/redoc (ReDoc)

2. **Enter credentials** when prompted:
   - Username: (the one you created)
   - Password: (the one you created)

3. **Browser will remember** credentials for the session

### Programmatic Access

To access docs programmatically with basic auth:

```bash
# Using curl
curl -u username:password https://wylot.eu/api/docs

# Using wget
wget --user=username --password=password https://wylot.eu/api/docs

# Using httpie
http -a username:password https://wylot.eu/api/docs
```

### Logout

To logout from basic auth:
- Close all browser windows
- Clear browser credentials for the site
- Or visit: https://logout@wylot.eu/api/docs

## Troubleshooting

### "htpasswd: command not found"

Install apache2-utils:

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install apache2-utils

# CentOS/RedHat
sudo yum install httpd-tools

# macOS
# htpasswd should be pre-installed with Apache
```

### "401 Unauthorized" error

1. Check `.htpasswd` file exists:
   ```bash
   ls -la nginx/.htpasswd
   ```

2. Verify nginx can read the file:
   ```bash
   docker-compose exec nginx cat /etc/nginx/.htpasswd
   ```

3. Check credentials are correct:
   ```bash
   cat nginx/.htpasswd
   ```

4. Restart nginx:
   ```bash
   make docker-restart
   ```

### ".htpasswd file not found" in nginx logs

Ensure the file is mounted correctly in docker-compose.yml:

```yaml
volumes:
  - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
```

Then restart:
```bash
docker-compose down && docker-compose up -d
```

### Changes not taking effect

1. Verify nginx configuration is valid:
   ```bash
   docker-compose exec nginx nginx -t
   ```

2. Reload nginx configuration:
   ```bash
   docker-compose exec nginx nginx -s reload
   ```

3. Or restart nginx completely:
   ```bash
   make docker-restart
   ```

## Nginx Configuration Details

The basic auth is configured in `conf.d/default.conf`:

```nginx
# Protected API Documentation endpoints
location ~ ^/api/(docs|redoc|openapi\.json) {
    auth_basic "API Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://backend:8900;
    # ... proxy headers ...
}
```

This uses a regex location block to match:
- `/api/docs` - Swagger UI
- `/api/redoc` - ReDoc documentation
- `/api/openapi.json` - OpenAPI schema

All other `/api/*` requests bypass basic auth and go directly to the backend.

## Disabling Basic Auth (Not Recommended)

If you want to completely disable basic auth (not recommended for production):

1. **Option 1**: Disable docs entirely in backend:
   ```bash
   # In .env file
   ENABLE_API_DOCS=false
   ```

2. **Option 2**: Remove auth from nginx (not recommended):
   Edit `nginx/conf.d/default.conf` and comment out:
   ```nginx
   # auth_basic "API Documentation";
   # auth_basic_user_file /etc/nginx/.htpasswd;
   ```

## Additional Resources

- [Nginx Basic Auth Documentation](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/)
- [htpasswd Documentation](https://httpd.apache.org/docs/current/programs/htpasswd.html)
- [Bcrypt Password Hashing](https://en.wikipedia.org/wiki/Bcrypt)
