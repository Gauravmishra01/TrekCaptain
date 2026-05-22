import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import emails  # type: ignore[import-untyped]
import jwt
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


def _email_shell(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{title}</title>
  </head>
  <body style=\"margin:0;background:#fafbfc;font-family:Arial,Helvetica,sans-serif;color:#1f2937;\">
    <div style=\"max-width:600px;margin:0 auto;padding:32px 16px;\">
      <div style=\"background:#ffffff;border-radius:16px;padding:32px;border:1px solid #e5e7eb;\">
        {body_html}
      </div>
    </div>
  </body>
</html>"""


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    project_name = context.get("project_name", settings.PROJECT_NAME)
    if template_name == "test_email.html":
        return _email_shell(
            f"{project_name} - Test email",
            f"<h1 style=\"margin:0 0 16px;font-size:24px;\">{project_name}</h1>"
            f"<p style=\"margin:0 0 8px;\">Test email for: <strong>{context.get('email', '')}</strong></p>",
        )
    if template_name == "reset_password.html":
        return _email_shell(
            f"{project_name} - Password recovery for user {context.get('username', '')}",
            f"<h1 style=\"margin:0 0 16px;font-size:24px;\">{project_name} - Password Recovery</h1>"
            f"<p style=\"margin:0 0 8px;\">Hello {context.get('username', '')}</p>"
            f"<p style=\"margin:0 0 16px;\">We've received a request to reset your password.</p>"
            f"<p><a href=\"{context.get('link', '#')}\" style=\"display:inline-block;background:#0ea5e9;color:#ffffff;text-decoration:none;padding:12px 20px;border-radius:8px;\">Reset password</a></p>"
            f"<p style=\"margin-top:16px;color:#6b7280;font-size:14px;\">This password will expire in {context.get('valid_hours', settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)} hours.</p>",
        )
    if template_name == "new_account.html":
        return _email_shell(
            f"{project_name} - New account for user {context.get('username', '')}",
            f"<h1 style=\"margin:0 0 16px;font-size:24px;\">{project_name} - New Account</h1>"
            f"<p style=\"margin:0 0 8px;\">Welcome to your new account!</p>"
            f"<p style=\"margin:0 0 8px;\">Username: <strong>{context.get('username', '')}</strong></p>"
            f"<p style=\"margin:0 0 16px;\">Password: <strong>{context.get('password', '')}</strong></p>"
            f"<p><a href=\"{context.get('link', settings.FRONTEND_HOST)}\" style=\"display:inline-block;background:#0ea5e9;color:#ffffff;text-decoration:none;padding:12px 20px;border-radius:8px;\">Go to Dashboard</a></p>",
        )
    if template_name == "agency_login_otp.html":
        return _email_shell(
            f"{project_name} - Login OTP",
            f"<h1 style=\"margin:0 0 16px;font-size:24px;\">{project_name} - Login OTP</h1>"
            f"<p style=\"margin:0 0 8px;\">Use the following OTP to continue signing in:</p>"
            f"<p style=\"font-size:32px;letter-spacing:8px;font-weight:700;margin:16px 0;color:#0f172a;\">{context.get('otp_code', '')}</p>"
            f"<p style=\"margin:0;color:#6b7280;font-size:14px;\">This code expires in 10 minutes.</p>",
        )
    return _email_shell(project_name, "<p>Email template</p>")


def send_email(*, email_to: str, subject: str = "", html_content: str = "") -> None:
    from_name = settings.EMAILS_FROM_NAME or settings.PROJECT_NAME
    from_email = settings.EMAILS_FROM_EMAIL or "info@example.com"
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(from_name, from_email),
    )
    if not settings.SMTP_HOST:
        logger.info("SMTP_HOST is not configured; skipping email to %s", email_to)
        return
    smtp_options: dict[str, Any] = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info("send email result: %s", response)


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_login_otp_email(email_to: str, otp_code: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Login verification code"
    html_content = render_email_template(
        template_name="agency_login_otp.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
            "otp_code": otp_code,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    encoded_jwt = jwt.encode(
        {"exp": expires, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
