import argparse
import json
from pathlib import Path

from fastapi_app.main import LEVELS
from frontend_snapshot import build_frontend_snapshot


def main():
    parser = argparse.ArgumentParser(
        description="Export the full actor/movie graph as a frontend-friendly JSON snapshot."
    )
    parser.add_argument(
        "--output",
        default="frontend_snapshot.json",
        help="Output JSON path. Defaults to frontend_snapshot.json in the project root.",
    )
    args = parser.parse_args()

    snapshot = build_frontend_snapshot(LEVELS)
    output_path = Path(args.output)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Wrote frontend snapshot to {output_path}")


if __name__ == "__main__":
    main()