import os

from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} environment variable is required.")
    return value


def _parse_superadmin_ids(raw_value: str) -> list[int]:
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not values:
        raise RuntimeError("SUPERADMIN_IDS environment variable must contain at least one Telegram user ID.")
    return [int(item) for item in values]


BOT_TOKEN = _require_env("BOT_TOKEN")
DATABASE_URL = _require_env("DATABASE_URL")
SUPERADMIN_IDS = _parse_superadmin_ids(_require_env("SUPERADMIN_IDS"))
ADMIN_IDS = SUPERADMIN_IDS
