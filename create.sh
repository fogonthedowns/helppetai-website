#!/bin/bash
set -e

# Configuration
DOMAIN="helppet.ai"
BUCKET_NAME="helppet.ai"
REGION="us-west-1"
CERT_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up AWS infrastructure for ${DOMAIN}${NC}"

# Step 1: Check S3 Bucket (skip creation if exists)
echo -e "${YELLOW}📦 Checking S3 bucket...${NC}"
if aws s3api head-bucket --bucket ${BUCKET_NAME} 2>/dev/null; then
    echo -e "${GREEN}✅ Bucket ${BUCKET_NAME} already exists${NC}"
else
    echo -e "${YELLOW}Creating S3 bucket...${NC}"
    aws s3 mb s3://${BUCKET_NAME} --region ${REGION}
fi

# Step 2: Enable static website hosting
echo -e "${YELLOW}🌐 Enabling static website hosting...${NC}"
aws s3 website s3://${BUCKET_NAME} --index-document index.html --error-document index.html

# Step 3: Create bucket policy
echo -e "${YELLOW}🔒 Creating bucket policy...${NC}"
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

# Apply bucket policy
aws s3api put-bucket-policy --bucket ${BUCKET_NAME} --policy file://bucket-policy.json

# Step 4: Request SSL Certificate
echo -e "${YELLOW}🔐 Requesting SSL certificate...${NC}"
CERT_ARN=$(aws acm request-certificate \
    --domain-name ${DOMAIN} \
    --subject-alternative-names "*.${DOMAIN}" \
    --validation-method DNS \
    --region ${CERT_REGION} \
    --output text --query 'CertificateArn')

echo -e "${GREEN}Certificate ARN: ${CERT_ARN}${NC}"

# Step 5: Get certificate validation records
echo -e "${YELLOW}📋 Getting certificate validation records...${NC}"
echo -e "${RED}IMPORTANT: You need to add these DNS records to validate your certificate:${NC}"

# Wait a moment for the certificate request to be processed
sleep 10

aws acm describe-certificate \
    --certificate-arn ${CERT_ARN} \
    --region ${CERT_REGION} \
    --query 'Certificate.DomainValidationOptions[].ResourceRecord' \
    --output table

echo -e "${RED}Please add these CNAME records to your DNS and press Enter when done...${NC}"
read -p "Press Enter to continue..."

# Step 6: Wait for certificate validation
echo -e "${YELLOW}⏳ Waiting for certificate validation...${NC}"
aws acm wait certificate-validated \
    --certificate-arn ${CERT_ARN} \
    --region ${CERT_REGION}

echo -e "${GREEN}✅ Certificate validated!${NC}"

# Step 7: Create CloudFront Origin Access Control
echo -e "${YELLOW}🔑 Creating Origin Access Control...${NC}"
OAC_ID=$(aws cloudfront create-origin-access-control \
    --origin-access-control-config '{
        "Name": "'${DOMAIN}'-OAC",
        "Description": "OAC for '${DOMAIN}'",
        "OriginAccessControlOriginType": "s3",
        "SigningBehavior": "always",
        "SigningProtocol": "sigv4"
    }' \
    --output text --query 'OriginAccessControl.Id')

echo -e "${GREEN}OAC ID: ${OAC_ID}${NC}"

# Step 8: Create CloudFront distribution
echo -e "${YELLOW}☁️ Creating CloudFront distribution...${NC}"
cat > distribution-config.json << EOF
{
    "CallerReference": "${DOMAIN}-$(date +%s)",
    "Comment": "${DOMAIN} CDN",
    "DefaultCacheBehavior": {
        "TargetOriginId": "${DOMAIN}-s3-origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "${DOMAIN}-s3-origin",
                "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                },
                "OriginAccessControlId": "${OAC_ID}"
            }
        ]
    },
    "Enabled": true,
    "Aliases": {
        "Quantity": 1,
        "Items": ["${DOMAIN}"]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": "${CERT_ARN}",
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "DefaultRootObject": "index.html",
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 403,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    }
}
EOF

DISTRIBUTION_OUTPUT=$(aws cloudfront create-distribution --distribution-config file://distribution-config.json)
DISTRIBUTION_ID=$(echo ${DISTRIBUTION_OUTPUT} | jq -r '.Distribution.Id')
CLOUDFRONT_DOMAIN=$(echo ${DISTRIBUTION_OUTPUT} | jq -r '.Distribution.DomainName')

echo -e "${GREEN}Distribution ID: ${DISTRIBUTION_ID}${NC}"
echo -e "${GREEN}CloudFront Domain: ${CLOUDFRONT_DOMAIN}${NC}"

# Step 9: Update bucket policy with distribution ARN
echo -e "${YELLOW}🔄 Updating bucket policy with distribution ARN...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

cat > bucket-policy-final.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DISTRIBUTION_ID}"
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket ${BUCKET_NAME} --policy file://bucket-policy-final.json

# Step 10: Create/Update Route53 hosted zone and records
echo -e "${YELLOW}🌍 Setting up Route53...${NC}"

# Check if hosted zone exists
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name ${DOMAIN} --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text | sed 's|/hostedzone/||')

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo -e "${YELLOW}Creating hosted zone for ${DOMAIN}...${NC}"
    HOSTED_ZONE_OUTPUT=$(aws route53 create-hosted-zone --name ${DOMAIN} --caller-reference $(date +%s))
    HOSTED_ZONE_ID=$(echo ${HOSTED_ZONE_OUTPUT} | jq -r '.HostedZone.Id' | sed 's|/hostedzone/||')
    
    echo -e "${GREEN}Created hosted zone: ${HOSTED_ZONE_ID}${NC}"
    echo -e "${RED}IMPORTANT: Update your domain nameservers to:${NC}"
    echo ${HOSTED_ZONE_OUTPUT} | jq -r '.DelegationSet.NameServers[]'
else
    echo -e "${GREEN}Using existing hosted zone: ${HOSTED_ZONE_ID}${NC}"
fi

# Create A record for domain
echo -e "${YELLOW}📝 Creating DNS A record...${NC}"
cat > dns-record.json << EOF
{
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "${DOMAIN}",
            "Type": "A",
            "AliasTarget": {
                "DNSName": "${CLOUDFRONT_DOMAIN}",
                "EvaluateTargetHealth": false,
                "HostedZoneId": "Z2FDTNDATAQYW2"
            }
        }
    }]
}
EOF

aws route53 change-resource-record-sets \
    --hosted-zone-id ${HOSTED_ZONE_ID} \
    --change-batch file://dns-record.json

# Step 11: Create deployment script
echo -e "${YELLOW}📝 Creating deployment script...${NC}"
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

BUCKET_NAME="helppet.ai"
DISTRIBUTION_ID="REPLACE_WITH_DISTRIBUTION_ID"

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
EOF

# Update deploy.sh with actual distribution ID
sed -i.bak "s/REPLACE_WITH_DISTRIBUTION_ID/${DISTRIBUTION_ID}/g" deploy.sh
rm deploy.sh.bak
chmod +x deploy.sh

# Cleanup temporary files
rm -f bucket-policy.json distribution-config.json bucket-policy-final.json dns-record.json

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}Summary:${NC}"
echo -e "  S3 Bucket: ${BUCKET_NAME}"
echo -e "  CloudFront Distribution: ${DISTRIBUTION_ID}"
echo -e "  CloudFront Domain: ${CLOUDFRONT_DOMAIN}"
echo -e "  Route53 Hosted Zone: ${HOSTED_ZONE_ID}"
echo -e "  Certificate: ${CERT_ARN}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Wait for CloudFront distribution to deploy (15-20 minutes)"
echo -e "  2. Test your site: https://${CLOUDFRONT_DOMAIN}"
echo -e "  3. Once working, test your custom domain: https://${DOMAIN}"
echo -e "  4. Deploy your app: ./deploy.sh"
echo ""
echo -e "${GREEN}Your infrastructure is ready! 🚀${NC}"