#!/bin/bash
# S3 Bucket Setup for HelpPetAI Visit Recordings

# Set variables
BUCKET_NAME="helppetai-visit-recordings"
REGION="us-west-1"
IAM_USER="helppetai-upload-user"
TEMP_DIR="/tmp/s3-setup-$$"

# Create temp directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "🪣 Creating S3 bucket: $BUCKET_NAME in $REGION"
aws s3 mb s3://$BUCKET_NAME --region $REGION

echo "🔒 Setting up bucket versioning"
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

echo "🚫 Blocking public access"
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "👤 Creating IAM user: $IAM_USER"
aws iam create-user --user-name $IAM_USER

echo "🔑 Creating access key"
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name $IAM_USER)
ACCESS_KEY_ID=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.AccessKeyId')
SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.SecretAccessKey')

echo "📝 Creating bucket policy"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cat > bucket-policy.json << POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVisitRecordingUploads",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::$ACCOUNT_ID:user/$IAM_USER"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    },
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::$ACCOUNT_ID:user/$IAM_USER"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::$BUCKET_NAME"
    }
  ]
}
POLICY

echo "🛡️ Applying bucket policy"
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

echo "🏷️ Adding bucket tags"
aws s3api put-bucket-tagging \
  --bucket $BUCKET_NAME \
  --tagging 'TagSet=[
    {Key=Project,Value=HelpPetAI},
    {Key=Purpose,Value=VisitRecordings},
    {Key=Environment,Value=Production}
  ]'

echo "🔄 Setting up lifecycle policy for cleanup"
cat > lifecycle-policy.json << LIFECYCLE
{
  "Rules": [
    {
      "ID": "DeleteOldRecordings",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "visit-recordings/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}
LIFECYCLE

aws s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET_NAME \
  --lifecycle-configuration file://lifecycle-policy.json

echo "✅ S3 bucket setup complete!"
echo ""
echo "🔑 SAVE THESE CREDENTIALS:"
echo "================================"
echo "Access Key ID: $ACCESS_KEY_ID"
echo "Secret Access Key: $SECRET_ACCESS_KEY"
echo "================================"
echo ""
echo "📋 Add to your backend .env file:"
echo "S3_BUCKET_NAME=$BUCKET_NAME"
echo "S3_REGION=$REGION"
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY"
echo ""
echo "3. Test the setup:"
echo "   aws s3 ls s3://$BUCKET_NAME"
echo ""

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo "🗑️ Temporary files cleaned up"
