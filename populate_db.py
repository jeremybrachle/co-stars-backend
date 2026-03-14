import argparse
import csv
from pathlib import Path

from db import ensure_schema, init_db
from db_helper import movie_exists
from ingest import ingest_movie_by_id

DEFAULT_SEED_FILE = "movie_seed.csv"


def load_seed_movie_ids(seed_file):
    seed_path = Path(seed_file)
    with seed_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "tmdb_movie_id" not in (reader.fieldnames or []):
            raise ValueError("Seed file must include a 'tmdb_movie_id' column")

        movie_ids = []
        for line_number, row in enumerate(reader, start=2):
            raw_movie_id = (row.get("tmdb_movie_id") or "").strip()
            if not raw_movie_id:
                continue
            try:
                movie_ids.append(int(raw_movie_id))
            except ValueError as exc:
                raise ValueError(
                    f"Invalid tmdb_movie_id '{raw_movie_id}' on line {line_number}"
                ) from exc

    return movie_ids


def sync_movies(movie_ids, refresh_existing=False):
    summary = {"inserted": 0, "refreshed": 0, "skipped": 0}

    for movie_id in movie_ids:
        if movie_exists(movie_id) and not refresh_existing:
            print(f"Movie ID {movie_id} already exists. Skipping.")
            summary["skipped"] += 1
            continue

        result = ingest_movie_by_id(movie_id, refresh_existing=refresh_existing)
        if result == "refreshed":
            summary["refreshed"] += 1
        elif result == "inserted":
            summary["inserted"] += 1
        else:
            summary["skipped"] += 1

    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Populate the SQLite database from a TMDB seed CSV."
    )
    parser.add_argument(
        "--seed-file",
        default=DEFAULT_SEED_FILE,
        help=f"CSV file containing a tmdb_movie_id column. Default: {DEFAULT_SEED_FILE}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional number of seed rows to process for quick verification.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the database before ingesting seed rows.",
    )
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Refresh metadata for movies that already exist in the database.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.reset:
        init_db()
    else:
        ensure_schema()

    movie_ids = load_seed_movie_ids(args.seed_file)
    if args.limit is not None:
        movie_ids = movie_ids[: args.limit]

    print(f"Loaded {len(movie_ids)} movie IDs from {args.seed_file}")
    summary = sync_movies(movie_ids, refresh_existing=args.refresh_existing)

    print(
        "\nDatabase population complete! "
        f"Inserted: {summary['inserted']}, "
        f"Refreshed: {summary['refreshed']}, "
        f"Skipped: {summary['skipped']}"
    )

if __name__ == "__main__":
    main()
