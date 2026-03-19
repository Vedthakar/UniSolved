from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_name: str = "UniSolved"
    default_campus: str = "U of T St. George"
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str = ""
    db_path: Path = PROJECT_ROOT / "data" / "unisolved_demo.sqlite3"

    @property
    def live_mode_enabled(self) -> bool:
        return bool(self.gemini_api_key)


def load_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")
    db_path = os.getenv("UNISOLVED_DB_PATH")
    return Settings(
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        db_path=Path(db_path) if db_path else PROJECT_ROOT / "data" / "unisolved_demo.sqlite3",
    )


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
