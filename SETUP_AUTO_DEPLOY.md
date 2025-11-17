# Setup Automatic Vercel Deployment

Since I can't authenticate to your Vercel account directly, here are 3 easy options to get auto-deployment working:

## Option 1: Merge PR (Easiest if Vercel is connected)

If your repository is already connected to Vercel:

1. **Merge the pull request** on GitHub
2. Vercel will automatically deploy when code is pushed to `main`

**Check if connected**: Go to your Vercel dashboard → check if this repo is listed

---

## Option 2: GitHub Actions (Fully Automated)

I've created GitHub Actions workflow for automatic deployment!

### Setup Steps (5 minutes):

1. **Get Vercel Token**
   ```bash
   # Visit: https://vercel.com/account/tokens
   # Create new token → Copy it
   ```

2. **Get Project IDs**
   ```bash
   cd frontend
   vercel link
   # Follow prompts to link project

   # Get your IDs
   cat .vercel/project.json
   ```

3. **Add GitHub Secrets**
   - Go to: https://github.com/ehudso7/OmniAudit/settings/secrets/actions
   - Add these secrets:
     - `VERCEL_TOKEN` = (from step 1)
     - `VERCEL_ORG_ID` = (from .vercel/project.json)
     - `VERCEL_PROJECT_ID` = (from .vercel/project.json)
     - `VITE_API_URL` = https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app

4. **Push changes** → GitHub Actions will auto-deploy!

---

## Option 3: Manual Deploy (Fastest - 2 minutes)

Run these commands:

```bash
cd frontend
vercel --prod
```

When prompted:
- **Set up and deploy?** Yes
- **Link to existing project?** No
- **Project name:** omniaudit-frontend
- **Directory:** `./`
- **Build command:** `npm run build`
- **Output directory:** `dist`

✅ Done! You'll get a live URL.

---

## After Deployment

Once deployed, you need to update CORS:

```bash
# Get your frontend URL (e.g., https://omniaudit-frontend-xxx.vercel.app)

# Update API CORS
vercel env add CORS_ORIGINS production
# Enter: https://your-frontend-url.vercel.app,http://localhost:3000

# Redeploy API
vercel --prod
```

---

## Verification

After deployment:

1. **Frontend**: Open `https://your-frontend-url.vercel.app`
   - Should see dashboard
   - Should show "✓ API Healthy" badge

2. **Backend**: Check `https://omni-audit-c1oeztkup-everton-hudsons-projects.vercel.app/health`
   - Should return `{"status": "healthy"}`

---

## Current Status

✅ All code is ready and pushed to GitHub
✅ Security fixes applied
✅ Tests passing
✅ GitHub Actions workflow configured
⏳ Awaiting deployment trigger (choose option above)

---

## Need Help?

If you run into issues:
1. Check Vercel dashboard for deployment logs
2. Verify GitHub secrets are set correctly
3. Check that `.github/workflows/deploy-frontend.yml` exists
4. Review `DEPLOY_NOW.md` for detailed troubleshooting

**Quick help commands:**
```bash
vercel --help
vercel list
vercel logs
```
