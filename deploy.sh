#!/bin/bash
set -e

BUCKET_NAME="helppet.ai"
DISTRIBUTION_ID="E2VN7ITPTEP957"

echo "🚀 Deploying helppet.ai..."

# Build the application
echo "📦 Building application..."
yarn build

# Navigate to build directory
cd build

# Create route directories and copy index.html
echo "📁 Setting up SPA routing..."
mkdir -p vets about
cp index.html vets/index.html
cp index.html about/index.html

# Go back to project root
cd ..

# Sync to S3
echo "☁️ Uploading to S3..."
aws s3 sync ./build s3://${BUCKET_NAME} --delete

# Set cache headers
echo "⚡ Setting cache headers..."
aws s3 cp s3://${BUCKET_NAME} s3://${BUCKET_NAME} --recursive \
    --exclude "*" --include "*.html" \
    --metadata-directive REPLACE \
    --content-type "text/html" \
    --cache-control "no-cache"

aws s3 cp s3://${BUCKET_NAME} s3://${BUCKET_NAME} --recursive \
    --exclude "*" --include "*.css" \
    --metadata-directive REPLACE \
    --content-type "text/css" \
    --cache-control "public, max-age=31536000"

aws s3 cp s3://${BUCKET_NAME} s3://${BUCKET_NAME} --recursive \
    --exclude "*" --include "*.js" \
    --metadata-directive REPLACE \
    --content-type "application/javascript" \
    --cache-control "public, max-age=31536000"

# Invalidate CloudFront
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*"

echo "✅ Deployment complete!"
echo "🌐 Your site will be live at https://helppet.ai in a few minutes."
