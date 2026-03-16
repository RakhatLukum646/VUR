import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


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
        print(f"Verification email sent to {email}")
    except Exception as e:
        print("Email sending failed:", e)
        raise e