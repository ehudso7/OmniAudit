# 🚀 Deploy OmniAudit Now - Complete Guide

Everything is ready! Follow these simple steps to get your platform live.

## Prerequisites (One-Time Setup)

```bash
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Login to Vercel (opens browser)
vercel login
```

## Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- ✅ Install frontend dependencies
- ✅ Build the frontend
- ✅ Deploy to Vercel production

## Option 2: Manual Deployment

### Step 1: Deploy Frontend

```bash
cd frontend
npm install
npm run build
vercel --prod
```

**Save the frontend URL** you get (e.g., `https://omniaudit-frontend-xxx.vercel.app`)

### Step 2: Update API CORS Settings

```bash
# Go back to root
cd ..

# Add your frontend URL to API CORS
vercel env add CORS_ORIGINS production
# When prompted, enter: https://your-frontend-url.vercel.app,http://localhost:3000

# Redeploy API with new settings
vercel --prod
```

### Step 3 (Optional): Configure Webhooks

```bash
# For GitHub webhooks
vercel env add GITHUB_WEBHOOK_SECRET production
# Enter a random secret string

# For Slack integration
vercel env add SLACK_VERIFICATION_TOKEN production
# Enter your Slack verification token

# Redeploy API
vercel --prod
```

## What You'll Get

After deployment, you'll have:

1. **Backend API**: `https://omni-audit-xxx.vercel.app`
   - All API endpoints
   - Webhooks
   - Batch operations
   - Export functionality

2. **Frontend Dashboard**: `https://omniaudit-frontend-xxx.vercel.app`
   - Visual dashboard
   - Run audits through UI
   - Export reports
   - View statistics

## Verify Deployment

### Test Backend API
```bash
curl https://your-api-url.vercel.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "..."
}
```

### Test Frontend
Open `https://your-frontend-url.vercel.app` in your browser

You should see:
- 🔍 OmniAudit Dashboard header
- ✓ API Healthy badge (green)
- Dashboard, Run Audit, Export tabs
- Available collectors list

## Environment Variables Reference

### Required for Production

| Variable | Purpose | Example |
|----------|---------|---------|
| `CORS_ORIGINS` | Frontend URL(s) | `https://frontend.vercel.app` |

### Optional

| Variable | Purpose | Example |
|----------|---------|---------|
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook auth | Any random string |
| `SLACK_VERIFICATION_TOKEN` | Slack integration | From Slack app config |
| `AI_FEATURES_ENABLED` | Enable AI features | `true` |
| `ANTHROPIC_API_KEY` | AI analysis | `sk-ant-...` |

## Troubleshooting

### Frontend shows "API Healthy" as yellow/unknown
- Check that `VITE_API_URL` in frontend/.env.production matches your API URL
- Redeploy frontend after fixing

### CORS errors in browser console
- Add your frontend URL to `CORS_ORIGINS` in API project
- Redeploy API

### Webhook returns 503
- Set `GITHUB_WEBHOOK_SECRET` environment variable
- Redeploy API

### API returns 500
- Check build logs in Vercel dashboard
- Verify all dependencies are installed
- Check function logs for errors

## Quick Reference

```bash
# Deploy frontend
cd frontend && vercel --prod

# Update API environment variable
vercel env add VARIABLE_NAME production

# Redeploy API
vercel --prod

# View logs
vercel logs

# List deployments
vercel list
```

## Need Help?

1. Check Vercel dashboard for deployment logs
2. Review `docs/API.md` for API documentation
3. Review `docs/QUICKSTART.md` for usage examples
4. Check GitHub issues

## Success Checklist

- [ ] Frontend deployed and accessible
- [ ] Backend API deployed and accessible
- [ ] API returns healthy status
- [ ] Frontend shows green "API Healthy" badge
- [ ] CORS configured correctly
- [ ] Can run audit from UI
- [ ] Can export reports
- [ ] Webhooks configured (if needed)

🎉 **You're all set! Your OmniAudit platform is live!**
