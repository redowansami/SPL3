"""OTP generation and the registration-confirmation email (Gmail SMTP via smtplib)."""

import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from starlette.concurrency import run_in_threadpool

from backend.app.core.config import (
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_PASSWORD,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_USERNAME,
)

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "otp_email.html"


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _render_template(otp_code: str, expire_minutes: int) -> str:
    html = _TEMPLATE_PATH.read_text(encoding="utf-8")
    return html.replace("{{OTP_CODE}}", otp_code).replace("{{EXPIRE_MINUTES}}", str(expire_minutes))


def _send_smtp(email: str, subject: str, html_body: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM or MAIL_USERNAME}>"
    message["To"] = email
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15) as server:
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_FROM or MAIL_USERNAME, [email], message.as_string())


async def send_otp_email(email: str, otp_code: str, expire_minutes: int) -> None:
    html_body = _render_template(otp_code, expire_minutes)
    await run_in_threadpool(_send_smtp, email, "Your ATLAS-Scan verification code", html_body)
