"""
Find contact email for a domain: use Hunter.io when API key is set, else guess jobs@domain.
"""
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

HUNTER_DOMAIN_SEARCH = "https://api.hunter.io/v2/domain-search"
PREFERRED_PREFIXES = ("hr@", "jobs@", "careers@", "contact@", "info@")


def _hunter_find(domain: str) -> str | None:
    """Return one email from Hunter.io or None."""
    if not config.HUNTER_API_KEY:
        return None
    domain = domain.lower().strip()
    if " " in domain or "/" in domain or "@" in domain:
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
        for prefix in PREFERRED_PREFIXES:
            for e in emails:
                if isinstance(e, dict):
                    addr = (e.get("value") or e.get("email") or "").lower()
                    if addr and addr.startswith(prefix):
                        return addr
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
        time.sleep(1.5)


def _guess_email(domain: str) -> str | None:
    """Return guessed email jobs@domain or None if domain invalid."""
    if not domain or not isinstance(domain, str):
        return None
    domain = domain.lower().strip()
    if " " in domain or "/" in domain or "@" in domain:
        return None
    if len(domain) > 253:
        return None
    return f"jobs@{domain}"


def find_email_for_domain(domain: str) -> str | None:
    """
    Return one email for the domain. Uses Hunter.io when HUNTER_API_KEY is set,
    otherwise falls back to jobs@domain.
    """
    if not domain or not isinstance(domain, str):
        return None
    domain = domain.lower().strip()
    email = _hunter_find(domain)
    if email:
        return email
    return _guess_email(domain)
