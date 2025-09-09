#!/bin/bash

# HelpPet AI - Serverless Transcription Service Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
STACK_NAME="helppet-transcription-service"
REGION="us-west-1"
S3_BUCKET="helppetai-visit-recordings"
WEBHOOK_URL="https://api.helppet.ai/api/v1/webhook/transcription/complete/by-s3-key"
WEBHOOK_SECRET="HelpPetWebhook2024!"

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    print_error "ANTHROPIC_API_KEY environment variable is required"
    exit 1
fi

if [ -z "$API_TOKEN" ]; then
    print_error "API_TOKEN environment variable is required"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if AWS CLI is configured
print_step "Checking AWS CLI configuration..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS CLI is not configured or credentials are invalid"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
print_success "AWS Account: $AWS_ACCOUNT"

# Check if S3 bucket exists
print_step "Checking if S3 bucket exists..."
if aws s3api head-bucket --bucket "$S3_BUCKET" --region "$REGION" > /dev/null 2>&1; then
    print_success "S3 bucket $S3_BUCKET exists"
else
    print_error "S3 bucket $S3_BUCKET does not exist or is not accessible"
    exit 1
fi

# Create deployment package for Lambda functions
print_step "Creating deployment packages..."

# Create temp directory for packaging
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Package audio processor
cp "$SCRIPT_DIR/lambda/src/audio_processor.py" .
zip audio_processor.zip audio_processor.py

# Package transcription complete handler
cp "$SCRIPT_DIR/lambda/src/transcription_complete_handler.py" .
zip transcription_complete.zip transcription_complete_handler.py

# Package transcript processor with dependencies
print_step "Installing transcript processor dependencies..."
if command -v docker >/dev/null 2>&1; then
    print_step "Using Docker for Linux-compatible dependency build..."
    # Use official AWS Lambda Python image that matches the runtime
    docker run --rm --platform linux/amd64 --entrypoint="" -v "$SCRIPT_DIR/lambda/src:/var/task" public.ecr.aws/lambda/python:3.9 bash -c "
        yum install -y zip && 
        cd /var/task && 
        pip install -r requirements.txt -t /tmp/lambda-package && 
        cp transcript_processor.py /tmp/lambda-package/ && 
        cd /tmp/lambda-package && 
        zip -r /var/task/transcript_processor.zip .
    "
    mv "$SCRIPT_DIR/lambda/src/transcript_processor.zip" .
else
    print_warning "Docker not available, falling back to local pip install"
    mkdir transcript_processor_pkg
    cd transcript_processor_pkg
    cp "$SCRIPT_DIR/lambda/src/transcript_processor.py" .
    cp "$SCRIPT_DIR/lambda/src/requirements.txt" .
    pip install -r requirements.txt -t .
    zip -r ../transcript_processor.zip .
    cd ..
    rm -rf transcript_processor_pkg
fi

print_success "Lambda packages created"

# Create S3 bucket for Lambda code (if doesn't exist)
LAMBDA_BUCKET="helppet-lambda-deployments-$AWS_ACCOUNT-$REGION"
if ! aws s3api head-bucket --bucket "$LAMBDA_BUCKET" --region "$REGION" > /dev/null 2>&1; then
    print_step "Creating S3 bucket for Lambda code..."
    aws s3 mb "s3://$LAMBDA_BUCKET" --region "$REGION"
    print_success "Created bucket $LAMBDA_BUCKET"
fi

# Upload Lambda packages
print_step "Uploading Lambda packages to S3..."
aws s3 cp audio_processor.zip "s3://$LAMBDA_BUCKET/audio_processor.zip"
aws s3 cp transcription_complete.zip "s3://$LAMBDA_BUCKET/transcription_complete.zip"
aws s3 cp transcript_processor.zip "s3://$LAMBDA_BUCKET/transcript_processor.zip"
print_success "Lambda packages uploaded"

# Deploy CloudFormation stack
print_step "Deploying CloudFormation stack..."

aws cloudformation deploy \
    --template-file "$SCRIPT_DIR/lambda/infrastructure/transcription_stack.yaml" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --parameter-overrides \
        ExistingBucketName="$S3_BUCKET" \
        WebhookEndpointUrl="$WEBHOOK_URL" \
        WebhookSecretToken="$WEBHOOK_SECRET" \
        AnthropicApiKey="$ANTHROPIC_API_KEY" \
        ApiToken="$API_TOKEN" \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

print_success "CloudFormation stack deployed"

# Get function ARNs from stack outputs
print_step "Getting Lambda function ARNs..."
AUDIO_PROCESSOR_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='AudioProcessorFunctionArn'].OutputValue" \
    --output text)

TRANSCRIPTION_COMPLETE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='TranscriptionCompleteFunctionArn'].OutputValue" \
    --output text)

TRANSCRIPT_PROCESSOR_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='TranscriptProcessorFunctionArn'].OutputValue" \
    --output text)

print_success "Audio Processor ARN: $AUDIO_PROCESSOR_ARN"
print_success "Transcription Complete ARN: $TRANSCRIPTION_COMPLETE_ARN"
print_success "Transcript Processor ARN: $TRANSCRIPT_PROCESSOR_ARN"

# Update Lambda function code
print_step "Updating Lambda function code..."

aws lambda update-function-code \
    --function-name "$AUDIO_PROCESSOR_ARN" \
    --s3-bucket "$LAMBDA_BUCKET" \
    --s3-key "audio_processor.zip" \
    --region "$REGION" > /dev/null

aws lambda update-function-code \
    --function-name "$TRANSCRIPTION_COMPLETE_ARN" \
    --s3-bucket "$LAMBDA_BUCKET" \
    --s3-key "transcription_complete.zip" \
    --region "$REGION" > /dev/null

aws lambda update-function-code \
    --function-name "$TRANSCRIPT_PROCESSOR_ARN" \
    --s3-bucket "$LAMBDA_BUCKET" \
    --s3-key "transcript_processor.zip" \
    --region "$REGION" > /dev/null

print_success "Lambda function code updated"

# Clean up temp directory
cd - > /dev/null
rm -rf "$TEMP_DIR"

# Test webhook endpoint
print_step "Testing webhook endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL" | grep -q "405\|404\|200"; then
    print_success "Webhook endpoint is accessible"
else
    print_warning "Webhook endpoint may not be accessible - check your backend deployment"
fi

print_success "Deployment completed successfully!"
echo ""
echo "Configuration Summary:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo "  S3 Bucket: $S3_BUCKET"
echo "  Webhook URL: $WEBHOOK_URL"
echo "  Audio Processor: $AUDIO_PROCESSOR_ARN"
echo "  Transcription Handler: $TRANSCRIPTION_COMPLETE_ARN"
echo "  Transcript Processor: $TRANSCRIPT_PROCESSOR_ARN"
echo ""
echo "Next steps:"
echo "1. Upload an audio file (.m4a or .mp3) to s3://$S3_BUCKET/visit-recordings/"
echo "2. Wait for transcription to complete (creates file in s3://$S3_BUCKET/transcripts/)"
echo "3. The transcript processor will automatically extract SOAP data and update the visit"
echo "4. Check CloudWatch logs for all Lambda functions"
echo ""
print_success "Ready to process audio files!"