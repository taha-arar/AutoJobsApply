"""
Verify email deliverability via Hunter.io Email Verifier. When HUNTER_API_KEY is set,
only addresses with status 'valid' or 'accept_all' are considered deliverable.
"""
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

HUNTER_EMAIL_VERIFIER = "https://api.hunter.io/v2/email-verifier"
REQUEST_HEADERS = {"User-Agent": "AutoApply/1.0 (job application agent)"}

# Treat both 'valid' and 'accept_all' as deliverable (many corporate domains use accept-all).
DELIVERABLE_STATUSES = ("valid", "accept_all")


def is_deliverable(email: str) -> bool:
    """
    Return True if the email is considered deliverable.
    When HUNTER_API_KEY is not set, returns True (no verification, pipeline unchanged).
    When set, calls Hunter Email Verifier and returns True only for status 'valid' or 'accept_all'.
    """
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if "@" not in email:
        return False

    if not config.HUNTER_API_KEY:
        return True

    try:
        r = requests.get(
            HUNTER_EMAIL_VERIFIER,
            params={"email": email, "api_key": config.HUNTER_API_KEY},
            headers=REQUEST_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        status = (data.get("data") or {}).get("status")
        if status in DELIVERABLE_STATUSES:
            return True
        logger.debug("Hunter verifier: %s status=%s", email, status)
        return False
    except Exception as e:
        logger.warning("Hunter email-verifier %s failed: %s", email, e)
        return False
    finally:
        time.sleep(1.5)
