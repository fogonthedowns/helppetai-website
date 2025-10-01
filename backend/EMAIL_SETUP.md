# Email Setup for Practice Invitations

## Overview

HelpPetAI uses AWS SES (Simple Email Service) to send practice invitation emails. The email system is integrated into the invitation workflow to automatically send beautifully designed emails when team members are invited to join a practice.

## AWS SES Configuration

### Verified Identities

The following identities are verified in AWS SES (us-west-1):

1. **Domain**: `helppet.ai`
   - ARN: `arn:aws:ses:us-west-1:724843234496:identity/helppet.ai`
   - Status: Verified
   - Can send emails from any `@helppet.ai` address

2. **Email**: `hi@upcactus.com`
   - ARN: `arn:aws:ses:us-west-1:724843234496:identity/hi@upcactus.com`
   - Status: Verified
   - Currently used as the default sender

## Environment Variables

Add these to your `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-west-1
AWS_DEFAULT_REGION=us-west-1

# Email Configuration (AWS SES)
FROM_EMAIL=hi@upcactus.com

# Frontend URL (for invitation links)
FRONTEND_URL=http://localhost:3000  # Development
# FRONTEND_URL=https://helppet.ai    # Production
```

### AWS Credentials

**Local Development:**
- Use AWS CLI configured credentials: `aws configure`
- Or set environment variables:
  ```bash
  AWS_ACCESS_KEY_ID=your_access_key
  AWS_SECRET_ACCESS_KEY=your_secret_key
  ```

**Production (EC2/ECS):**
- Use IAM roles attached to the instance/service
- No credentials needed in environment variables

## Email Template

The invitation email includes:

### Design Features
- Modern, clean design based on Apple/Notion aesthetics
- Mobile-responsive layout
- Professional branding with HelpPetAI name
- Gravatar integration for inviter profile picture
- Clear call-to-action button
- Practice name prominently displayed
- Expiration notice (7 days)
- Copy-paste link option for accessibility

### Email Content
- **Subject**: `{inviter_name} invited you to join {practice_name} on HelpPetAI`
- **From**: `hi@upcactus.com` (or configured FROM_EMAIL)
- **HTML & Plain Text** versions included

## Usage

The email is automatically sent when a VET_STAFF or ADMIN creates an invitation via:

```bash
POST /api/v1/practices/{practice_id}/invites
{
  "email": "colleague@example.com"
}
```

### Email Sending Process

1. User creates invitation via API
2. Invitation record created in database
3. Email service called with:
   - Recipient email
   - Practice name
   - Inviter name and email
   - Unique invitation ID and code
4. HTML email sent via AWS SES
5. Recipient receives email with link: `/accept-invite/{id}?code={code}`

### Error Handling

- Email failures are logged but **do not** fail the invitation creation
- Invitation is still created in database even if email fails
- Admin can resend or share invitation link manually
- Check logs for email sending errors

## Testing

### Test Email Sending

```python
from src.utils.email_service import send_practice_invitation_email

# Send test invitation
result = send_practice_invitation_email(
    recipient_email="test@example.com",
    practice_name="Test Veterinary Clinic",
    inviter_name="Dr. Jane Smith",
    invite_id="123e4567-e89b-12d3-a456-426614174000",
    invite_code="987fcdeb-51a2-43e1-b234-567890abcdef",
    inviter_email="jane@example.com"
)

print(f"Email sent: {result}")
```

### Email Preview

The generated email includes:
- HelpPetAI header
- Inviter's gravatar and name
- Practice name in highlighted box
- Blue "Accept Invitation" button
- 7-day expiration warning
- Copy-paste link option
- Professional footer

## Monitoring

### Check Email Status

1. **AWS SES Console**: 
   - Go to AWS SES → Email sending → Configuration sets
   - Monitor send rate, bounces, complaints

2. **Application Logs**:
   ```bash
   # Success
   Email sent to user@example.com (SES Message ID: xxx) (type: practice_invitation)
   
   # Failure
   Failed to send email to user@example.com: [error details]
   ```

### Common Issues

**Issue**: Email not received
- Check spam/junk folder
- Verify recipient email is valid
- Check AWS SES sending limits (sandbox mode allows 200 emails/day)
- Verify FROM_EMAIL is a verified identity

**Issue**: SES Sandbox Limits
- Request production access in AWS SES console
- Sandbox mode: Can only send to verified emails
- Production mode: Can send to any email

## Switching to helppet.ai Email

To use `@helppet.ai` addresses instead of `hi@upcactus.com`:

1. Update `.env`:
   ```bash
   FROM_EMAIL=support@helppet.ai
   # or
   FROM_EMAIL=noreply@helppet.ai
   ```

2. Verify the email address in AWS SES (or use the domain verification which covers all `@helppet.ai` addresses)

3. Restart the application

## Production Checklist

- [ ] AWS SES moved out of sandbox mode
- [ ] IAM role configured for production environment
- [ ] `FROM_EMAIL` set to appropriate `@helppet.ai` address
- [ ] `FRONTEND_URL` set to production URL
- [ ] Email sending monitored in CloudWatch
- [ ] Bounce and complaint notifications configured
- [ ] DKIM and SPF records configured for helppet.ai domain

## Email Content Customization

To modify the email template, edit:
```
backend/src/utils/email_service.py
```

Key sections:
- `body_text`: Plain text version
- `body_html`: HTML version with styling
- Update subject line, branding, colors as needed

