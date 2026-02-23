"""
Fetch jobs from all 10 sources (APIs + RSS), normalize, filter by Spring Boot/Java/backend, dedupe by URL.
"""
import logging
import time
import feedparser
import requests

import config

logger = logging.getLogger(__name__)

KEYWORDS = ("spring boot", "springboot", "java", "backend")
REQUEST_HEADERS = {"User-Agent": "AutoApply/1.0 (job application agent)"}


def _matches(job: dict) -> bool:
    """True if job title/position/tags/description contain any keyword."""
    text = " ".join(
        str(job.get(k, "")) for k in ("position", "title", "company", "company_name")
    ).lower()
    desc = (job.get("description") or job.get("summary") or "").lower()
    tags = " ".join(job.get("tags") or []).lower()
    combined = f"{text} {desc} {tags}"
    return any(kw in combined for kw in KEYWORDS)


def _normalize(source: str, job_id: str, company: str, position: str, url: str) -> dict | None:
    if not (company or position) or not url:
        return None
    return {
        "source": source,
        "id": str(job_id),
        "company": (company or "").strip(),
        "position": (position or "").strip(),
        "url": url.strip(),
    }


def fetch_remoteok() -> list[dict]:
    """RemoteOK API. First element is metadata."""
    try:
        r = requests.get(
            "https://remoteok.com/api",
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) < 2:
            return []
        jobs = []
        for item in data[1:]:
            if not isinstance(item, dict):
                continue
            job_url = (item.get("url") or item.get("apply_url") or "").strip()
            if not job_url:
                continue
            norm = _normalize(
                "remoteok",
                item.get("id", ""),
                item.get("company", ""),
                item.get("position", ""),
                job_url,
            )
            if norm and _matches({**item, "title": item.get("position"), "tags": item.get("tags") or []}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("RemoteOK fetch failed: %s", e)
        return []


def fetch_remotive() -> list[dict]:
    """Remotive API. Rate: max 2 req/min."""
    time.sleep(35)  # stay under 2/min
    try:
        r = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "search": "spring boot", "limit": 100},
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        jobs_list = data.get("jobs") if isinstance(data, dict) else []
        jobs = []
        for item in jobs_list or []:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            if not url:
                continue
            norm = _normalize(
                "remotive",
                item.get("id", ""),
                item.get("company_name", ""),
                item.get("title", ""),
                url,
            )
            if norm and _matches({**item, "position": item.get("title"), "company": item.get("company_name")}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("Remotive fetch failed: %s", e)
        return []


def fetch_jobicy() -> list[dict]:
    """Jobicy API."""
    time.sleep(35)
    try:
        r = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"tag": "spring boot", "count": 100},
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        jobs_list = data.get("jobs") if isinstance(data, dict) else []
        jobs = []
        for item in jobs_list or []:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            if not url:
                continue
            norm = _normalize(
                "jobicy",
                item.get("id", ""),
                item.get("companyName", ""),
                item.get("jobTitle", ""),
                url,
            )
            if norm and _matches({**item, "position": item.get("jobTitle"), "company": item.get("companyName")}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("Jobicy fetch failed: %s", e)
        return []


def fetch_working_nomads() -> list[dict]:
    """Working Nomads API. Full list, filter in code."""
    try:
        r = requests.get(
            "https://www.workingnomads.com/api/exposed_jobs/",
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        jobs = []
        for item in data:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            if not url:
                continue
            norm = _normalize(
                "workingnomads",
                url,
                item.get("company_name", ""),
                item.get("title", ""),
                url,
            )
            desc = (item.get("description") or "").lower()
            if norm and _matches({**item, "position": item.get("title"), "description": desc}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("Working Nomads fetch failed: %s", e)
        return []


def fetch_jobscollider() -> list[dict]:
    """JobsCollider API."""
    time.sleep(5)
    try:
        r = requests.get(
            "https://jobscollider.com/api/search-jobs",
            params={"query": "spring boot", "category": "software_development"},
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        jobs_list = data.get("jobs") if isinstance(data, dict) else []
        jobs = []
        for item in jobs_list or []:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            if not url:
                continue
            norm = _normalize(
                "jobscollider",
                item.get("id", ""),
                item.get("company_name", ""),
                item.get("title", ""),
                url,
            )
            if norm and _matches({**item, "position": item.get("title"), "company": item.get("company_name")}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("JobsCollider fetch failed: %s", e)
        return []


def _parse_wwr_entry(entry, source: str) -> dict | None:
    """Parse one We Work Remotely RSS entry."""
    link = (entry.get("link") or "").strip()
    title = (entry.get("title") or "").strip()
    if not link:
        return None
    # Title often like "Company Name: Job Title" or just "Job Title"
    company = ""
    if ":" in title:
        company, _, position = title.partition(":")
        position = position.strip()
    else:
        position = title
    norm = _normalize(source, link, company, position, link)
    if norm and _matches({"position": position, "title": position, "company": company}):
        return norm
    return None


def fetch_wwr() -> list[dict]:
    """We Work Remotely RSS feeds."""
    base = "https://weworkremotely.com/categories/"
    urls = [
        base + "remote-programming-jobs.rss",
        base + "remote-back-end-programming-jobs.rss",
    ]
    jobs = []
    for url in urls:
        try:
            feed = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for entry in feed.get("entries") or []:
                norm = _parse_wwr_entry(entry, "wwr")
                if norm:
                    jobs.append(norm)
        except Exception as e:
            logger.warning("WWR RSS %s failed: %s", url, e)
    return jobs


def fetch_adzuna() -> list[dict]:
    """Adzuna API. Only if keys set."""
    if not (config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY):
        return []
    jobs = []
    for country in ("gb", "us"):
        try:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                params={
                    "app_id": config.ADZUNA_APP_ID,
                    "app_key": config.ADZUNA_APP_KEY,
                    "what": "spring boot java backend",
                },
                headers=REQUEST_HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") if isinstance(data, dict) else []
            for item in results or []:
                if not isinstance(item, dict):
                    continue
                url = (item.get("redirect_url") or item.get("url") or "").strip()
                if not url:
                    continue
                norm = _normalize(
                    "adzuna",
                    item.get("id", ""),
                    item.get("company", {}).get("display_name", "") if isinstance(item.get("company"), dict) else "",
                    item.get("title", ""),
                    url,
                )
                if norm and _matches({**item, "position": item.get("title")}):
                    jobs.append(norm)
            time.sleep(2)
        except Exception as e:
            logger.warning("Adzuna %s fetch failed: %s", country, e)
    return jobs


def fetch_themuse() -> list[dict]:
    """The Muse API. Only if key set."""
    if not config.THEMUSE_API_KEY:
        return []
    jobs = []
    try:
        for page in range(1, 4):
            r = requests.get(
                "https://www.themuse.com/api/public/jobs",
                params={"page": page, "api_key": config.THEMUSE_API_KEY},
                headers=REQUEST_HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") if isinstance(data, dict) else []
            for item in results or []:
                if not isinstance(item, dict):
                    continue
                url = (item.get("refs", {}).get("landing_page") or item.get("url") or "").strip()
                if not url:
                    continue
                norm = _normalize(
                    "themuse",
                    item.get("id", ""),
                    item.get("company", {}).get("name", "") if isinstance(item.get("company"), dict) else "",
                    item.get("name", ""),
                    url,
                )
                if norm and _matches({**item, "position": item.get("name"), "title": item.get("name")}):
                    jobs.append(norm)
            time.sleep(1)
    except Exception as e:
        logger.warning("The Muse fetch failed: %s", e)
    return jobs


def fetch_realworkfromanywhere() -> list[dict]:
    """Real Work From Anywhere RSS feeds."""
    base = "https://www.realworkfromanywhere.com"
    urls = [
        f"{base}/rss.xml",
        f"{base}/remote-developer-jobs/rss.xml",
        f"{base}/remote-backend-jobs/rss.xml",
    ]
    jobs = []
    for url in urls:
        try:
            feed = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for entry in feed.get("entries") or []:
                link = (entry.get("link") or "").strip()
                title = (entry.get("title") or "").strip()
                if not link:
                    continue
                summary = (entry.get("summary", "") or "").lower()
                norm = _normalize("realworkfromanywhere", link, "", title, link)
                if norm and _matches({"position": title, "title": title, "description": summary}):
                    jobs.append(norm)
        except Exception as e:
            logger.warning("Real Work From Anywhere %s failed: %s", url, e)
    return jobs


def fetch_authenticjobs() -> list[dict]:
    """Authentic Jobs API. Only if key set."""
    if not config.AUTHENTICJOBS_API_KEY:
        return []
    try:
        r = requests.get(
            "https://authenticjobs.com/api/posts/search/",
            params={"api_key": config.AUTHENTICJOBS_API_KEY, "keywords": "spring boot java"},
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        listings = data.get("listings") if isinstance(data, dict) else []
        jobs = []
        for item in listings or []:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or item.get("apply_url") or "").strip()
            if not url:
                continue
            company = item.get("company", {})
            company_name = company.get("name", "") if isinstance(company, dict) else ""
            norm = _normalize(
                "authenticjobs",
                item.get("id", ""),
                company_name,
                item.get("title", ""),
                url,
            )
            if norm and _matches({**item, "position": item.get("title"), "company": company_name}):
                jobs.append(norm)
        return jobs
    except Exception as e:
        logger.warning("Authentic Jobs fetch failed: %s", e)
        return []


def dedupe_by_url(jobs: list[dict]) -> list[dict]:
    """Keep first occurrence of each job_url."""
    seen = set()
    out = []
    for j in jobs:
        u = (j.get("url") or "").strip()
        if u and u not in seen:
            seen.add(u)
            out.append(j)
    return out


def fetch_all_jobs() -> list[dict]:
    """Fetch from all 10 sources, normalize, filter, dedupe."""
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_working_nomads())
    all_jobs.extend(fetch_jobscollider())
    all_jobs.extend(fetch_wwr())
    all_jobs.extend(fetch_adzuna())
    all_jobs.extend(fetch_themuse())
    all_jobs.extend(fetch_realworkfromanywhere())
    all_jobs.extend(fetch_authenticjobs())
    deduped = dedupe_by_url(all_jobs)
    logger.info("Fetched %d jobs after dedupe", len(deduped))
    return deduped
