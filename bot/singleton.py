import atexit
import os
import sys

from bot.config import DATA_DIR

LOCK_PATH = DATA_DIR / "bot.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def ensure_single_instance() -> None:
    """Aynı token ile ikinci polling örneğini engeller (çift mesaj önlenir)."""
    if LOCK_PATH.exists():
        try:
            old_pid = int(LOCK_PATH.read_text(encoding="utf-8").strip())
        except ValueError:
            old_pid = 0
        if old_pid and old_pid != os.getpid() and _pid_alive(old_pid):
            print(
                f"HATA: Bot zaten çalışıyor (PID {old_pid}). "
                "Çift yanıt olmaması için ikinci örnek kapatılıyor.",
                file=sys.stderr,
            )
            sys.exit(1)

    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")

    def _cleanup():
        if LOCK_PATH.exists():
            try:
                if int(LOCK_PATH.read_text(encoding="utf-8").strip()) == os.getpid():
                    LOCK_PATH.unlink(missing_ok=True)
            except ValueError:
                LOCK_PATH.unlink(missing_ok=True)

    atexit.register(_cleanup)
