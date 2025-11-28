"""
Email service for sending OTP and notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Email configuration from settings (loaded from .env)
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
SMTP_USERNAME = settings.smtp_username
SMTP_PASSWORD = settings.smtp_password
SENDER_EMAIL = settings.sender_email or settings.smtp_username
SENDER_NAME = settings.sender_name


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content
        text_content: Plain text content (fallback)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # If SMTP not configured, log the email instead
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP not configured. Email content:")
        logger.warning(f"To: {to_email}")
        logger.warning(f"Subject: {subject}")
        logger.warning(f"Content: {html_content}")
        print(f"\n{'='*60}")
        print(f"📧 EMAIL (SMTP Not Configured)")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{text_content or html_content}")
        print(f"{'='*60}\n")
        return True  # Return True for development
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        message["To"] = to_email
        
        # Add text and HTML parts
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_otp_email(email: str, otp: str, user_name: str) -> bool:
    """
    Send OTP email for password reset
    
    Args:
        email: Recipient email address
        otp: 6-digit OTP code
        user_name: User's name
    
    Returns:
        bool: True if sent successfully
    """
    subject = "Password Reset OTP - Restaurant POS"
    
    text_content = f"""
Hello {user_name},

You have requested to reset your password for Restaurant POS.

Your OTP code is: {otp}

This code will expire in 10 minutes.

If you didn't request this password reset, please ignore this email or contact support.

Best regards,
Restaurant POS Team
    """.strip()
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .otp-code {{
            background: #f8f9fa;
            border: 2px dashed #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 8px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin: 20px 0;
            border-radius: 4px;
            text-align: left;
        }}
        .footer {{
            color: white;
            margin-top: 20px;
            font-size: 14px;
        }}
        h1 {{
            color: white;
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Password Reset</h1>
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>You have requested to reset your password for Restaurant POS.</p>
            
            <p>Your One-Time Password (OTP) is:</p>
            
            <div class="otp-code">{otp}</div>
            
            <p><strong>This code will expire in 10 minutes.</strong></p>
            
            <div class="warning">
                ⚠️ <strong>Security Notice:</strong><br>
                If you didn't request this password reset, please ignore this email or contact our support team immediately.
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Best regards,<br>
                <strong>Restaurant POS Team</strong>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(email, subject, html_content, text_content)


def send_password_reset_confirmation(email: str, user_name: str) -> bool:
    """
    Send confirmation email after password has been reset
    
    Args:
        email: Recipient email address
        user_name: User's name
    
    Returns:
        bool: True if sent successfully
    """
    subject = "Password Reset Successful - Restaurant POS"
    
    text_content = f"""
Hello {user_name},

Your password has been successfully reset for Restaurant POS.

If you did not perform this action, please contact our support team immediately.

Best regards,
Restaurant POS Team
    """.strip()
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 40px 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .success-icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        .footer {{
            color: white;
            margin-top: 20px;
            font-size: 14px;
        }}
        h1 {{
            color: white;
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Password Reset Successful</h1>
        <div class="content">
            <div class="success-icon">✓</div>
            
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>Your password has been successfully reset for Restaurant POS.</p>
            
            <p>You can now login with your new password.</p>
            
            <p style="margin-top: 30px; padding: 15px; background: #fff3cd; border-radius: 4px;">
                ⚠️ If you did not perform this action, please contact our support team immediately.
            </p>
            
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Best regards,<br>
                <strong>Restaurant POS Team</strong>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(email, subject, html_content, text_content)
