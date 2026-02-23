"""
Hunter.io domain-search: get best email for a domain. Prefer hr@, jobs@, careers@, contact@, info@.
"""
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

PREFERRED_PREFIXES = ("hr@", "jobs@", "careers@", "contact@", "info@")
HUNTER_DOMAIN_SEARCH = "https://api.hunter.io/v2/domain-search"


def find_email_for_domain(domain: str) -> str | None:
    """
    Return one email for the domain, or None. Prefer generic addresses.
    Rate limit: short delay between calls.
    """
    if not domain or not config.HUNTER_API_KEY:
        return None
    domain = domain.lower().strip()
    if " " in domain or "/" in domain:
        return None
    try:
        r = requests.get(
            HUNTER_DOMAIN_SEARCH,
            params={"domain": domain, "api_key": config.HUNTER_API_KEY},
            headers={"User-Agent": "AutoApply/1.0"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        emails = data.get("data", {}).get("emails")
        if not emails or not isinstance(emails, list):
            return None
        # Prefer generic addresses
        for prefix in PREFERRED_PREFIXES:
            for e in emails:
                if isinstance(e, dict):
                    addr = (e.get("value") or e.get("email") or "").lower()
                    if addr and addr.startswith(prefix):
                        return addr
        # Else first valid
        for e in emails:
            if isinstance(e, dict):
                addr = (e.get("value") or e.get("email") or "").strip()
                if addr and "@" in addr:
                    return addr
        return None
    except Exception as e:
        logger.warning("Hunter domain-search %s failed: %s", domain, e)
        return None
    finally:
        time.sleep(1.5)  # rate limit
