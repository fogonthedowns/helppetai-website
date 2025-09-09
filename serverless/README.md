# HelpPet AI - Serverless Audio Transcription Service

This serverless component automatically transcribes audio files uploaded to S3 using AWS Transcribe and updates the HelpPet database via webhook.

## Architecture

```
S3 Upload (m4a/mp3) → Lambda (Audio Processor) → AWS Transcribe → EventBridge → Lambda (Completion Handler) → HelpPet API Webhook
```

## Components

### 1. Audio Processor Lambda (`lambda/src/audio_processor.py`)
- **Trigger**: S3 ObjectCreated events for .m4a and .mp3 files
- **Function**: Starts AWS Transcribe jobs
- **Configuration**: 
  - Speaker labels enabled (for vet + pet owner conversations)
  - Medical-optimized settings

### 2. Transcription Complete Handler (`lambda/src/transcription_complete_handler.py`)
- **Trigger**: EventBridge events when AWS Transcribe jobs complete/fail
- **Function**: Downloads transcription results and posts to HelpPet webhook
- **Security**: Uses X-Webhook-Token header for authentication

### 3. Webhook Endpoint (Backend: `backend/src/routes_pg/webhook.py`)
- **URL**: `https://api.helppet.ai/api/v1/webhook/transcription/complete/by-s3-key`
- **Function**: Receives transcription results and updates Visit records in PostgreSQL
- **Security**: Validates X-Webhook-Token header

## Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Existing S3 bucket: `helppetai-visit-recordings`
- HelpPet backend deployed with webhook endpoint

### Deploy the Stack

```bash
cd serverless
./deploy.sh
```

The deployment script will:
1. Package Lambda functions
2. Upload packages to S3
3. Deploy CloudFormation stack
4. Configure S3 bucket notifications
5. Update Lambda function code

### Manual Deployment

```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file lambda/infrastructure/transcription_stack.yaml \
  --stack-name helppet-transcription-service \
  --region us-west-1 \
  --parameter-overrides \
    ExistingBucketName=helppetai-visit-recordings \
    WebhookEndpointUrl=https://api.helppet.ai/api/v1/webhook/transcription/complete/by-s3-key \
    WebhookSecretToken=HelpPetWebhook2024 \
  --capabilities CAPABILITY_NAMED_IAM
```

## Configuration

### Environment Variables (Lambda)

**Audio Processor:**
- `TRANSCRIPTION_OUTPUT_BUCKET`: S3 bucket for transcription results

**Transcription Complete Handler:**
- `WEBHOOK_ENDPOINT_URL`: HelpPet API webhook URL
- `WEBHOOK_SECRET_TOKEN`: Authentication token for webhook

### Webhook Authentication

The webhook uses a simple secret token in the `X-Webhook-Token` header:
- **Default Token**: `HelpPetWebhook2024`
- **Backend Configuration**: Set `webhook_secret_token` in backend settings

## Data Flow

1. **File Upload**: Audio file (m4a/mp3) uploaded to S3 bucket `helppetai-visit-recordings`
2. **S3 Trigger**: S3 ObjectCreated event triggers Audio Processor Lambda
3. **Start Transcription**: Lambda starts AWS Transcribe job with:
   - Speaker labels for vet/owner identification
   - Medical-optimized settings
   - Tags with original file information
4. **Transcription Processing**: AWS Transcribe processes audio (typically 1-10 minutes)
5. **Completion Event**: EventBridge captures Transcribe job completion
6. **Result Processing**: Completion Handler Lambda:
   - Downloads transcription results
   - Extracts transcript text
   - Posts to HelpPet webhook with authentication token
7. **Database Update**: HelpPet webhook:
   - Validates authentication token
   - Finds Visit record by S3 file key
   - Updates Visit with transcript text
   - Changes state from "PROCESSING" to "PROCESSED"

## File Key Format

The system expects S3 files in this format:
```
visit-recordings/YYYY/MM/DD/pet-uuid/visit-uuid.m4a
```

The webhook endpoint `/by-s3-key` finds Visit records by matching the `audio_transcript_url` field.

## Monitoring

### CloudWatch Logs

- **Audio Processor**: `/aws/lambda/helppet-audio-transcription-processor`
- **Transcription Complete**: `/aws/lambda/helppet-transcription-complete-handler`
- **S3 Notification Config**: `/aws/lambda/helppet-s3-notification-configurator`

### Key Metrics

- **Transcription Jobs**: AWS Transcribe console
- **Lambda Invocations**: CloudWatch metrics
- **Webhook Success Rate**: Backend API logs
- **Visit State Changes**: Database queries

## Troubleshooting

### Common Issues

1. **S3 Trigger Not Working**
   - Check S3 bucket notification configuration
   - Verify Lambda permissions for S3 bucket
   - Check file extensions (.m4a, .mp3 only)

2. **Transcription Jobs Failing**
   - Check audio file format and quality
   - Verify AWS Transcribe service limits
   - Check CloudWatch logs for Audio Processor

3. **Webhook Not Receiving Results**
   - Verify EventBridge rule is enabled
   - Check Transcription Complete Handler logs
   - Test webhook endpoint manually

4. **Database Not Updating**
   - Check webhook authentication token
   - Verify Visit record exists with matching S3 URL
   - Check backend API logs

### Test Commands

```bash
# Test webhook endpoint
curl -X POST https://api.helppet.ai/api/v1/webhook/transcription/health

# Check S3 bucket notifications
aws s3api get-bucket-notification-configuration --bucket helppetai-visit-recordings

# List recent transcription jobs
aws transcribe list-transcription-jobs --status COMPLETED --max-items 10

# Check Lambda function
aws lambda get-function --function-name helppet-audio-transcription-processor
```

## Security Considerations

1. **Webhook Authentication**: Simple token-based authentication
2. **IAM Permissions**: Least-privilege access for Lambda roles
3. **S3 Access**: Limited to specific bucket operations
4. **Transcribe Access**: Limited to job operations only

## Costs

- **AWS Transcribe**: $0.024/minute of audio
- **Lambda**: ~$0.01/1000 requests (minimal compute time)
- **S3**: Standard storage and request charges
- **CloudWatch**: Standard logging charges

For a typical 5-minute vet visit recording: ~$0.12 + minimal Lambda/S3 costs.

## Future Enhancements

1. **Medical Vocabulary**: Add veterinary-specific vocabulary to AWS Transcribe
2. **Speaker Identification**: Improve speaker labeling for vet vs. owner
3. **Confidence Scoring**: Filter low-confidence transcriptions
4. **Retry Logic**: Add retry mechanism for failed webhooks
5. **Batch Processing**: Support for multiple file formats
6. **Cost Optimization**: Use Transcribe batch jobs for non-real-time processing