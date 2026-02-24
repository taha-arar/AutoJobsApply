"""
Orchestrate the job application pipeline: fetch jobs, find emails, send applications, report on Telegram.
"""
import logging
import sys
from pathlib import Path

import config
from src import domain_resolver, email_finder, email_sender, email_verifier, job_discovery, state, telegram_notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

STATE_PATH = Path(__file__).resolve().parent / "data" / "applied.json"


def main() -> None:
    config.validate_config()
    applied = state.load_applied(STATE_PATH)
    jobs = job_discovery.fetch_all_jobs()
    sent = 0
    cap = config.MAX_APPLICATIONS_PER_RUN
    for job in jobs:
        if sent >= cap:
            logger.info("Reached cap of %d applications, stopping", cap)
            break
        job_url = (job.get("url") or "").strip()
        if not job_url:
            continue
        if state.is_applied(job_url, applied):
            logger.debug("Skipped (already applied): %s", job_url[:60])
            continue
        company = (job.get("company") or "").strip()
        if not company:
            continue
        domains = domain_resolver.candidate_domains(company)
        to_email = None
        for domain in domains:
            to_email = email_finder.find_email_for_domain(domain)
            if to_email:
                break
        if not to_email:
            logger.info("No email for domain (company: %s), skip", company[:40])
            continue
        if not email_verifier.is_deliverable(to_email):
            logger.info("Email not deliverable, skip %s (company: %s)", to_email, company[:40])
            continue
        ok = email_sender.send_application_email(
            to_email,
            company,
            job.get("position") or job.get("title") or "Spring Boot Developer",
        )
        if not ok:
            continue
        telegram_notifier.send_telegram_report(
            job.get("position") or job.get("title") or "Spring Boot Developer",
            company,
            job_url,
            to_email,
            job.get("source", ""),
        )
        state.append_applied(
            job.get("source", ""),
            job.get("id", ""),
            job_url,
            company,
            applied,
            STATE_PATH,
        )
        sent += 1
        logger.info("Applied to %s (%s)", company, job_url[:50])
    logger.info("Done. Applied to %d jobs (cap %d).", sent, cap)


if __name__ == "__main__":
    main()
