# Coolify Deployment Guide

## Prerequisites

- Coolify installed and running
- Telegram API credentials obtained from https://my.telegram.org
- GitHub repository with the code (optional, can deploy from local)

## Step 1: Initialize Session Locally

Before deploying, authenticate with Telegram:

```bash
# In the project directory
export TELEGRAM_API_ID="your_api_id"
export TELEGRAM_API_HASH="your_api_hash"

# Run initialization
python initialize_session.py

# This creates: data/telegram_session.session
```

## Step 2: Configure Coolify Resource

### Create New Application

1. Go to Coolify dashboard
2. Create a new resource
3. Choose "Application" or "Docker"

### Configure Environment Variables

Add these environment variables:

```
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
ALLOWED_IPS=cloudflare_worker_ip_or_empty
```

**ALLOWED_IPS** - Comma-separated list of IPs that can access the API
- Leave empty to disable filtering (not recommended for production)
- Add Cloudflare Worker IPs for security
- Example: `ALLOWED_IPS=1.2.3.4,5.6.7.8`

###
Expose ports

```
Ports exposes: 8000
Ports mapping: 9000:8000
```

### Configure Volumes

Mount a volume for persistent session storage:

```
Host Path: /data/telegram
Container Path: /app/data
```

This ensures the Telegram session persists across container restarts.

### Configure Port

```
Host Port: 8000
Container Port: 8000
```

Or use Coolify's automatic port assignment.

### Configure Health Check

```
Endpoint: /health
Interval: 30s
Timeout: 10s
Retries: 3
```

### Configure Restart Policy

Set to: `always`

## Step 3: Deploy

### Option A: Deploy from GitHub

1. Connect your GitHub repository in Coolify
2. Set build directory: `telegram-parser-service` (if using monorepo)
3. Dockerfile path: `Telegram parser/Dockerfile`
4. Click "Deploy"

### Option B: Deploy from Local Build

```bash
# On your local machine
cd "/Users/ivanabramov/Desktop/Telegram parser"
docker build -t telegram-parser .
docker push your-registry/telegram-parser
```

Then deploy using the pushed image in Coolify.

## Step 4: Upload Session File

After first deployment, upload the session file:

```bash
# Create data directory on server
ssh user@your-server "mkdir -p /data/telegram-parser"

# Upload session file
scp data/telegram_session.session user@your-server:/data/telegram-parser/telegram_session.session
```

Or use Coolify's file manager in the resource settings.

## Step 5: Verify Deployment

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test parse endpoint
curl "https://your-domain.com/parse/telegram/single?url=https://t.me/ivan_talknow/99"
```

## Update Configuration

To update environment variables or other settings:

1. Go to resource settings in Coolify
2. Edit environment variables or volumes
3. Click "Redeploy" or "Update"

## Monitoring

Check logs in Coolify dashboard:

- Application logs show all requests
- Health check status in Coolify dashboard
- Errors are logged with full stack traces

## Troubleshooting

### Service won't start

- Check environment variables are set correctly
- Verify session file exists in `/app/data/telegram_session.session`
- Check logs for authentication errors

### "Session required" errors

- Upload session file to server: `/data/telegram-parser/telegram_session.session`
- Ensure volume mount points to correct path

### Rate limiting errors

- Wait for cooldown period
- Consider implementing caching in the Worker layer
- Reduce request frequency

## Security Recommendations

1. **Use IP allowlist** - Set `ALLOWED_IPS` to only allow Cloudflare Worker IPs
2. **Use HTTPS** - Configure SSL/TLS in Coolify
3. **Rotate credentials** - If session compromised, create new session
4. **Monitor access** - Watch logs for unauthorized access attempts
5. **Session file permissions** - Ensure only Docker user can read session file

## Next Steps

After successful deployment:

1. Configure Cloudflare Worker to call this service
2. Set up monitoring and alerts
3. Implement rate limiting if needed
4. Consider caching layer for frequently accessed posts

