"""
Load configuration from environment. Required: Gmail, Hunter.
Telegram optional (report skipped if token or chat_id missing).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Required for sending emails
GMAIL_USER = os.environ.get("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "").strip()

# Optional: Telegram report after each application
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Portfolio and motivation letter
PORTFOLIO_URL = os.environ.get(
    "PORTFOLIO_URL", "https://taha-arar-portfolio.vercel.app"
).strip()

# Cap applications per run (default 10)
_raw = (os.environ.get("MAX_APPLICATIONS_PER_RUN") or "10").strip()
MAX_APPLICATIONS_PER_RUN = int(_raw) if _raw.isdigit() else 10

# Optional: extra job sources (skip if not set)
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "").strip()
THEMUSE_API_KEY = os.environ.get("THEMUSE_API_KEY", "").strip()
AUTHENTICJOBS_API_KEY = os.environ.get("AUTHENTICJOBS_API_KEY", "").strip()

MOTIVATION_LETTER = """Dear Hiring Manager,

I hope this message finds you well.

I am writing to express my interest in the Spring Boot Developer position. With strong experience in Java and Spring Boot development, I have worked on building scalable backend systems, designing RESTful APIs, implementing security with Spring Security, and developing full-stack applications integrated with Thymeleaf and modern frontend frameworks.

In my professional journey, I focus on writing clean and maintainable code, optimizing performance, and applying software architecture best practices. I am currently strengthening my knowledge in microservices concepts and system integration, where I actively practice service communication, event-driven design, and distributed system patterns to build more scalable and resilient applications. I also have experience working with databases and backend optimizations for enterprise-level systems.

I am highly motivated to contribute to challenging projects where I can improve backend architecture, enhance system performance, and collaborate effectively with development teams to deliver reliable solutions.

I would welcome the opportunity to further discuss how my skills and continuous learning mindset can add value to your team.

Thank you for your time and consideration.

Best regards,
Taha Arar"""


def validate_config() -> None:
    """Raise with clear message if required env is missing."""
    missing = []
    if not GMAIL_USER:
        missing.append("GMAIL_USER")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")
    if not HUNTER_API_KEY:
        missing.append("HUNTER_API_KEY")
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and set them."
        )


def telegram_configured() -> bool:
    """True if we can send Telegram reports."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
