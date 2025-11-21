#!/bin/bash

# OmniAudit Cloudflare Workers Deployment Script

set -e

echo "🚀 Deploying OmniAudit to Cloudflare Workers..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Check if logged in
if ! wrangler whoami &> /dev/null; then
    echo "Please login to Cloudflare..."
    wrangler login
fi

# Build the project
echo "📦 Building project..."
bun run build

# Set secrets (if not already set)
echo "🔐 Setting up secrets..."

if [ -f .env ]; then
    source .env

    echo "Setting ANTHROPIC_API_KEY..."
    echo "$ANTHROPIC_API_KEY" | wrangler secret put ANTHROPIC_API_KEY

    echo "Setting TURSO_URL..."
    echo "$TURSO_URL" | wrangler secret put TURSO_URL

    echo "Setting TURSO_TOKEN..."
    echo "$TURSO_TOKEN" | wrangler secret put TURSO_TOKEN

    echo "Setting UPSTASH_URL..."
    echo "$UPSTASH_URL" | wrangler secret put UPSTASH_URL

    echo "Setting UPSTASH_TOKEN..."
    echo "$UPSTASH_TOKEN" | wrangler secret put UPSTASH_TOKEN

    if [ -n "$PINECONE_API_KEY" ]; then
        echo "Setting PINECONE_API_KEY..."
        echo "$PINECONE_API_KEY" | wrangler secret put PINECONE_API_KEY
    fi

    if [ -n "$SENTRY_DSN" ]; then
        echo "Setting SENTRY_DSN..."
        echo "$SENTRY_DSN" | wrangler secret put SENTRY_DSN
    fi
fi

# Deploy to staging first
echo "📤 Deploying to staging..."
wrangler deploy --env staging

echo "✅ Staging deployment complete!"
echo "🔗 URL: https://omniaudit-api-staging.workers.dev"

# Ask for confirmation to deploy to production
read -p "Deploy to production? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Deploying to production..."
    wrangler deploy --env production
    echo "✅ Production deployment complete!"
    echo "🔗 URL: https://api.omniaudit.dev"
else
    echo "Production deployment skipped."
fi

echo "🎉 Deployment process complete!"
