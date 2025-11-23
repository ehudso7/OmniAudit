# Frontend Deployment Instructions

## Option 1: Deploy to Vercel (Recommended)

### Using Vercel CLI:
```bash
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Or deploy with the frontend config from root
cd /path/to/OmniAudit
vercel --prod --config vercel-frontend.json
```

### Using Vercel Dashboard:
1. Go to https://vercel.com/dashboard
2. Click "Add New Project"
3. Import your GitHub repository: `ehudso7/OmniAudit`
4. Configure deployment:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variable:
   - **Name:** `VITE_API_URL`
   - **Value:** Your Vercel API URL (e.g., `https://omni-audit.vercel.app`)
6. Click "Deploy"

## Option 2: Local Network Access

To access the frontend from other devices on your local network:

```bash
# Start dev server with host flag
cd frontend
npm run dev -- --host

# Then access from any device on your network:
# http://<your-local-ip>:3000
```

## Current Configuration

**Local Development:** http://localhost:3000
**API Endpoint (Production):** https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app

The frontend is currently running locally and configured to call the TypeScript API endpoints.
