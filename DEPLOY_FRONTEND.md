# OmniAudit Frontend Deployment

Quick deployment guide for the React dashboard.

## Option 1: Deploy to Vercel (Recommended)

### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

### Step 2: Deploy from frontend directory
```bash
cd frontend
vercel
```

Follow the prompts:
- **Set up and deploy:** Yes
- **Which scope:** Select your account
- **Link to existing project:** No
- **Project name:** omniaudit-frontend (or your choice)
- **Directory:** `./` (current directory)
- **Build command:** `npm run build`
- **Output directory:** `dist`

### Step 3: Set environment variable
```bash
vercel env add VITE_API_URL production
# Enter: https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app
```

### Step 4: Redeploy
```bash
vercel --prod
```

## Option 2: Deploy to Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Navigate to frontend
cd frontend

# Build
npm run build

# Deploy
netlify deploy --prod --dir=dist

# Set environment variable in Netlify dashboard
# VITE_API_URL = https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app
```

## Option 3: Quick Local Test

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

## After Deployment

Your frontend will be at a URL like:
- Vercel: `https://omniaudit-frontend.vercel.app`
- Netlify: `https://omniaudit-frontend.netlify.app`

**Don't forget to:**
1. Update CORS settings in your API to allow the frontend domain
2. Set `CORS_ORIGINS` environment variable in the API deployment

Example:
```bash
# In your API Vercel project
vercel env add CORS_ORIGINS production
# Enter: https://omniaudit-frontend.vercel.app
```

## Troubleshooting

### CORS Errors
If you see CORS errors, add your frontend URL to the API's CORS_ORIGINS:
```bash
# In the API deployment
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

### API Not Found
Make sure VITE_API_URL points to your deployed API:
```bash
# Should be
VITE_API_URL=https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app

# NOT
VITE_API_URL=http://localhost:8000
```
