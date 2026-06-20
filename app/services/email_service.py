import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY

FROM_EMAIL = settings.FROM_EMAIL
FRONTEND_URL = settings.FRONTEND_URL


def send_password_reset_email(to_email: str, token: str):
    """Send password reset link to user's email"""

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": "Reset your Marketonomy password",
        "html": f"""
            <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                <h2>Reset your password</h2>
                <p>We received a request to reset your Marketonomy password.</p>
                <p>Click the button below to set a new password. This link expires in 30 minutes.</p>
                <a href="{reset_link}"
                   style="display: inline-block; background: #185FA5; color: white;
                          padding: 10px 20px; border-radius: 6px; text-decoration: none;
                          margin: 16px 0;">
                    Reset Password
                </a>
                <p style="color: #666; font-size: 13px;">
                    If you didn't request this, you can safely ignore this email.
                </p>
            </div>
        """
    })


def send_welcome_email(to_email: str, first_name: str):
    """Send welcome email after successful signup"""

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": "Welcome to Marketonomy!",
        "html": f"""
            <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                <h2>Welcome to Marketonomy, {first_name}! 🎉</h2>
                <p>Your account has been created successfully.</p>
                <p>You can now log in with Google or your email and password.</p>
            </div>
        """
    })


def send_suspicious_login_alert(to_email: str, ip_address: str, device_info: str):
    """Alert user of a new/suspicious login"""

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": "New login detected on your Marketonomy account",
        "html": f"""
            <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                <h2>New login detected</h2>
                <p>We noticed a new login to your account:</p>
                <ul>
                    <li>IP Address: {ip_address}</li>
                    <li>Device: {device_info}</li>
                </ul>
                <p style="color: #666; font-size: 13px;">
                    If this wasn't you, please reset your password immediately.
                </p>
            </div>
        """
    })