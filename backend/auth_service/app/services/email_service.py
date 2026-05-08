import logging
import smtplib
import textwrap
from urllib.parse import urlparse, urlunparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("auth_service")

def _frontend_link(path: str) -> str:
    raw_base = (settings.frontend_url or "").strip().rstrip("/")
    if not raw_base:
        raw_base = "http://localhost:5173"

    parsed = urlparse(raw_base)
    if not parsed.scheme:
        parsed = urlparse(f"http://{raw_base}")

    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    is_localhost = hostname in {"localhost", "127.0.0.1"}

    if is_localhost and port is None:
        netloc = f"{hostname}:5173"
        parsed = parsed._replace(netloc=netloc)

    base = urlunparse(parsed).rstrip("/")
    return f"{base}{path}"


def send_verification_email(email: str, token: str):
    verification_link = _frontend_link(f"/verify-email?token={token}")

    subject = "Verify your email"
    body = textwrap.dedent(
        f"""\
        Hello,

        Thank you for registering in SignZhan.

        Please verify your email by clicking the link below:

        <{verification_link}>

        If you did not create this account, you can ignore this email.
        """
    ).strip()

    msg = MIMEMultipart()
    msg["From"] = f"SignZhan <{settings.email_user}>"
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
    reset_link = _frontend_link(f"/reset-password?token={token}")

    subject = "Reset your password"
    body = textwrap.dedent(
        f"""\
        Hello,

        We received a request to reset your SignZhan password.

        Use the link below to set a new password:

        <{reset_link}>

        This link expires in {settings.password_reset_expire_minutes} minutes.
        If you did not request a reset, you can ignore this message.
        """
    ).strip()

    msg = MIMEMultipart()
    msg["From"] = f"SignZhan <{settings.email_user}>"
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
