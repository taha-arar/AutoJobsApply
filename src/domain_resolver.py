"""
Company name to candidate domain(s). Slugify and try .com, .io, .co.
"""
import re


def slugify(name: str) -> str:
    """Lowercase, alphanumeric and spaces only, then replace spaces with nothing."""
    if not name or not isinstance(name, str):
        return ""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "", s)
    return s[:50]  # avoid very long slugs


def candidate_domains(company_name: str) -> list[str]:
    """Return list of domain candidates to try (e.g. company.com, company.io, company.co)."""
    slug = slugify(company_name)
    if not slug:
        return []
    return [f"{slug}.com", f"{slug}.io", f"{slug}.co"]
