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

def _parse_group_names(raw: str) -> set[str]:
    import re
    import unicodedata

    names = set()
    for part in raw.split(","):
        label = part.strip()
        if not label:
            continue
        label = label.lower()
        label = unicodedata.normalize("NFKD", label)
        label = "".join(c for c in label if not unicodedata.combining(c))
        label = re.sub(r"[^\w\s]", " ", label, flags=re.UNICODE)
        label = re.sub(r"\s+", " ", label).strip()
        if label:
            names.add(label)
    return names


_allowed_ids = os.getenv("ALLOWED_GROUP_IDS", "").strip()
ALLOWED_GROUP_IDS = (
    {int(x.strip()) for x in _allowed_ids.split(",") if x.strip().lstrip("-").isdigit()}
    if _allowed_ids
    else None
)

_allowed_names = os.getenv("ALLOWED_GROUP_NAMES", "").strip()
ALLOWED_GROUP_NAMES = _parse_group_names(_allowed_names) if _allowed_names else None

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

if ALLOWED_GROUP_IDS is None and ALLOWED_GROUP_NAMES is None:
    logger.warning(
        "ALLOWED_GROUP_IDS / ALLOWED_GROUP_NAMES boş — bot eklendiği TÜM gruplarda çalışır."
    )
elif ALLOWED_GROUP_NAMES:
    logger.info("İzinli grup adları: %s", ", ".join(sorted(ALLOWED_GROUP_NAMES)))
