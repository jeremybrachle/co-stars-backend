from datetime import datetime, timezone
import json
from pathlib import Path

from db_helper import (
    get_all_actors_with_metadata,
    get_all_movie_actor_links,
    get_all_movies_with_metadata,
)
from db import DB_FILE
from project_version import get_project_version
from tmdb_api import build_poster_url, build_profile_url


ROOT = Path(__file__).resolve().parent
LEVELS_FILE = ROOT / "levels.json"


def _isoformat_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _get_source_updated_at():
    timestamps = []

    db_path = ROOT / DB_FILE
    if db_path.exists():
        timestamps.append(db_path.stat().st_mtime)

    if LEVELS_FILE.exists():
        timestamps.append(LEVELS_FILE.stat().st_mtime)

    if not timestamps:
        return datetime.now(timezone.utc).isoformat()

    return _isoformat_from_timestamp(max(timestamps))


def _serialize_actors(actor_rows):
    return [
        {
            "id": row[0],
            "name": row[1],
            "popularity": row[2],
            "birthday": row[3],
            "deathday": row[4],
            "place_of_birth": row[5],
            "biography": row[6],
            "profile_path": row[7],
            "profile_url": build_profile_url(row[7]),
            "known_for_department": row[8],
        }
        for row in actor_rows
    ]


def _serialize_movies(movie_rows):
    serialized = []
    for row in movie_rows:
        genres_json = row[3]
        try:
            genres = json.loads(genres_json) if genres_json else []
        except json.JSONDecodeError:
            genres = []

        serialized.append(
            {
                "id": row[0],
                "title": row[1],
                "release_date": row[2],
                "genres": genres,
                "overview": row[4],
                "poster_path": row[5],
                "poster_url": build_poster_url(row[5]),
                "original_language": row[6],
                "content_rating": row[7],
            }
        )
    return serialized


def _serialize_links(link_rows):
    return [
        {
            "movie_id": movie_id,
            "actor_id": actor_id,
        }
        for movie_id, actor_id in link_rows
    ]


def _build_adjacency(link_rows):
    actor_to_movies = {}
    movie_to_actors = {}

    for movie_id, actor_id in link_rows:
        actor_key = str(actor_id)
        movie_key = str(movie_id)
        actor_to_movies.setdefault(actor_key, []).append(movie_id)
        movie_to_actors.setdefault(movie_key, []).append(actor_id)

    return actor_to_movies, movie_to_actors


def _normalize_actor_name(name):
    return name.strip().casefold()


def _validate_levels_against_actor_rows(levels, actor_rows):
    actor_names = {
        _normalize_actor_name(row[1])
        for row in actor_rows
        if isinstance(row[1], str) and row[1].strip()
    }
    missing_names = set()

    for level in levels:
        for field_name in ("actor_a", "actor_b"):
            actor_name = level.get(field_name)
            if not isinstance(actor_name, str) or not actor_name.strip():
                continue
            if _normalize_actor_name(actor_name) not in actor_names:
                missing_names.add(actor_name)

    if missing_names:
        missing_list = ", ".join(sorted(missing_names, key=str.casefold))
        raise ValueError(
            "Levels reference actors missing from the exported graph: "
            f"{missing_list}. This usually means the snapshot export is using the wrong database."
        )


def build_frontend_snapshot(levels):
    actor_rows = get_all_actors_with_metadata()
    movie_rows = get_all_movies_with_metadata()
    link_rows = get_all_movie_actor_links()
    _validate_levels_against_actor_rows(levels, actor_rows)
    actor_to_movies, movie_to_actors = _build_adjacency(link_rows)

    return {
        "meta": {
            "version": get_project_version(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "actor_count": len(actor_rows),
            "movie_count": len(movie_rows),
            "relationship_count": len(link_rows),
            "level_count": len(levels),
        },
        "actors": _serialize_actors(actor_rows),
        "movies": _serialize_movies(movie_rows),
        "movie_actors": _serialize_links(link_rows),
        "adjacency": {
            "actor_to_movies": actor_to_movies,
            "movie_to_actors": movie_to_actors,
        },
        "levels": list(levels),
    }


def build_frontend_manifest(levels, snapshot_endpoint="/api/export/frontend-snapshot"):
    actor_rows = get_all_actors_with_metadata()
    movie_rows = get_all_movies_with_metadata()
    link_rows = get_all_movie_actor_links()
    _validate_levels_against_actor_rows(levels, actor_rows)

    return {
        "version": get_project_version(),
        "source_updated_at": _get_source_updated_at(),
        "actor_count": len(actor_rows),
        "movie_count": len(movie_rows),
        "relationship_count": len(link_rows),
        "level_count": len(levels),
        "recommended_refresh_interval_hours": 168,
        "snapshot_endpoint": snapshot_endpoint,
    }