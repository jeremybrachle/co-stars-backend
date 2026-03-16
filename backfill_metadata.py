import argparse

from db import ensure_schema
from db_helper import get_all_movie_ids
from ingest import ingest_movie_by_id


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill enriched TMDB metadata for movies already stored in the database."
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional number of existing movies to refresh for quick verification.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ensure_schema()
    movie_ids = get_all_movie_ids()
    if args.limit is not None:
        movie_ids = movie_ids[: args.limit]

    print(f"Refreshing metadata for {len(movie_ids)} existing movies")
    refreshed = 0
    for movie_id in movie_ids:
        result = ingest_movie_by_id(movie_id, refresh_existing=True)
        if result == "refreshed":
            refreshed += 1

    print(f"Metadata backfill complete. Refreshed: {refreshed}")


if __name__ == "__main__":
    main()