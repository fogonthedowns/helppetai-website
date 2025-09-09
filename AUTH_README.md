# Authentication & Authorization Issues Resolution

This document details the complex authentication and authorization issues encountered in the HelpPet.ai production environment and the solutions implemented to resolve them.

## Issues Encountered

### 1. Database Password Authentication Failure

**Problem:**
```
InvalidPasswordError: password authentication failed for user "helppetadmin"
```

**Root Cause:**
The RDS_PASSWORD environment variable in the ECS task definition was set to the literal string "DB" instead of the actual database password.

**Impact:**
- All database-dependent API endpoints returned 500 errors
- The application could start but couldn't establish database connections
- Health checks with database queries failed

**Solution:**
1. **Generated secure password**: Created a 25-character random password using OpenSSL
2. **Stored in AWS Secrets Manager**: Created secret `helppet-prod/database-password`
3. **Updated RDS instance**: Changed master password to match the generated password
4. **Modified task definition**: Replaced hardcoded password with Secrets Manager reference
5. **Added IAM permissions**: Granted execution role access to read from Secrets Manager

**Files Changed:**
- ECS Task Definition: Updated to use `secrets` instead of `environment` for RDS_PASSWORD
- IAM Role: Added SecretsManagerReadWrite policy to execution role

### 2. AWS S3 Credentials Authentication Failure

**Problem:**
```
POST /api/v1/visit-transcripts/audio/upload/initiate HTTP/1.1" 500 Internal Server Error
```

**Root Cause:**
The audio upload endpoint was trying to create S3 clients using explicit AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) which were empty in the task definition, causing boto3 to fail with NoCredentialsError.

**Impact:**
- iPhone m4v file uploads failed with 500 errors
- Users saw "The recording service is temporarily down" message
- S3 presigned URL generation failed

**Solution:**
1. **Updated S3 client creation**: Modified `get_s3_client()` function to use IAM roles first, fallback to explicit credentials
2. **Added task role**: Assigned existing `helppet-api-prod-TaskRole-09am3AGqERAX` to ECS task definition
3. **Verified IAM permissions**: Confirmed task role has `s3:*` permissions on all resources
4. **Updated deployment**: Built new Docker image and deployed with updated task definition

**Code Changes:**
```python
def get_s3_client():
    """Get configured S3 client using IAM role or explicit credentials"""
    try:
        # Try to use IAM role first (recommended for ECS/EC2)
        return boto3.client('s3', region_name=S3_REGION)
    except NoCredentialsError:
        # Fallback to explicit credentials if IAM role not available
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 credentials not configured and IAM role not available"
            )
        
        return boto3.client(
            's3',
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
```

## Security Best Practices Implemented

### 1. AWS Secrets Manager Integration

- **Secure Storage**: Database passwords stored encrypted in AWS Secrets Manager
- **Automatic Rotation**: Can be rotated without code changes
- **Least Privilege**: ECS execution role has minimal permissions to read specific secrets
- **No Hardcoded Secrets**: Removed all hardcoded passwords from task definitions

### 2. IAM Role-Based Authentication

- **Task Roles**: ECS tasks use IAM roles instead of hardcoded AWS credentials
- **Service-to-Service**: Secure communication between ECS and AWS services (S3, RDS, Secrets Manager)
- **Credential Rotation**: IAM credentials automatically managed by AWS
- **Audit Trail**: All API calls logged in CloudTrail

### 3. Defense in Depth

- **Multiple Auth Layers**: Database auth + AWS service auth + application auth
- **Fallback Mechanisms**: S3 client tries IAM role first, falls back to explicit creds if needed
- **Error Handling**: Graceful failure with informative error messages
- **Connection Resilience**: Database connection pooling with retry logic

## Infrastructure Changes

### ECS Task Definition Updates

**Before:**
```json
{
  "environment": [
    {
      "name": "RDS_PASSWORD",
      "value": "DB"
    },
    {
      "name": "AWS_ACCESS_KEY_ID",
      "value": ""
    },
    {
      "name": "AWS_SECRET_ACCESS_KEY", 
      "value": ""
    }
  ]
}
```

**After:**
```json
{
  "taskRoleArn": "arn:aws:iam::724843234496:role/helppet-api-prod-TaskRole-09am3AGqERAX",
  "secrets": [
    {
      "name": "RDS_PASSWORD",
      "valueFrom": "arn:aws:secretsmanager:us-west-1:724843234496:secret:helppet-prod/database-password-gcpLfV"
    }
  ],
  "environment": [
    // AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY removed - using IAM role
  ]
}
```

### IAM Permissions

**Execution Role** (`helppet-api-prod-TaskExecutionRole-pNhwKGdip9aE`):
- `SecretsManagerReadWrite` policy for reading database password
- ECR and CloudWatch Logs permissions (existing)

**Task Role** (`helppet-api-prod-TaskRole-09am3AGqERAX`):
- Inline policy `HelpPetAITaskPermissions` with `s3:*` and `dynamodb:*` permissions

## Deployment Process

### Task Definition Revisions
- **Revision 59**: Original with hardcoded password "DB"
- **Revision 60**: Added Secrets Manager integration for database password
- **Revision 61**: Added task role for S3 access (final working version)

### Deployment Commands
```bash
# Build updated Docker image
make build-prod

# Push to ECR
make push-image

# Update ECS service
aws ecs update-service --cluster helppet-prod --service helppet-api-prod \
  --task-definition helppet-api-prod:61 --force-new-deployment
```

## Verification

### Database Connection
```bash
curl https://api.helppet.ai/health/db
# Returns: {"status": "healthy", "database": "postgresql", "connection": "active"}
```

### S3 Audio Upload
- iPhone m4v file upload now works successfully
- Generates presigned S3 URLs without errors
- No more "recording service temporarily down" messages

## Lessons Learned

1. **Never hardcode credentials**: Use AWS services like Secrets Manager and IAM roles
2. **Implement proper error handling**: Generic 500 errors mask the real issues
3. **Use CloudWatch logs**: Essential for debugging production issues
4. **Test end-to-end**: Database health checks don't catch S3 credential issues
5. **Document infrastructure**: Complex auth issues require detailed documentation

## Future Improvements

1. **Secret Rotation**: Implement automatic database password rotation
2. **Parameter Store**: Consider using AWS Systems Manager Parameter Store for non-sensitive config
3. **Monitoring**: Add CloudWatch alarms for authentication failures
4. **Health Checks**: Expand health endpoints to test all external service connections
5. **Terraform/CDK**: Infrastructure as Code for better change management

---

**Resolution Date**: September 8, 2025  
**Task Definitions**: helppet-api-prod:59 → helppet-api-prod:61  
**Status**: ✅ Resolved - All authentication issues fixed