import argparse
import json
from pathlib import Path

from frontend_snapshot import (
    build_frontend_manifest,
    build_frontend_manifest_v2,
    build_frontend_snapshot,
    build_frontend_snapshot_v2,
)
from levels_contracts import build_v2_levels_export, load_v1_levels, load_v2_levels_document


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
    parser.add_argument(
        "--api-version",
        choices=["v1", "v2"],
        default="v1",
        help="Choose whether to export the legacy flat v1 contract or the grouped v2 contract. Defaults to v1 for compatibility.",
    )
    args = parser.parse_args()

    if args.api_version == "v2":
        levels = build_v2_levels_export(load_v2_levels_document())
        snapshot = build_frontend_snapshot_v2(levels)
        default_snapshot_endpoint = "/api/v2/export/frontend-snapshot"
        manifest_builder = build_frontend_manifest_v2
    else:
        levels = load_v1_levels()
        snapshot = build_frontend_snapshot(levels)
        default_snapshot_endpoint = "/api/v1/export/frontend-snapshot"
        manifest_builder = build_frontend_manifest

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Wrote frontend snapshot to {output_path}")

    if args.manifest_output:
        manifest_output_path = Path(args.manifest_output)
        manifest_output_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_endpoint = args.snapshot_endpoint or output_path.name or default_snapshot_endpoint
        manifest = manifest_builder(levels, snapshot_endpoint=snapshot_endpoint)
        manifest_output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote frontend manifest to {manifest_output_path}")


if __name__ == "__main__":
    main()