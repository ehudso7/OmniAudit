# GitHub Actions Workflows

## Automatic Vercel Deployment Setup

To enable automatic deployments, add these secrets to your GitHub repository:

### Required Secrets

1. **VERCEL_TOKEN**
   - Get from: https://vercel.com/account/tokens
   - Create a new token with appropriate permissions

2. **VERCEL_ORG_ID**
   - Find in: Project Settings → General → Project ID section
   - Or run: `vercel link` in your project directory

3. **VERCEL_PROJECT_ID**
   - Find in: Project Settings → General
   - Or from `.vercel/project.json` after running `vercel link`

4. **VITE_API_URL** (Optional)
   - Your backend API URL
   - Default: https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app

### How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its corresponding value

### Getting Vercel IDs

```bash
# Install Vercel CLI
npm i -g vercel

# Link your project
cd frontend
vercel link

# This creates .vercel/project.json with your IDs
cat .vercel/project.json
```

### How It Works

- **On PR**: Creates preview deployment
- **On push to main**: Deploys to production
- **On push to feature branch**: Creates preview deployment

### Manual Deployment (No GitHub Actions)

If you prefer manual deployment:

```bash
cd frontend
vercel --prod
```
