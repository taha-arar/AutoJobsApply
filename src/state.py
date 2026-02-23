"""
Track which jobs we have already applied to. Uses applied.json (gitignored or committed in CI).
"""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "applied.json"


def load_applied(state_path: Path | None = None) -> list[dict]:
    """Load list of applied jobs. Returns [] if file missing or invalid."""
    path = state_path or DEFAULT_STATE_PATH
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load applied.json: %s", e)
        return []


def is_applied(job_url: str, applied_list: list[dict]) -> bool:
    """True if job_url is already in the applied list."""
    urls = {r.get("job_url") for r in applied_list if r.get("job_url")}
    return job_url in urls


def append_applied(
    source: str,
    job_id: str,
    job_url: str,
    company: str,
    applied_list: list[dict],
    state_path: Path | None = None,
) -> None:
    """Append one record and write back atomically."""
    path = state_path or DEFAULT_STATE_PATH
    record = {
        "source": source,
        "job_id": str(job_id),
        "job_url": job_url,
        "company": company,
        "applied_at": datetime.utcnow().isoformat() + "Z",
    }
    applied_list.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(applied_list, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
