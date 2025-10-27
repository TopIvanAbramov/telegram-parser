# Telegram Parser API Service

A FastAPI service for parsing Telegram channel posts to extract views and reactions statistics.

## Features

- ✅ Parse views count from Telegram posts
- ✅ Extract reactions breakdown by emoji type
- ✅ FastAPI async endpoint
- ✅ Docker containerization
- ✅ IP allowlist security
- ✅ Persistent Telegram session (authenticate once)
- ✅ Graceful error handling

## Quick Start

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Navigate to "API Development Tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

### 2. Initialize Telegram Session

Before deploying, you need to authenticate once:

```bash
# Set credentials
export TELEGRAM_API_ID="your_api_id"
export TELEGRAM_API_HASH="your_api_hash"

# Run initialization
python initialize_session.py
```

This will:
- Prompt for your phone number
- Ask for verification code (sent to Telegram)
- Create `data/telegram_session.session` file

### 3. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_API_ID="your_api_id"
export TELEGRAM_API_HASH="your_api_hash"
export ALLOWED_IPS=""  # Empty = allow all

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Docker Development

```bash
# Copy .env.example to .env and edit
cp .env.example .env

# Edit .env with your credentials

# Build and run
docker-compose up --build

# Service runs on http://localhost:8000
```

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "service": "telegram-parser"
}
```

### Parse Telegram Post

```bash
GET /parse/telegram/single?url=https://t.me/ivan_talknow/99
```

**Success Response:**
```json
{
  "success": true,
  "channel": "ivan_talknow",
  "message_id": 99,
  "views": 1234,
  "reactions": {
    "👍": 45,
    "❤️": 23,
    "🔥": 12
  },
  "total_reactions": 80,
  "message_date": "2024-01-15T10:30:00+00:00",
  "has_reactions": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Post not found",
  "error_code": "POST_NOT_FOUND"
}
```

## Error Codes

- `INVALID_URL` - Invalid Telegram URL format
- `POST_NOT_FOUND` - Post doesn't exist or was deleted
- `CHANNEL_PRIVATE` - Channel is private or requires membership
- `TELEGRAM_RATE_LIMIT` - Rate limited by Telegram
- `CHANNEL_BLOCKED` - Channel has blocked the account
- `FORBIDDEN` - IP not in allowlist
- `INTERNAL_ERROR` - Unexpected error

## Deploy to Coolify

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Telegram Parser API"
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2: Configure Coolify

1. **Create New Resource** in Coolify
2. **Environment Variables:**
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ALLOWED_IPS=cloudflare_worker_ip
   ```
3. **Volume Mount:**
   - Host path: `/data/telegram-parser`
   - Container path: `/app/data`
4. **Port Mapping:**
   - Host: `8000`
   - Container: `8000`
5. **Health Check:**
   - Endpoint: `/health`
   - Interval: `30s`
6. **Restart Policy:** `always`

### Step 3: Upload Session File

Before first deployment, upload the session file:

```bash
# Copy session to server
scp data/telegram_session.session user@your-server:/data/telegram-parser/
```

Or use Coolify's file manager to upload directly.

### Step 4: Deploy

Deploy from GitHub in Coolify dashboard.

## Cloudflare Worker Integration

Create a Worker to call this service:

```typescript
// Worker code
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);
    const telegramUrl = url.searchParams.get('url');
    
    const response = await fetch(`${env.TELEGRAM_PARSER_API_URL}/parse/telegram/single?url=${telegramUrl}`);
    return response;
  }
}
```

**Worker Environment Variable:**
```
TELEGRAM_PARSER_API_URL=https://your-vds-domain.com
```

## Security

### IP Allowlist

Set `ALLOWED_IPS` environment variable to restrict access:

```bash
ALLOWED_IPS=127.0.0.1,192.168.1.1
```

Leave empty to allow all IPs (not recommended for production).

### Session File Security

The `telegram_session.session` file grants access to your Telegram account:

- ✅ Keep it secure
- ✅ Don't commit to git
- ✅ Store on server with proper permissions
- ✅ If compromised, revoke in Telegram settings

## Troubleshooting

### "Session Required"

Create session file by running `initialize_session.py`.

### "Rate Limited"

Wait for the specified time. Telethon handles rate limits automatically.

### "Channel is private"

The API account must be a member of the channel. Add the account to the channel first.

### "Post not found"

- Verify the post ID is correct
- Ensure the channel is public
- Check that the post hasn't been deleted

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test parse endpoint
curl "http://localhost:8000/parse/telegram/single?url=https://t.me/ivan_talknow/99"
```

## Architecture

```
Cloudflare Worker
    ↓ (HTTP)
FastAPI Service (Docker)
    ↓ (Telethon)
Telegram API
```

## License

MIT
