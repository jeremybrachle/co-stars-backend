from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parent / "VERSION"


def get_project_version(default="0.0.0"):
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or default
    except FileNotFoundError:
        return default