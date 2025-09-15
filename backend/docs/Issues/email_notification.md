import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_calendar_invite(to_email, from_email="you@example.com"):
    ses = boto3.client("ses", region_name="us-east-1")  # change region if needed

    # Generate ICS file
    ics_content = generate_ics()

    # Create email container
    msg = MIMEMultipart("mixed")
    msg["Subject"] = "Calendar Invite: Meeting with Client"
    msg["From"] = from_email
    msg["To"] = to_email

    # Plain-text body
    body = MIMEText("Please find attached a calendar invite.", "plain")
    msg.attach(body)

    # Attach ICS
    attachment = MIMEText(ics_content, "calendar;method=REQUEST")
    attachment.add_header("Content-Disposition", "attachment", filename="invite.ics")
    msg.attach(attachment)

    # Send via SES
    response = ses.send_raw_email(
        Source=from_email,
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()},
    )

    return response


from datetime import datetime, timedelta

def generate_ics():
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = (datetime.utcnow() + timedelta(days=1)).strftime("%Y%m%dT%H%M%SZ")
    dtend   = (datetime.utcnow() + timedelta(days=1, hours=1)).strftime("%Y%m%dT%H%M%SZ")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Company//Your App//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{dtstamp}-your-app@example.com
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Meeting with Client
DESCRIPTION:Discuss project
ORGANIZER;CN=You:mailto:you@example.com
ATTENDEE;CN=Client;RSVP=TRUE:mailto:client@example.com
END:VEVENT
END:VCALENDAR
"""
    return ics_content