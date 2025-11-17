#!/bin/bash
# OmniAudit Complete Deployment Script

set -e  # Exit on error

echo "🚀 OmniAudit Deployment Script"
echo "================================"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "✅ Vercel CLI is installed"
echo ""

# Deploy Frontend
echo "📦 Deploying Frontend Dashboard..."
echo "-----------------------------------"
cd frontend

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build
echo "Building frontend..."
npm run build

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel --prod

cd ..

echo ""
echo "✅ Frontend Deployment Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Copy your frontend URL from the output above"
echo "2. Set CORS_ORIGINS in your API deployment:"
echo "   vercel env add CORS_ORIGINS production"
echo "   (Enter your frontend URL when prompted)"
echo ""
echo "3. Set optional environment variables for webhooks:"
echo "   vercel env add GITHUB_WEBHOOK_SECRET production"
echo "   vercel env add SLACK_VERIFICATION_TOKEN production"
echo ""
echo "🎉 Your OmniAudit platform is now live!"
