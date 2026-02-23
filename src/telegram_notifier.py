"""
Send Telegram report after each application. No-op if TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.
"""
import logging
import requests

import config

logger = logging.getLogger(__name__)


def send_telegram_report(position: str, company: str, job_url: str) -> bool:
    """
    Send one message to the configured Telegram chat: "Applied: [position] @ [company] – [job url]".
    Returns True on success, False otherwise. Does not raise.
    """
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.debug("Telegram report skipped (token or chat_id not set)")
        return False
    text = f"Applied: {position} @ {company} – {job_url}"
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            data={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        if r.ok:
            logger.info("Telegram report sent")
            return True
        logger.warning("Telegram API error: %s %s", r.status_code, r.text[:200])
        return False
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False
