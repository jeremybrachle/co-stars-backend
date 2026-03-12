import argparse
import json
from pathlib import Path

from fastapi_app.main import LEVELS
from frontend_snapshot import build_frontend_manifest, build_frontend_snapshot


def main():
    parser = argparse.ArgumentParser(
        description="Export the full actor/movie graph as a frontend-friendly JSON snapshot."
    )
    parser.add_argument(
        "--output",
        default="frontend_snapshot.json",
        help="Output JSON path. Defaults to frontend_snapshot.json in the project root.",
    )
    parser.add_argument(
        "--manifest-output",
        help="Optional manifest JSON path. When provided, exports frontend refresh metadata alongside the snapshot.",
    )
    parser.add_argument(
        "--snapshot-endpoint",
        help="Override the manifest snapshot endpoint. Defaults to the snapshot file name when --manifest-output is used.",
    )
    args = parser.parse_args()

    snapshot = build_frontend_snapshot(LEVELS)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Wrote frontend snapshot to {output_path}")

    if args.manifest_output:
        manifest_output_path = Path(args.manifest_output)
        manifest_output_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_endpoint = args.snapshot_endpoint or output_path.name
        manifest = build_frontend_manifest(LEVELS, snapshot_endpoint=snapshot_endpoint)
        manifest_output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote frontend manifest to {manifest_output_path}")


if __name__ == "__main__":
    main()