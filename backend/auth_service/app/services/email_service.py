import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("auth_service")


def send_verification_email(email: str, token: str):
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"

    subject = "Verify your email"
    body = f"""
    Hello,

    Thank you for registering in VUR Translator.

    Please verify your email by clicking the link below:

    {verification_link}

    If you did not create this account, you can ignore this email.
    """

    msg = MIMEMultipart()
    msg["From"] = f"VUR Translator <{settings.email_user}>"
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(settings.email_host, settings.email_port)
        server.starttls()
        server.login(settings.email_user, settings.email_password)
        server.send_message(msg)
        server.quit()
        logger.info("verification_email_sent email=%s", email)
    except Exception as e:
        # SMTP not configured — log the link so local dev can still verify accounts.
        logger.warning(
            "email_send_failed reason=%s verification_link=%s", e, verification_link
        )


def send_password_reset_email(email: str, token: str):
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"

    subject = "Reset your password"
    body = f"""
    Hello,

    We received a request to reset your VUR Translator password.

    Use the link below to set a new password:

    {reset_link}

    This link expires in {settings.password_reset_expire_minutes} minutes.
    If you did not request a reset, you can ignore this message.
    """

    msg = MIMEMultipart()
    msg["From"] = f"VUR Translator <{settings.email_user}>"
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(settings.email_host, settings.email_port)
        server.starttls()
        server.login(settings.email_user, settings.email_password)
        server.send_message(msg)
        server.quit()
        logger.info("password_reset_email_sent email=%s", email)
    except Exception as e:
        logger.warning(
            "email_send_failed reason=%s reset_link=%s", e, reset_link
        )
