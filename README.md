# AutoApply – Job Application Agent

Automated agent that finds remote Spring Boot/Java developer jobs from 10 sources, finds company emails via Hunter.io, sends application emails via Gmail, and reports each application to you on Telegram.

## Features

- **10 job sources** (APIs and RSS only, no scraping): RemoteOK, Remotive, Jobicy, Working Nomads, JobsCollider, We Work Remotely, Adzuna, The Muse, Real Work From Anywhere, Authentic Jobs
- **Up to 10 applications per run** (configurable via `MAX_APPLICATIONS_PER_RUN`)
- **No duplicate applications**: state stored in `data/applied.json`
- **Telegram report** after each successful application (title + company + job URL)
- **Daily run** via GitHub Actions (8:00 AM UTC)

## Requirements

- Python 3.10+
- Gmail account (with App Password)
- [Hunter.io](https://hunter.io) API key (domain search)
- Telegram bot token and your chat ID (for reports)

## Local setup

1. **Clone and install**

   ```bash
   cd AutoApply
   pip install -r requirements.txt
   ```

2. **Configure**

   Copy `.env.example` to `.env` and set:

   - `GMAIL_USER` – your Gmail address
   - `GMAIL_APP_PASSWORD` – [Gmail App Password](https://support.google.com/accounts/answer/185833)
   - `HUNTER_API_KEY` – from [Hunter.io](https://hunter.io)
   - `TELEGRAM_BOT_TOKEN` – from [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID` – e.g. from [@userinfobot](https://t.me/userinfobot)

   Optional (more job sources):

   - `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` – [Adzuna API](https://developer.adzuna.com/)
   - `THEMUSE_API_KEY` – [The Muse API](https://www.themuse.com/developers)
   - `AUTHENTICJOBS_API_KEY` – [Authentic Jobs](https://authenticjobs.com/)

3. **Run**

   ```bash
   python run_agent.py
   ```

## Deployment (GitHub Actions)

1. Push this repo to GitHub.
2. In the repo: **Settings → Secrets and variables → Actions**, add:
   - `GMAIL_USER`
   - `GMAIL_APP_PASSWORD`
   - `HUNTER_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID` (or set in the workflow env, e.g. `2011164169`)
3. The workflow runs daily at 8:00 AM UTC. You can also trigger it manually (**Actions → Run Job Application Agent → Run workflow**).
4. After each run, `data/applied.json` is committed back so the next run does not re-apply to the same jobs.

## Project structure

- `run_agent.py` – entrypoint
- `config.py` – env and motivation letter
- `src/job_discovery.py` – fetch from all 10 sources, filter, dedupe
- `src/domain_resolver.py` – company name → domain candidates
- `src/email_finder.py` – Hunter.io domain search
- `src/email_sender.py` – Gmail SMTP
- `src/telegram_notifier.py` – Telegram report
- `src/state.py` – load/save `data/applied.json`
- `.github/workflows/run-agent.yml` – daily schedule

## Attribution

Job data is used only to send one application email per company. All sources require linking back; do not repost their listings to third-party job boards.
