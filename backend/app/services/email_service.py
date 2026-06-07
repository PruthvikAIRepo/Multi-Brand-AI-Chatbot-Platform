"""Email service for sending password reset links and user invitations.
Uses SMTP (works with AWS SES, SendGrid, Gmail, etc.)
Configure SMTP settings in .env. Falls back to logging in development mode."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

settings = get_settings()


async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email with the reset link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    subject = "Password Reset Request"
    html = f"""
    <h2>Password Reset</h2>
    <p>You requested a password reset. Click the link below to set a new password:</p>
    <p><a href="{reset_url}" style="background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Reset Password</a></p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request this, please ignore this email.</p>
    """

    return await _send_email(email, subject, html)


async def send_invitation_email(email: str, full_name: str, temp_password: str) -> bool:
    """Send invitation email with temporary password."""
    login_url = f"{settings.FRONTEND_URL}/login"

    subject = "You've Been Invited to the Admin Panel"
    html = f"""
    <h2>Welcome, {full_name}!</h2>
    <p>You've been invited to manage the chatbot admin panel.</p>
    <p><strong>Your login credentials:</strong></p>
    <ul>
        <li>Email: {email}</li>
        <li>Temporary Password: <code>{temp_password}</code></li>
    </ul>
    <p><a href="{login_url}" style="background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Login Now</a></p>
    <p>You'll be asked to change your password on first login.</p>
    """

    return await _send_email(email, subject, html)


async def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email. Returns True on success, False on failure.
    In development mode, logs the email instead of sending."""

    # Development mode — log instead of sending
    if settings.ENVIRONMENT == "development":
        if not settings.SMTP_HOST:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[DEV EMAIL] To: {to}, Subject: {subject}")
            return True

    if not settings.SMTP_HOST:
        return False

    try:
        import asyncio

        def _send_sync():
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())

        # Run blocking SMTP in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync)

        return True
    except Exception:
        return False
