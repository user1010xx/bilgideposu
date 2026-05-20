import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


def _parse_usernames(raw: str) -> set[str]:
    names = set()
    for part in raw.split(","):
        name = part.strip().lstrip("@").lower()
        if name:
            names.add(name)
    return names


ADMIN_USERNAMES = _parse_usernames(os.getenv("ADMIN_USERNAMES", ""))

_allowed = os.getenv("ALLOWED_GROUP_IDS", "").strip()
ALLOWED_GROUP_IDS = (
    {int(x.strip()) for x in _allowed.split(",") if x.strip().lstrip("-").isdigit()}
    if _allowed
    else None
)

_raw_db = os.getenv("DATABASE_URL", "").strip()
if _raw_db.startswith("postgres://"):
    _raw_db = _raw_db.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_db.startswith("postgresql://") and "+psycopg2" not in _raw_db:
    _raw_db = _raw_db.replace("postgresql://", "postgresql+psycopg2://", 1)

DATABASE_URL = _raw_db or f"sqlite:///{DATA_DIR / 'bilgibotu.db'}"
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "82"))
MIN_QUERY_WORDS = int(os.getenv("MIN_QUERY_WORDS", "2"))
COOLDOWN_SECONDS = float(os.getenv("COOLDOWN_SECONDS", "2"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "30"))
QUESTIONS_PAGE_SIZE = int(os.getenv("QUESTIONS_PAGE_SIZE", "20"))
MAX_NORMALIZED_LENGTH = 2000

# Telegram metin sınırı (güvenli pay)
MAX_MESSAGE_LENGTH = 4000

if not ADMIN_IDS and not ADMIN_USERNAMES:
    logger.warning(
        "ADMIN_IDS ve ADMIN_USERNAMES boş — /ekle ve /sil kimseye açık değil."
    )
