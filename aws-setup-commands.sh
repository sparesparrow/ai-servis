#!/bin/bash

# AWS Setup Commands for ai.sparetools.dev
# Run these commands to set up the infrastructure

echo "🚀 Setting up AWS infrastructure for ai.sparetools.dev"

# 1. Create S3 bucket
echo "📦 Creating S3 bucket..."
aws s3 mb s3://ai-sparetools-web --region eu-north-1

# 2. Set bucket policy for CloudFront access
echo "🔐 Setting bucket policy..."
aws s3api put-bucket-policy --bucket ai-sparetools-web --policy file://bucket-policy.json

# 3. Enable static website hosting
echo "🌐 Enabling static website hosting..."
aws s3 website s3://ai-sparetools-web --index-document index.html --error-document error.html

# 4. Request ACM certificate (DŮLEŽITÉ: v us-east-1 pro CloudFront!)
echo "🔒 Requesting ACM certificate..."
aws acm request-certificate \
  --domain-name ai.sparetools.dev \
  --validation-method DNS \
  --region us-east-1

echo "✅ AWS setup complete!"
echo "📋 Next steps:"
echo "1. Validate DNS records in ACM console"
echo "2. Create CloudFront distribution"
echo "3. Add DNS record: ai.sparetools.dev -> ALIAS -> <cloudfront-domain>.cloudfront.net"
