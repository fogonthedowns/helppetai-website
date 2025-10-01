"""
Email service for HelpPetAI using AWS SES
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Email configuration - can be overridden by environment variables
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-1')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'hi@helppet.ai')  # Using verified email
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


def send_email(recipient_email: str, subject: str, body_text: str, body_html: str = None, email_type: str = None) -> bool:
    """
    Send an email to a recipient using AWS SES
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject line
        body_text: Plain text email body
        body_html: HTML version of the email body (optional)
        email_type: Type of email being sent (e.g., 'invitation')
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create SES client
        ses_client = boto3.client('ses', region_name=AWS_REGION)
        
        # Create message structure
        message = {
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': body_text
                }
            }
        }
        
        # Add HTML version if provided
        if body_html:
            message['Body']['Html'] = {'Data': body_html}
        
        # Send email
        response = ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message=message
        )
        
        # Log success
        log_message = f"Email sent to {recipient_email} (SES Message ID: {response['MessageId']})"
        if email_type:
            log_message += f" (type: {email_type})"
        
        logger.info(log_message)
        return True
        
    except ClientError as e:
        # Log error
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {recipient_email}: {str(e)}")
        return False


def send_practice_invitation_email(
    recipient_email: str,
    practice_name: str,
    inviter_name: str,
    invite_id: str,
    invite_code: str,
    inviter_email: str = None
) -> bool:
    """
    Send a practice invitation email
    
    Args:
        recipient_email: Email address of the invitee
        practice_name: Name of the veterinary practice
        inviter_name: Name of the person sending the invitation
        invite_id: Invitation ID (UUID)
        invite_code: Invitation verification code (UUID)
        inviter_email: Email address of the inviter (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Generate invitation URL
    invitation_url = f"{FRONTEND_URL}/accept-invite/{invite_id}?code={invite_code}"
    
    # Create email subject
    subject = f"{inviter_name} invited you to join {practice_name} on HelpPetAI"
    
    # Get a gravatar hash for the inviter (fallback to default if no email available)
    if not inviter_email:
        inviter_email = FROM_EMAIL
    import hashlib
    gravatar_hash = hashlib.md5(inviter_email.lower().encode()).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{gravatar_hash}?s=80&d=mp"
    
    # Create plain text email body
    body_text = f"""
Hello,

{inviter_name} has invited you to join the veterinary practice "{practice_name}" on HelpPetAI.

HelpPetAI is an AI-powered phone system that helps veterinary practices manage calls, schedule appointments, and reduce phone time by up to 80%.

To accept this invitation, please visit:
{invitation_url}

This invitation will expire in 7 days.

Best regards,
The HelpPetAI Team
"""
    
    # Create HTML email body with modern design
    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>{subject}</title>
    <style>
        @media only screen and (max-width: 620px) {{
            table.body h1 {{
                font-size: 28px !important;
                margin-bottom: 10px !important;
            }}
            table.body p,
            table.body ul,
            table.body ol,
            table.body td,
            table.body span,
            table.body a {{
                font-size: 16px !important;
            }}
            table.body .wrapper,
            table.body .article {{
                padding: 10px !important;
            }}
            table.body .content {{
                padding: 0 !important;
            }}
            table.body .container {{
                padding: 0 !important;
                width: 100% !important;
            }}
            table.body .main {{
                border-left-width: 0 !important;
                border-radius: 0 !important;
                border-right-width: 0 !important;
            }}
            table.body .btn table {{
                width: 100% !important;
            }}
            table.body .btn a {{
                width: 100% !important;
            }}
        }}
        @media all {{
            .ExternalClass {{
                width: 100%;
            }}
            .ExternalClass,
            .ExternalClass p,
            .ExternalClass span,
            .ExternalClass font,
            .ExternalClass td,
            .ExternalClass div {{
                line-height: 100%;
            }}
        }}
    </style>
</head>
<body style="background-color: #f6f9fc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; font-size: 16px; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body" style="border-collapse: separate; width: 100%; background-color: #f6f9fc;">
        <tr>
            <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top;">&nbsp;</td>
            <td class="container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top; display: block; max-width: 580px; padding: 10px; width: 580px; margin: 0 auto;">
                <div class="content" style="box-sizing: border-box; display: block; margin: 0 auto; max-width: 580px; padding: 10px;">
                    <!-- CENTERED WHITE CONTAINER -->
                    <table role="presentation" class="main" style="border-collapse: separate; border-radius: 8px; background: #ffffff; width: 100%; box-shadow: 0px 2px 5px rgba(0,0,0,0.05);">
                        <!-- HEADER -->
                        <tr>
                            <td style="padding: 30px 30px 20px 30px; text-align: center;">
                                <h2 style="color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 600; font-size: 28px; margin: 0;">HelpPetAI</h2>
                            </td>
                        </tr>
                        <!-- MAIN CONTENT AREA -->
                        <tr>
                            <td class="wrapper" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top; box-sizing: border-box; padding: 0 30px 30px 30px;">
                                <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                    <tr>
                                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top;">
                                            <div style="margin-bottom: 24px; padding: 20px; background-color: #f9fafb; border-radius: 8px; border-left: 4px solid #3b82f6;">
                                                <div style="display: flex; align-items: center;">
                                                    <img src="{gravatar_url}" alt="{inviter_name}" width="48" height="48" style="border-radius: 50%; margin-right: 12px; border: none;">
                                                    <div>
                                                        <h1 style="color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 600; line-height: 1.2; font-size: 20px; margin: 0 0 4px 0;">Join {practice_name}</h1>
                                                        <p style="color: #6b7280; margin: 0; font-size: 14px;"><strong>{inviter_name}</strong> has invited you</p>
                                                    </div>
                                                </div>
                                            </div>
                                            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; font-weight: normal; margin: 0 0 20px 0; color: #374151; line-height: 1.5;">You've been invited to join <strong>{practice_name}</strong> on HelpPetAI, the AI-powered phone system that helps veterinary practices save up to 80% of their phone time.</p>
                                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="btn btn-primary" style="border-collapse: separate; box-sizing: border-box; width: 100%; min-width: 100%;">
                                                <tbody>
                                                    <tr>
                                                        <td align="center" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top; padding-bottom: 16px;">
                                                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: auto;">
                                                                <tbody>
                                                                    <tr>
                                                                        <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top; border-radius: 8px; text-align: center; background-color: #3b82f6;">
                                                                            <a href="{invitation_url}" target="_blank" style="border: solid 1px #3b82f6; border-radius: 8px; box-sizing: border-box; cursor: pointer; display: inline-block; font-size: 16px; font-weight: 600; margin: 0; padding: 14px 28px; text-decoration: none; background-color: #3b82f6; border-color: #3b82f6; color: #ffffff;">Accept Invitation</a>
                                                                        </td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin-top: 20px; border-left: 4px solid #f59e0b;">
                                                <p style="color: #92400e; margin: 0; font-size: 14px; line-height: 1.5;"><strong>Note:</strong> This invitation will expire in 7 days.</p>
                                            </div>
                                            <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
                                                <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; font-weight: normal; margin: 0; color: #6b7280; line-height: 1.5;">Or copy and paste this link into your browser:</p>
                                                <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 13px; font-weight: normal; margin: 8px 0 0 0; color: #3b82f6; word-break: break-all; background-color: #f9fafb; padding: 8px; border-radius: 4px;">{invitation_url}</p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    <!-- FOOTER -->
                    <div class="footer" style="clear: both; margin-top: 10px; text-align: center; width: 100%;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                            <tr>
                                <td class="content-block" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #9ca3af; font-size: 12px; text-align: center;">
                                    <span style="color: #9ca3af; font-size: 12px;">HelpPetAI</span>
                                    <br>
                                    <span style="color: #9ca3af; font-size: 12px;">This is an automated message, please do not reply to this email.</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </td>
            <td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; vertical-align: top;">&nbsp;</td>
        </tr>
    </table>
</body>
</html>
"""
    
    # Send the email
    return send_email(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        email_type='practice_invitation'
    )

