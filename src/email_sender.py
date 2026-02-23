"""
Send application email via Gmail SMTP: motivation letter + portfolio link.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def send_application_email(to_email: str, company_name: str, job_position: str) -> bool:
    """
    Send one application email to to_email. Subject and body use company_name and job_position.
    Returns True on success, False on failure.
    """
    if not to_email or not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        return False
    subject = f"Application: Spring Boot Developer – {company_name}"
    body = config.MOTIVATION_LETTER.strip()
    body += f"\n\nPortfolio: {config.PORTFOLIO_URL}\n\n"
    body += "Best regards,\nTaha Arar"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.sendmail(config.GMAIL_USER, [to_email], msg.as_string())
        logger.info("Sent application to %s", to_email)
        return True
    except Exception as e:
        logger.warning("SMTP send to %s failed: %s", to_email, e)
        return False
