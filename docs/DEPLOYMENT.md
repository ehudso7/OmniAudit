# OmniAudit Deployment Guide

This guide covers deploying the OmniAudit backend API and connecting it to the Vercel-hosted frontend.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vercel        │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (FastAPI)     │     │   (Database)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

1. **Deploy with one click:**
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/omniaudit)

2. **Or deploy manually:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login and deploy
   railway login
   railway init
   railway up
   ```

3. **Set environment variables in Railway dashboard:**
   - `ANTHROPIC_API_KEY` - Your Anthropic API key for AI features
   - `DATABASE_URL` - Automatically set if using Railway PostgreSQL
   - `CORS_ORIGINS` - Your Vercel frontend URL

4. **Get your API URL** from Railway dashboard (e.g., `https://omniaudit-api.up.railway.app`)

### Option 2: Render.com

1. **Deploy using Blueprint:**
   - Fork this repository
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your forked repo
   - Render will auto-detect `render.yaml`

2. **Manual deploy:**
   - Click "New" → "Web Service"
   - Connect repository
   - Settings:
     - **Runtime:** Python 3
     - **Build Command:** `pip install -e .`
     - **Start Command:** `uvicorn omniaudit.api.main:app --host 0.0.0.0 --port $PORT`

3. **Set environment variables:**
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL` (from Render PostgreSQL)
   - `CORS_ORIGINS`

### Option 3: Fly.io

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Deploy:**
   ```bash
   cd /path/to/OmniAudit
   fly auth login
   fly launch  # First time only
   fly deploy
   ```

3. **Set secrets:**
   ```bash
   fly secrets set ANTHROPIC_API_KEY=your-key-here
   fly secrets set DATABASE_URL=your-database-url
   fly secrets set CORS_ORIGINS=https://your-frontend.vercel.app
   ```

### Option 4: Docker (Self-hosted)

1. **Build the image:**
   ```bash
   docker build -f python-app/Dockerfile -t omniaudit-api .
   ```

2. **Run locally:**
   ```bash
   docker run -p 8000:8000 \
     -e ANTHROPIC_API_KEY=your-key \
     -e DATABASE_URL=postgresql://... \
     -e CORS_ORIGINS=http://localhost:5173 \
     omniaudit-api
   ```

3. **Deploy to any container platform** (AWS ECS, Google Cloud Run, Azure Container Apps, etc.)

## Connecting Frontend to Backend

After deploying the backend, configure the frontend:

### For Vercel Deployment

1. Go to your Vercel project settings
2. Navigate to **Settings** → **Environment Variables**
3. Add:
   ```
   VITE_API_URL=https://your-backend-url.com
   ```
4. Redeploy the frontend

### For Local Development

Create `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8000
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for AI-powered code analysis |
| `DATABASE_URL` | No | PostgreSQL connection string (for persistence) |
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed frontend origins |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `PORT` | No | Server port (default: 8000) |

## Health Check

Verify your deployment is working:

```bash
curl https://your-backend-url.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T12:00:00Z",
  "version": "0.3.0"
}
```

## Troubleshooting

### CORS Errors
Ensure `CORS_ORIGINS` includes your frontend URL:
```
CORS_ORIGINS=https://omni-audit.vercel.app,https://your-custom-domain.com
```

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/database`
- Check if database allows external connections
- For Railway/Render, use their provided connection string

### AI Features Not Working
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API key has sufficient quota
- Review logs for specific error messages

## Scaling Considerations

### For Production
- Use a managed PostgreSQL database (Railway, Render, or dedicated like Supabase)
- Enable auto-scaling on your platform
- Set up monitoring and alerting
- Configure proper logging

### Recommended Resources
- **Minimum:** 512MB RAM, 0.5 vCPU
- **Recommended:** 1GB RAM, 1 vCPU
- **High traffic:** 2GB RAM, 2 vCPU with horizontal scaling
